"""Cryptographic provenance hashing and immutable DAG lineage tracking for CTI observations."""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from .models import ThreatIntelProvenanceRecord


def compute_payload_sha256(content: bytes) -> str:
    """Computes cryptographic SHA-256 checksum for physical/digital bitstream verification."""
    return hashlib.sha256(content).hexdigest()


def compute_provenance_id(
    source_id: str,
    indicator_id: str,
    source_record_id: Optional[str],
    timestamp: float,
    raw_payload_sha256: str,
    transformation: str = "raw_cti_ingest",
    sequence_index: int = 0,
) -> str:
    """
    Computes collision-resistant, deterministic provenance ID.
    
    CRITICAL ARCHITECTURAL INVARIANT:
    Contains sufficient entropy material (source, indicator, upstream record ID, exact microsecond
    timestamp, bitstream SHA-256, transformation name, and batch sequence index) so that multiple
    observations within the same second never collide.
    """
    composite = (
        f"{source_id}|{indicator_id}|{source_record_id or 'NONE'}|"
        f"{timestamp:.6f}|{raw_payload_sha256}|{transformation}|{sequence_index}"
    )
    digest = hashlib.sha256(composite.encode("utf-8")).hexdigest()[:16]
    return f"prv-cti:{digest}"


def compute_indicator_id(ioc_type_str: str, canonical_val: str) -> str:
    """Computes deterministic indicator identity: ioc:{type}:{canonical_value_digest[:16]}."""
    val_digest = hashlib.sha256(canonical_val.encode("utf-8")).hexdigest()[:16]
    return f"ioc:{ioc_type_str.lower()}:{val_digest}"


def compute_correlation_id(
    case_id: str,
    entity_id: str,
    indicator_id: str,
    provenance_id: str,
) -> str:
    """Computes deterministic candidate correlation ID."""
    composite = f"{case_id}|{entity_id}|{indicator_id}|{provenance_id}"
    digest = hashlib.sha256(composite.encode("utf-8")).hexdigest()[:16]
    return f"cor:{case_id}:{digest}"


class ThreatIntelProvenanceTracker:
    """Directed Acyclic Graph (DAG) manager tracking provenance for all CTI observations."""

    def __init__(self):
        self._records: Dict[str, ThreatIntelProvenanceRecord] = {}

    def register_record(self, record: ThreatIntelProvenanceRecord) -> str:
        """Registers an immutable provenance record."""
        self._records[record.provenance_id] = record
        return record.provenance_id

    def get_record(self, provenance_id: str) -> Optional[ThreatIntelProvenanceRecord]:
        return self._records.get(provenance_id)

    def build_lineage_chain(self, provenance_id: str, depth_limit: int = 10) -> List[ThreatIntelProvenanceRecord]:
        """
        Traverses parent lineage DAG backwards to reconstruct complete evidence audit trail.
        Safeguarded by depth_limit against potential cyclic references.
        """
        chain: List[ThreatIntelProvenanceRecord] = []
        visited: set = set()
        queue: List[str] = [provenance_id]
        depth = 0

        while queue and depth < depth_limit:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            rec = self._records.get(current_id)
            if rec:
                chain.append(rec)
                for parent_id in rec.parent_provenance_ids:
                    if parent_id not in visited:
                        queue.append(parent_id)
            depth += 1

        return chain

    @property
    def total_records(self) -> int:
        return len(self._records)
