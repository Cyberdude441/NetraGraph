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
        return json.loads(self.file.read_text(encoding="utf-8"))

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
        return next((item for item in self.list() if item["model_name"] == name and item["active"]), None)
