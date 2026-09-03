"""Configuration dataclasses for Emerging Threat & Early-Warning Intelligence Engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

DETECTOR_VERSION = "1.0.0"
EVENT_SCHEMA_VERSION = "1.0.0"
SNAPSHOT_SCHEMA_VERSION = "1.0.0"


class TrajectoryType(str, Enum):
    RAPID_ESCALATION = "RAPID_ESCALATION"      # Steep upward slope in threat risk
    SUDDEN_SPIKE = "SUDDEN_SPIKE"              # Abrupt discontinuous jump in risk
    SUSTAINED_ELEVATION = "SUSTAINED_ELEVATION"  # Persistent high-risk level over multiple intervals
    STABLE = "STABLE"                          # Minimal slope or variance
    VOLATILE = "VOLATILE"                      # High oscillation across observation windows
    DE_ESCALATING = "DE_ESCALATING"            # Downward trend in risk


class EventSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventLifecycleState(str, Enum):
    DETECTED = "DETECTED"                      # Initial automated detection (default)
    CONFIRMED_BY_ANALYST = "CONFIRMED_BY_ANALYST"  # Verified by authorized forensic investigator
    RESOLVED = "RESOLVED"                      # Addressed or mitigated
    EXPIRED = "EXPIRED"                        # Observation window elapsed without recurrence


@dataclass
class TopologyEvolutionConfig:
    """Thresholds for detecting significant network topology changes between snapshots."""
    node_growth_rate_threshold: float = 0.50   # 50% increase in nodes
    edge_growth_rate_threshold: float = 0.60   # 60% increase in edges
    node_churn_threshold: float = 0.40         # Churn fraction (added + removed) / total
    edge_churn_threshold: float = 0.50
    density_delta_threshold: float = 0.15      # Sudden density jump
    min_nodes_for_analysis: int = 3


@dataclass
class RiskTrajectoryConfig:
    """Parameters for risk slope, acceleration, and spike detection."""
    rapid_escalation_slope: float = 0.15       # Minimum risk change per snapshot for escalation
    sudden_spike_delta: float = 0.30           # Minimum single-step jump for spike detection
    sustained_elevation_threshold: float = 0.70  # Minimum risk level for sustained elevation
    volatility_variance_threshold: float = 0.08 # Variance threshold for volatility


@dataclass
class CentralityEvolutionConfig:
    """Thresholds for significant centrality shifts and bridge emergence."""
    degree_centrality_shift_threshold: float = 0.25
    betweenness_shift_threshold: float = 0.20
    pagerank_shift_threshold: float = 0.20
    bridge_betweenness_threshold: float = 0.35 # High betweenness bottleneck indicator


@dataclass
class CommunityEvolutionConfig:
    """Thresholds for community restructuring events."""
    community_growth_threshold: float = 0.50
    membership_churn_threshold: float = 0.40


@dataclass
class TemporalBurstConfig:
    """Parameters for event clustering and interaction burst detection."""
    burst_window_seconds: float = 300.0        # 5-minute sliding burst window
    min_events_for_burst: int = 8              # Minimum events in window to qualify
    burst_rate_multiplier: float = 2.5         # Rate compared to baseline


@dataclass
class EarlyWarningWeightsConfig:
    """Weights for synthesizing multi-signal early warning scores."""
    trajectory_weight: float = 1.3
    topology_velocity_weight: float = 1.1
    centrality_shift_weight: float = 1.0
    temporal_burst_weight: float = 1.2
    community_evolution_weight: float = 0.8
    dt_gnn_anomaly_weight: float = 1.2
    threat_fusion_weight: float = 1.0


@dataclass
class SafetyLimitsConfig:
    """Guards against pathological payloads and denial-of-service processing."""
    max_snapshots: int = 100
    max_nodes_per_snapshot: int = 10_000
    max_edges_per_snapshot: int = 25_000
    max_events_returned: int = 500
    max_entities_analyzed: int = 2_000


@dataclass
class EmergingThreatConfig:
    """Master configuration for Phase 13 Emerging Threat & Early-Warning Engine."""
    detector_version: str = DETECTOR_VERSION
    event_schema_version: str = EVENT_SCHEMA_VERSION
    snapshot_schema_version: str = SNAPSHOT_SCHEMA_VERSION

    topology: TopologyEvolutionConfig = field(default_factory=TopologyEvolutionConfig)
    trajectory: RiskTrajectoryConfig = field(default_factory=RiskTrajectoryConfig)
    centrality: CentralityEvolutionConfig = field(default_factory=CentralityEvolutionConfig)
    community: CommunityEvolutionConfig = field(default_factory=CommunityEvolutionConfig)
    burst: TemporalBurstConfig = field(default_factory=TemporalBurstConfig)
    weights: EarlyWarningWeightsConfig = field(default_factory=EarlyWarningWeightsConfig)
    safety_limits: SafetyLimitsConfig = field(default_factory=SafetyLimitsConfig)

    # Early-warning severity thresholds
    critical_warning_threshold: float = 0.80
    high_warning_threshold: float = 0.60
    medium_warning_threshold: float = 0.35

    # Confidence parameters
    min_snapshots_for_confidence: int = 3
    min_confidence_floor: float = 0.15

    # Determinism
    seed: int = 42
