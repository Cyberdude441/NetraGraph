"""Typed representations and normalization primitives for intelligence threat signals."""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalSource(str, Enum):
    MODEL_A_E = "model_a_e"                  # Tabular forensic ML classifiers (Models A-E)
    DT_GNN = "dt_gnn"                        # Dynamic Temporal Graph Neural Network
    GRAPH_CENTRALITY = "graph_centrality"    # Topological PageRank, Betweenness, Closeness
    GRAPH_ANOMALY = "graph_anomaly"          # Graph anomaly engine (Shared infra, bridge nodes)
    COMMUNITY = "community"                  # Syndicate community modularity
    TEMPORAL_BEHAVIOR = "temporal_behavior"  # Event frequency and velocity
    SYMBOLIC_RULE = "symbolic_rule"          # Transparent deterministic heuristic rules
    EXTERNAL = "external"                    # External OSINT, FIR, CDR, Bank feed


class SignalSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def normalize_score(val: Any) -> Optional[float]:
    """Strictly normalizes any numeric score into the range [0.0, 1.0].

    Returns None if missing/invalid to prevent fabricating scores.
    """
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return max(0.0, min(1.0, f))
    except (ValueError, TypeError):
        return None


def calculate_severity(score: Optional[float]) -> SignalSeverity:
    """Deterministically maps a normalized [0, 1] score into a standardized severity tier."""
    if score is None:
        return SignalSeverity.LOW
    if score >= 0.80:
        return SignalSeverity.CRITICAL
    if score >= 0.60:
        return SignalSeverity.HIGH
    if score >= 0.35:
        return SignalSeverity.MEDIUM
    return SignalSeverity.LOW


@dataclass
class ThreatSignal:
    """Standardized representation of a single evidence or analytical signal."""
    signal_id: str = field(default_factory=lambda: f"SIG-{uuid.uuid4().hex[:10].upper()}")
    source: SignalSource = SignalSource.MODEL_A_E
    entity_id: str = "UNKNOWN"
    signal_type: str = "threat_indicator"
    score: Optional[float] = 0.50            # Normalized to [0, 1]
    confidence: float = 0.80                 # Confidence in this signal [0, 1]
    timestamp: float = 0.0                   # Epoch timestamp in seconds
    severity: SignalSeverity = SignalSeverity.MEDIUM
    explanation: str = "Model-derived analytical indicator."
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance_id: Optional[str] = None
    is_missing: bool = False

    def __post_init__(self):
        # Enforce strict normalization
        if self.score is None:
            self.is_missing = True
            self.severity = SignalSeverity.LOW
        else:
            self.score = max(0.0, min(1.0, float(self.score)))
            self.severity = calculate_severity(self.score)

        self.confidence = max(0.0, min(1.0, float(self.confidence)))

        if not self.provenance_id:
            self.provenance_id = f"PRV-{self.signal_id}"

    @classmethod
    def create_missing(
        cls,
        source: SignalSource,
        entity_id: str,
        signal_type: str,
        timestamp: float = 0.0,
        explanation: str = "Signal value not provided by source.",
    ) -> ThreatSignal:
        """Explicitly represents an absent signal without fabricating a score or confidence."""
        return cls(
            source=source,
            entity_id=entity_id,
            signal_type=signal_type,
            score=None,
            confidence=0.0,
            timestamp=timestamp,
            severity=SignalSeverity.LOW,
            explanation=explanation,
            is_missing=True,
        )
