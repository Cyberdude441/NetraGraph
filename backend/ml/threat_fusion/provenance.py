"""Provenance tracking primitives and lineage audit DAGs."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .signals import SignalSource


@dataclass
class ProvenanceRecord:
    """Immutable provenance record establishing the lineage of an analytical signal."""
    provenance_id: str = field(default_factory=lambda: f"PRV-{uuid.uuid4().hex[:10].upper()}")
    source: SignalSource = SignalSource.MODEL_A_E
    source_type: str = "forensic_ml_classifier"
    collection_timestamp: float = 0.0          # Original observation/collection epoch seconds
    processing_timestamp: float = field(default_factory=lambda: time.time())
    transformation_performed: str = "raw_signal_ingestion"
    model_or_rule_version: str = "1.0.0"
    parent_provenance_ids: List[str] = field(default_factory=list)
    is_available: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_unavailable(
        cls,
        source: SignalSource,
        source_type: str = "unknown",
        reason: str = "Lineage unavailable from upstream producer",
    ) -> ProvenanceRecord:
        """Explicitly records that provenance is absent rather than fabricating lineage."""
        return cls(
            source=source,
            source_type=source_type,
            transformation_performed="unavailable",
            model_or_rule_version="unknown",
            is_available=False,
            metadata={"reason": reason},
        )


class ProvenanceTracker:
    """Maintains an auditable directed acyclic graph (DAG) of signal derivations."""

    def __init__(self):
        self._records: Dict[str, ProvenanceRecord] = {}

    def register(self, record: ProvenanceRecord) -> str:
        self._records[record.provenance_id] = record
        return record.provenance_id

    def get(self, provenance_id: str) -> Optional[ProvenanceRecord]:
        return self._records.get(provenance_id)

    def build_lineage_chain(self, provenance_id: str, depth_limit: int = 10) -> List[ProvenanceRecord]:
        """Traverses parent lineage backwards to reconstruct the evidence chain."""
        chain: List[ProvenanceRecord] = []
        visited = set()
        queue = [provenance_id]

        while queue and len(chain) < depth_limit:
            pid = queue.pop(0)
            if pid in visited:
                continue
            visited.add(pid)
            rec = self._records.get(pid)
            if rec:
                chain.append(rec)
                queue.extend(rec.parent_provenance_ids)

        return chain
