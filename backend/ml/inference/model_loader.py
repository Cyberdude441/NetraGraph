"""Strict loader: a model is never usable without its bundle companions."""
from __future__ import annotations

import json
from pathlib import Path

from ml.config.version import ensure_supported_ml_runtime

REQUIRED_FILES = ("model.joblib", "preprocessor.joblib", "feature_schema.json", "label_mapping.json", "metrics.json", "metadata.json", "requirements_model.txt")


def validate_bundle(path: str | Path) -> dict:
    path = Path(path)
    missing = [name for name in REQUIRED_FILES if not (path / name).is_file()]
    if missing:
        raise ValueError("Model bundle is missing: " + ", ".join(missing))
    metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    schema = json.loads((path / "feature_schema.json").read_text(encoding="utf-8"))
    if not metadata.get("model_name") or not metadata.get("model_version") or not schema.get("feature_names"):
        raise ValueError("metadata.json and feature_schema.json must declare model identity and features")
    return {"metadata": metadata, "schema": schema}


class LoadedModel:
    def __init__(self, path: str | Path):
        ensure_supported_ml_runtime()
        import joblib
        self.path = Path(path)
        details = validate_bundle(self.path)
        self.metadata = details["metadata"]
        self.schema = details["schema"]
        self.model = joblib.load(self.path / "model.joblib")
        self.preprocessor = joblib.load(self.path / "preprocessor.joblib")
        self.labels = json.loads((self.path / "label_mapping.json").read_text(encoding="utf-8"))

    def predict(self, payload: dict):
        import pandas as pd
        features = self.schema["feature_names"]
        missing = [feature for feature in features if feature not in payload]
        if missing:
            raise ValueError("Missing required features: " + ", ".join(missing))
        frame = pd.DataFrame([{feature: payload[feature] for feature in features}])
        transformed = self.preprocessor.transform(frame)
        prediction = self.model.predict(transformed)[0]
        probability = max(self.model.predict_proba(transformed)[0]) if hasattr(self.model, "predict_proba") else None
        return {"prediction": self.labels.get(str(int(prediction)), str(prediction)), "probability": probability, "features_validated": True}
