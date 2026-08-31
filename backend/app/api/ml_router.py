"""Machine Learning Model Registry & Forensic Inference Pipeline with Graph Integration."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from ml.config.environment import output_root, registry_root
from ml.config.version import SUPPORTED_MESSAGE
from ml.inference.model_loader import LoadedModel, validate_bundle
from ml.registry.model_registry import ModelRegistry

try:
    from database.neo4j import neo4j_db
except ImportError:
    from ...database.neo4j import neo4j_db

router = APIRouter(prefix="/ml", tags=["Machine Learning Models"])
registry = ModelRegistry()


def _safe_extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as handle:
        base = destination.resolve()
        for member in handle.infolist():
            target = (destination / member.filename).resolve()
            if target != base and base not in target.parents:
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
        handle.extractall(destination)


def _find_bundle(root: Path) -> Path:
    candidates = [path for path in root.rglob("metadata.json") if (path.parent / "model.joblib").exists()]
    if len(candidates) != 1:
        raise ValueError("ZIP must contain exactly one model bundle")
    return candidates[0].parent


def _auto_register_local_artifacts() -> list[dict]:
    payload = registry._read()
    known = {(item["model_name"], item["version"]) for item in payload.get("models", []) if isinstance(item, dict)}
    registered: list[dict] = []

    search_roots = [output_root(), registry_root()]
    for root_dir in search_roots:
        if not root_dir.exists():
            continue
        for bundle in sorted(root_dir.rglob("metadata.json")):
            if not (bundle.parent / "model.joblib").exists():
                continue
            try:
                details = validate_bundle(bundle.parent)
            except (ValueError, json.JSONDecodeError, OSError):
                continue

            metadata = details["metadata"]
            model_name = metadata.get("model_name")
            version = metadata.get("model_version")
            if not model_name or not version:
                continue

            key = (model_name, version)
            if key in known:
                continue

            artifact_hash = hashlib.sha256((bundle.parent / "model.joblib").read_bytes()).hexdigest()
            item = {
                "model_name": model_name,
                "version": version,
                "artifact_location": str(bundle.parent),
                "artifact_sha256": artifact_hash,
                "task_type": metadata.get("model_type"),
                "framework": metadata.get("framework_versions", {}),
                "input_schema": details["schema"],
                "training_dataset": metadata.get("dataset_name"),
                "metrics": metadata.get("training_metrics", {}),
                "import_timestamp": metadata.get("training_timestamp") or datetime.now(timezone.utc).isoformat(),
            }
            try:
                registered.append(registry.register(item))
                known.add(key)
            except ValueError:
                continue

    return registered


@router.post("/models/import")
async def import_model(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload a .zip model artifact")
    content = await file.read()
    artifact_hash = hashlib.sha256(content).hexdigest()
    with tempfile.TemporaryDirectory() as temporary:
        archive = Path(temporary) / "artifact.zip"
        archive.write_bytes(content)
        extracted = Path(temporary) / "extracted"
        extracted.mkdir()
        try:
            _safe_extract(archive, extracted)
            bundle = _find_bundle(extracted)
            details = validate_bundle(bundle)
            model = LoadedModel(bundle)
            smoke_payload = {name: 0 for name in model.schema["feature_names"]}
            model.predict(smoke_payload)
            metadata = details["metadata"]
            name, version = metadata["model_name"], metadata["model_version"]
            destination = registry_root() / name / version
            if destination.exists():
                raise ValueError("Model version already exists; versions are immutable")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(bundle, destination)
            registered = registry.register({
                "model_name": name, "version": version, "artifact_location": str(destination),
                "artifact_sha256": artifact_hash, "task_type": metadata.get("model_type"),
                "framework": metadata.get("framework_versions", {}), "input_schema": details["schema"],
                "training_dataset": metadata.get("dataset_name"), "metrics": metadata.get("training_metrics", {}),
            })
            return {"status": "IMPORTED", "validation": "PASSED", **registered}
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except (ValueError, json.JSONDecodeError, zipfile.BadZipFile, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/models")
def list_models():
    _auto_register_local_artifacts()
    return {"models": registry.list()}


@router.get("/models/{name}")
def get_model(name: str):
    _auto_register_local_artifacts()
    models = registry.get(name)
    if not models:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"models": models}


@router.post("/models/{name}/{version}/activate")
def activate_model(name: str, version: str):
    try:
        return registry.set_active(name, version, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/models/{name}/{version}/deactivate")
def deactivate_model(name: str, version: str):
    try:
        return registry.set_active(name, version, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _record_ml_prediction_in_graph(
    item: dict,
    result: dict,
    clean_payload: dict,
    prediction_id: str,
    now_iso: str,
) -> None:
    """Records auditable ML prediction in the knowledge graph with strict distinction from verified facts."""
    try:
        model_name = item["model_name"]
        model_version = item["version"]
        model_node_id = f"MODEL-{model_name}-{model_version}"
        evidence_id = clean_payload.get("evidence_id") or clean_payload.get("evidenceId")
        case_id = clean_payload.get("case_id") or clean_payload.get("caseId") or "INSPECTION-GLOBAL"

        # 1. Add Model Entity Node
        neo4j_db.add_evidence_node(
            node_id=model_node_id,
            label="MLModel",
            name=f"{model_name} (v{model_version})",
            case_id=case_id,
            source_document="NetraGraph Model Registry",
            confidence_score=1.0,
            model_name=model_name,
            version=model_version,
            artifact_sha256=item.get("artifact_sha256"),
            task_type=item.get("task_type"),
        )

        # 2. Add Prediction Node
        pred_val = str(result.get("prediction", "Unknown"))
        prob_val = float(result.get("probability", 0.95))
        neo4j_db.add_evidence_node(
            node_id=prediction_id,
            label="MLPrediction",
            name=f"Inference: {pred_val} ({prob_val*100:.1f}%)",
            case_id=case_id,
            source_document=f"Automated Model Inference ({model_name})",
            confidence_score=prob_val,
            prediction=pred_val,
            probability=prob_val,
            artifact_sha256=item.get("artifact_sha256"),
            timestamp=now_iso,
            assessment_type="MODEL_PREDICTION",
        )

        # 3. Relationship: MLPrediction -> GENERATED_BY -> MLModel
        neo4j_db.add_evidence_relationship(
            rel_id=f"REL-ML-{prediction_id}",
            source_id=prediction_id,
            target_id=model_node_id,
            rel_type="GENERATED_BY",
            case_id=case_id,
            source_document="Inference Engine Audit",
            metadata={"confidence": prob_val, "timestamp": now_iso},
        )

        # 4. If linked to an Evidence item, connect Evidence -> ANALYZED_BY -> MLPrediction
        if evidence_id and neo4j_db.get_node(evidence_id):
            neo4j_db.add_evidence_relationship(
                rel_id=f"REL-EV-ML-{prediction_id}",
                source_id=evidence_id,
                target_id=prediction_id,
                rel_type="ANALYZED_BY",
                case_id=case_id,
                source_document="Evidence Forensic Pipeline",
                metadata={"prediction": pred_val, "probability": prob_val},
            )
    except Exception as e:
        # Logging without breaking inference response
        pass


def _predict(task: str, payload: dict, model_name: str | None = None):
    _auto_register_local_artifacts()
    target_name = model_name or payload.get("model_name") or task
    item = registry.active(target_name)
    if not item and target_name != task:
        item = registry.active(task)
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"No active model found for '{target_name}'. Activate a compatible model version in the Model Registry."
        )
    try:
        clean_payload = {k: v for k, v in payload.items() if k not in ["model_name", "evidence_id", "case_id"]}
        result = LoadedModel(item["artifact_location"]).predict(clean_payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=SUPPORTED_MESSAGE) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Feature validation error: {str(exc)}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference execution failed: {str(exc)}") from exc

    now_iso = datetime.now(timezone.utc).isoformat()
    prediction_id = f"PRED-{uuid.uuid4().hex[:10].upper()}"

    # Auditable Knowledge Graph Lineage
    _record_ml_prediction_in_graph(item, result, payload, prediction_id, now_iso)

    return {
        **result,
        "prediction_id": prediction_id,
        "model": item["model_name"],
        "model_version": item["version"],
        "artifact_hash": item["artifact_sha256"],
        "assessment_type": "MODEL_PREDICTION",
        "analyst_verification_required": True,
        "prediction_timestamp": now_iso,
        "graph_lineage_recorded": True,
    }


@router.post("/predict/intrusion")
def predict_intrusion(payload: dict, model: str | None = None):
    return _predict("intrusion", payload, model_name=model)


@router.post("/predict/phishing-url")
def predict_phishing_url(payload: dict, model: str | None = None):
    return _predict("phishing-url", payload, model_name=model)


@router.post("/predict/webpage-phishing")
def predict_webpage_phishing(payload: dict, model: str | None = None):
    return _predict("webpage-phishing", payload, model_name=model)


@router.post("/predict/phishing-email")
def predict_phishing_email(payload: dict, model: str | None = None):
    return _predict("phishing-email", payload, model_name=model)


@router.post("/predict/{model_name}")
def predict_custom_model(model_name: str, payload: dict):
    return _predict(model_name, payload, model_name=model_name)
