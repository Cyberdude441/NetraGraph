"""Configuration dataclasses for Neuro-Symbolic Threat Fusion & Explainable Intelligence."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

FUSION_VERSION = "1.0.0"
RULE_SET_VERSION = "1.0.0"
EVIDENCE_SCHEMA_VERSION = "1.0.0"
ASSESSMENT_SCHEMA_VERSION = "1.0.0"


class TemporalDecayType(str, Enum):
    EXPONENTIAL = "exponential"
    HALF_LIFE = "half_life"
    LINEAR = "linear"
    NONE = "none"


@dataclass
class SourceWeightsConfig:
    """Configurable weights per intelligence source category. Must be >= 0."""
    model_a_e: float = 1.0           # Models A-E (tabular ML classifiers)
    dt_gnn: float = 1.2              # Dynamic Temporal GNN
    graph_centrality: float = 0.6    # PageRank, Betweenness, Degree
    graph_anomaly: float = 1.0       # Structural topological anomaly engine
    community: float = 0.5           # Modularity community analysis
    temporal_behavior: float = 0.8   # Event velocity and frequency
    symbolic_rule: float = 1.1       # Triggered deterministic heuristic rules


@dataclass
class TemporalDecayConfig:
    """Configuration for recency-based signal weighting."""
    enabled: bool = True
    decay_type: TemporalDecayType = TemporalDecayType.HALF_LIFE
    half_life_seconds: float = 86400.0 * 7.0  # 7 days half-life
    min_weight_floor: float = 0.10            # Historical signals never drop below 10% weight
    reference_timestamp: Optional[float] = None  # Defaults to current evaluation time or latest signal


@dataclass
class DisagreementConfig:
    """Parameters for conflict detection and confidence penalization."""
    disagreement_threshold: float = 0.25      # Variance/spread above which signals are deemed in conflict
    confidence_penalty_slope: float = 0.60    # Sensitivity factor reducing confidence under conflict
    min_confidence_floor: float = 0.10        # Minimum confidence limit


@dataclass
class SafetyLimitsConfig:
    """Guards against pathological payloads and denial-of-service processing."""
    max_entities_per_request: int = 2_000
    max_signals_per_request: int = 5_000
    max_evidence_records: int = 10_000
    max_graph_edges: int = 25_000
    max_explanation_items: int = 50


@dataclass
class ThreatFusionConfig:
    """Master configuration for the Phase 12 Threat Fusion & Explainability Engine."""
    fusion_version: str = FUSION_VERSION
    rule_set_version: str = RULE_SET_VERSION
    source_weights: SourceWeightsConfig = field(default_factory=SourceWeightsConfig)
    temporal_decay: TemporalDecayConfig = field(default_factory=TemporalDecayConfig)
    disagreement: DisagreementConfig = field(default_factory=DisagreementConfig)
    safety_limits: SafetyLimitsConfig = field(default_factory=SafetyLimitsConfig)

    # Risk classification thresholds
    critical_risk_threshold: float = 0.80
    high_risk_threshold: float = 0.60
    medium_risk_threshold: float = 0.35
    supporting_signal_threshold: float = 0.50

    # Determinism
    seed: int = 42
