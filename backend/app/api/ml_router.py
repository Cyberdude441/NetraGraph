from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ml.config.environment import registry_root
from ml.config.version import SUPPORTED_MESSAGE
from ml.inference.model_loader import LoadedModel, validate_bundle
from ml.registry.model_registry import ModelRegistry

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
    return {"models": registry.list()}


@router.get("/models/{name}")
def get_model(name: str):
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


def _predict(task: str, payload: dict):
    item = registry.active(task)
    if not item:
        raise HTTPException(status_code=404, detail=f"No active model for task: {task}")
    try:
        result = LoadedModel(item["artifact_location"]).predict(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=SUPPORTED_MESSAGE) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {**result, "model": item["model_name"], "model_version": item["version"], "artifact_hash": item["artifact_sha256"], "analyst_verification_required": True, "prediction_timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/predict/intrusion")
def predict_intrusion(payload: dict):
    return _predict("intrusion", payload)


@router.post("/predict/phishing-url")
def predict_phishing_url(payload: dict):
    return _predict("phishing-url", payload)


@router.post("/predict/phishing-email")
def predict_phishing_email(payload: dict):
    return _predict("phishing-email", payload)
