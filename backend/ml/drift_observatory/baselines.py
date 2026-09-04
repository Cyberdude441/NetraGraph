"""Baseline registry, validation, compatibility enforcement, and atomic JSON persistence.

PERSISTENCE INVARIANT:
Persistence uses bounded thread-safe in-memory state with atomic JSON serialization
and has no PostgreSQL schema or migration impact.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional

from .config import BaselineType, DriftDomain
from .models import BaselineWindow, ReferenceBaseline
from .provenance import compute_data_digest

logger = logging.getLogger("DriftBaselinesRegistry")


class IncompatibleBaselineError(ValueError):
    """Raised when an attempted baseline comparison violates compatibility constraints."""
    pass


class BaselineRegistry:
    """Thread-safe registry for frozen reference baselines."""

    def __init__(self, storage_path: Optional[Path] = None):
        self._lock = threading.RLock()
        self.storage_path = storage_path
        self._baselines: Dict[str, ReferenceBaseline] = {}
        if self.storage_path:
            self._load()

    def _load(self) -> None:
        with self._lock:
            if not self.storage_path or not self.storage_path.exists():
                return
            try:
                raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for b_dict in raw.get("baselines", []):
                    b = ReferenceBaseline.model_validate(b_dict)
                    self._baselines[b.baseline_id] = b
            except Exception as e:
                logger.warning(f"Failed to load drift baselines from {self.storage_path}: {e}")

    def _save(self) -> None:
        with self._lock:
            if not self.storage_path:
                return
            try:
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "version": "1.0.0",
                    "baselines": [b.model_dump() for b in self._baselines.values()]
                }
                temp_file = self.storage_path.with_suffix(".tmp")
                temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                temp_file.replace(self.storage_path)
            except Exception as e:
                logger.error(f"Failed to atomically persist drift baselines: {e}")

    def save_to_file(self, target_path: Path) -> None:
        """Explicit atomic JSON serialization to a specified file path."""
        with self._lock:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": "1.0.0",
                "baselines": [b.model_dump() for b in self._baselines.values()]
            }
            temp_file = target_path.with_suffix(".tmp")
            temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temp_file.replace(target_path)

    def load_from_file(self, source_path: Path) -> None:
        """Load baselines from an explicit JSON file."""
        with self._lock:
            if not source_path.exists():
                return
            raw = json.loads(source_path.read_text(encoding="utf-8"))
            for b_dict in raw.get("baselines", []):
                b = ReferenceBaseline.model_validate(b_dict)
                self._baselines[b.baseline_id] = b

    def register_baseline(self, baseline: ReferenceBaseline) -> ReferenceBaseline:
        with self._lock:
            self._baselines[baseline.baseline_id] = baseline
            self._save()
            return baseline

    def get_baseline(self, baseline_id: str) -> Optional[ReferenceBaseline]:
        with self._lock:
            return self._baselines.get(baseline_id)

    def list_baselines(self, domain: Optional[DriftDomain] = None) -> List[ReferenceBaseline]:
        with self._lock:
            if domain is None:
                return list(self._baselines.values())
            return [b for b in self._baselines.values() if b.domain == domain]

    def delete_baseline(self, baseline_id: str) -> bool:
        with self._lock:
            if baseline_id in self._baselines:
                del self._baselines[baseline_id]
                self._save()
                return True
            return False

    def validate_compatibility(
        self,
        baseline: ReferenceBaseline,
        domain: DriftDomain,
        target: str,
        model_version: Optional[str] = None,
        feature_schema_version: Optional[str] = None,
        graph_layer: Optional[str] = None,
    ) -> None:
        """
        Enforces strict baseline compatibility.
        Rejects mismatched domain, target, model version, feature schema, or graph layer.
        """
        if baseline.domain != domain:
            raise IncompatibleBaselineError(
                f"Domain mismatch: baseline '{baseline.baseline_id}' is for domain {baseline.domain.value}, "
                f"requested comparison domain is {domain.value}."
            )

        if baseline.target_name.lower() != target.lower():
            raise IncompatibleBaselineError(
                f"Target mismatch: baseline '{baseline.baseline_id}' targets '{baseline.target_name}', "
                f"requested target is '{target}'."
            )

        if model_version and baseline.model_version and baseline.model_version != model_version:
            raise IncompatibleBaselineError(
                f"Model version mismatch: baseline is {baseline.model_version}, comparison is {model_version}."
            )

        if feature_schema_version and baseline.feature_schema_version and baseline.feature_schema_version != feature_schema_version:
            raise IncompatibleBaselineError(
                f"Feature schema version mismatch: baseline is {baseline.feature_schema_version}, comparison is {feature_schema_version}."
            )

        if graph_layer and baseline.graph_layer and baseline.graph_layer != graph_layer:
            raise IncompatibleBaselineError(
                f"Graph layer mismatch: baseline layer is '{baseline.graph_layer}', comparison is '{graph_layer}'."
            )


# Global singleton instance
baseline_registry = BaselineRegistry()
