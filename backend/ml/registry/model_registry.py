"""Atomic JSON registry for imported model versions."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ml.config.environment import registry_root


class ModelRegistry:
    def __init__(self, path: str | Path | None = None):
        self.root = Path(path or registry_root())
        self.root.mkdir(parents=True, exist_ok=True)
        self.file = self.root.parent / "model_registry.json"

    def _read(self):
        if not self.file.exists():
            return {"models": []}
        try:
            payload = json.loads(self.file.read_text(encoding="utf-8"))
        except (TypeError, ValueError, json.JSONDecodeError):
            return {"models": []}

        if not isinstance(payload, dict):
            return {"models": []}

        models = payload.get("models", [])
        if not isinstance(models, list):
            return {"models": []}
        return {"models": models}

    def _write(self, payload):
        self.file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list(self):
        return self._read()["models"]

    def get(self, name: str):
        return [item for item in self.list() if item["model_name"] == name]

    def register(self, details: dict):
        payload = self._read()
        if any(item["model_name"] == details["model_name"] and item["version"] == details["version"] for item in payload["models"]):
            raise ValueError("Model version already exists")
        details["import_timestamp"] = datetime.now(timezone.utc).isoformat()
        details["active"] = not any(item["model_name"] == details["model_name"] and item["active"] for item in payload["models"])
        payload["models"].append(details)
        self._write(payload)
        return details

    def set_active(self, name: str, version: str, active: bool):
        payload = self._read()
        matches = [item for item in payload["models"] if item["model_name"] == name and item["version"] == version]
        if not matches:
            raise KeyError(f"Unknown model version: {name}/{version}")
        for item in payload["models"]:
            if item["model_name"] == name:
                item["active"] = active and item["version"] == version
        self._write(payload)
        return matches[0]

    def active(self, name: str):
        models = self.list()
        # 1. Exact active model name match
        exact = next((item for item in models if item["model_name"] == name and item.get("active")), None)
        if exact:
            return exact
        # 2. Match by task_type (case-insensitive)
        task_match = next((item for item in models if (item.get("task_type") or "").lower() == name.lower() and item.get("active")), None)
        if task_match:
            return task_match
        # 3. Match by domain substring (e.g. "intrusion" matches "session-intrusion")
        domain_match = next((item for item in models if name.lower() in item["model_name"].lower() and item.get("active")), None)
        if domain_match:
            return domain_match
        # 4. Fallback to any model with matching name
        return next((item for item in models if item["model_name"] == name), None)
