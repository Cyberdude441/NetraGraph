"""
Production Adapter for NetraGraph Shadow Inference.

Provides a read-only wrapper around production Models A–E.
Preserves existing behavior, measures high-resolution inference latency,
and guarantees that no production model state or files are modified.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure backend root is on sys.path for LoadedModel import
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    from training.shadow_inference.config import PRODUCTION_MODELS
    from training.shadow_inference.schemas import ProductionResult
except ImportError:
    from config import PRODUCTION_MODELS
    from schemas import ProductionResult


class ProductionAdapter:
    """
    Read-only adapter for production Models A–E.
    
    Loads models on-demand, executes predictions with microsecond precision,
    and returns standardized ProductionResult objects without modifying production state.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or (BACKEND_ROOT / "models" / "registry")
        self._loaded_models: Dict[str, Any] = {}

    def _get_model(self, model_name: str, version: str = "v1") -> Any:
        key = f"{model_name}:{version}"
        if key not in self._loaded_models:
            bundle_dir = self.registry_path / model_name / version
            if not bundle_dir.exists():
                raise FileNotFoundError(
                    f"Production model bundle not found at {bundle_dir}. "
                    f"Ensure {model_name}/{version} exists in the production registry."
                )
            
            from ml.inference.model_loader import LoadedModel
            self._loaded_models[key] = LoadedModel(bundle_dir)
        return self._loaded_models[key]

    def predict(
        self,
        model_name: str,
        payload: Dict[str, Any],
        version: str = "v1",
    ) -> ProductionResult:
        """
        Execute prediction on a production model in a completely read-only manner.
        """
        if model_name not in PRODUCTION_MODELS:
            for k, meta in PRODUCTION_MODELS.items():
                if meta["model_id"] == model_name or meta["category"] == model_name:
                    model_name = k
                    break

        t_start = time.perf_counter()
        try:
            model = self._get_model(model_name, version)
            clean_payload = {
                k: v for k, v in payload.items()
                if k not in ["model_name", "evidence_id", "case_id", "dataset_name", "request_id", "timestamp"]
            }
            output = model.predict(clean_payload)
            t_end = time.perf_counter()
            latency_ms = (t_end - t_start) * 1000.0

            raw_pred = output.get("prediction")
            prob = output.get("probability")
            
            if prob is not None:
                risk_score = float(prob)
            else:
                risk_score = 1.0 if str(raw_pred).lower() in ["1", "attack", "phishing", "anomaly", "malicious"] else 0.0

            return ProductionResult(
                model=model_name,
                model_version=version,
                prediction=raw_pred,
                risk_score=risk_score,
                latency_ms=latency_ms,
                raw_output=output,
                status="SUCCESS",
            )
        except Exception as exc:
            t_end = time.perf_counter()
            latency_ms = (t_end - t_start) * 1000.0
            return ProductionResult(
                model=model_name,
                model_version=version,
                prediction="ERROR",
                risk_score=0.0,
                latency_ms=latency_ms,
                status="ERROR",
                error=str(exc),
            )

    def get_model_info(self, model_name: str, version: str = "v1") -> Dict[str, Any]:
        """Return structural metadata and schema for a production model."""
        model = self._get_model(model_name, version)
        return {
            "model_name": model.metadata.get("model_name"),
            "model_version": model.metadata.get("model_version"),
            "model_type": model.metadata.get("model_type"),
            "feature_names": model.schema.get("feature_names", []),
            "labels": model.labels,
        }
