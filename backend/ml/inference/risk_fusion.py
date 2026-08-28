from __future__ import annotations


def fuse_prediction(prediction: dict, model: dict) -> dict:
    return {"source_model": model.get("model_name"), "model_version": model.get("version"), "confidence": prediction.get("probability"), "prediction": prediction.get("prediction"), "prediction_timestamp": model.get("import_timestamp"), "artifact_hash": model.get("artifact_sha256"), "analyst_verification_required": True}
