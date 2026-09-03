"""Pydantic event contracts, lifecycle states, and deterministic fingerprinting."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from .config import DETECTOR_VERSION, EVENT_SCHEMA_VERSION, EventLifecycleState, EventSeverity

GOVERNANCE_DISCLAIMER = (
    "Analytical early-warning signal based on temporal and structural patterns; "
    "not a determination of legal culpability, guilt, intent, or causality. Requires human verification."
)


def compute_event_fingerprint(
    network_id: str,
    entity_ids: List[str],
    window_start: float,
    window_end: float,
    event_type: str,
) -> str:
    """Computes a deterministic SHA-256 fingerprint for deduplication."""
    sorted_entities = sorted(list(set(entity_ids)))
    # Round window timestamps to 1-second granularity to resist micro-jitter
    w_start_int = int(round(window_start))
    w_end_int = int(round(window_end))
    raw_payload = f"{network_id}:{':'.join(sorted_entities)}:{w_start_int}:{w_end_int}:{event_type}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


class EmergingThreatEvent(BaseModel):
    """Unified early-warning event contract capturing dynamic network behavior changes."""
    event_id: str = Field(default_factory=lambda: f"EWE-{uuid.uuid4().hex[:12].upper()}")
    event_fingerprint: str = Field(..., description="Deterministic SHA-256 hash for deduplication")
    network_id: str = Field(..., description="Target network or case identifier")
    entity_ids: List[str] = Field(default_factory=list, description="Primary participating entity identifiers")
    detected_at: float = Field(default_factory=lambda: time.time())
    observation_window: Dict[str, float] = Field(default_factory=dict)
    event_type: str = Field(default="MULTI_SIGNAL_ACCELERATION")
    early_warning_score: float = Field(..., ge=0.0, le=1.0, description="Dynamic early-warning score [0, 1]")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in early-warning observation [0, 1]")
    severity: str = Field(..., description="Standardized severity: LOW, MEDIUM, HIGH, CRITICAL")
    lifecycle_state: str = Field(default=EventLifecycleState.DETECTED.value)

    trajectory: Dict[str, Any] = Field(default_factory=dict)
    topology_changes: Dict[str, Any] = Field(default_factory=dict)
    centrality_changes: Dict[str, Any] = Field(default_factory=dict)
    community_changes: Dict[str, Any] = Field(default_factory=dict)
    temporal_bursts: Dict[str, Any] = Field(default_factory=dict)
    subgraph_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    dt_gnn_signals: Dict[str, Any] = Field(default_factory=dict)
    fusion_signals: Dict[str, Any] = Field(default_factory=dict)

    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    contradicting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    explanation: Dict[str, Any] = Field(default_factory=dict)
    detector_version: str = Field(default=DETECTOR_VERSION)
    schema_version: str = Field(default=EVENT_SCHEMA_VERSION)
    disclaimer: str = Field(default=GOVERNANCE_DISCLAIMER)

    @field_validator("early_warning_score", "confidence_score")
    @classmethod
    def validate_bounds(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Score must be bounded between 0.0 and 1.0; got {v}")
        return round(float(v), 4)
