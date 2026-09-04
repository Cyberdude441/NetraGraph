"""Configuration dataclasses, enumerations, and safety limits for Investigation Timeline & Replay."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

TIMELINE_ENGINE_VERSION = "1.0.0"
EVENT_SCHEMA_VERSION = "1.0.0"
REPLAY_SCHEMA_VERSION = "1.0.0"


class TimelineEventType(str, Enum):
    """Categorized timeline events in chronological forensic reconstruction."""
    GRAPH_SNAPSHOT = "GRAPH_SNAPSHOT"
    NODE_ADDED = "NODE_ADDED"
    NODE_REMOVED = "NODE_REMOVED"
    EDGE_ADDED = "EDGE_ADDED"
    EDGE_REMOVED = "EDGE_REMOVED"
    NODE_ATTRIBUTE_CHANGED = "NODE_ATTRIBUTE_CHANGED"
    EDGE_ATTRIBUTE_CHANGED = "EDGE_ATTRIBUTE_CHANGED"
    COMMUNITY_CHANGED = "COMMUNITY_CHANGED"
    CENTRALITY_CHANGED = "CENTRALITY_CHANGED"
    EMERGING_THREAT = "EMERGING_THREAT"
    THREAT_FUSION_SIGNAL = "THREAT_FUSION_SIGNAL"
    DT_GNN_SIGNAL = "DT_GNN_SIGNAL"
    INVESTIGATION_MARKER = "INVESTIGATION_MARKER"


class ProvenanceType(str, Enum):
    """Lineage origin classification for timeline events and graph changes."""
    SOURCE = "SOURCE"                    # Raw observation from source graph/case record
    DERIVED = "DERIVED"                  # Computed structural delta or algorithm output
    CORRELATED = "CORRELATED"            # Linked intelligence event (Phase 12/13 or DT-GNN)
    APPROXIMATED = "APPROXIMATED"        # Interpolated from nearest valid snapshot


class ReconstructionAccuracy(str, Enum):
    """Classification of graph state reconstruction fidelity."""
    EXACT = "EXACT"                      # Exact timestamp match with verified snapshot
    APPROXIMATED = "APPROXIMATED"        # Nearest valid snapshot interpolation
    EMPTY_INTERPOLATED = "EMPTY_INTERPOLATED"  # Empty baseline state when no snapshot matches


@dataclass
class SafetyLimitsConfig:
    """Configurable bounds guarding against computational and memory exhaustion."""
    max_snapshots: int = 100
    max_timeline_events: int = 1000
    max_nodes: int = 10_000
    max_edges: int = 25_000
    max_replay_frames: int = 200
    max_window_duration_seconds: float = 315_360_000.0  # 10 years max window


@dataclass
class TimelineConfig:
    """Master configuration for the Investigation Timeline and Graph Replay Engine."""
    engine_version: str = TIMELINE_ENGINE_VERSION
    event_schema_version: str = EVENT_SCHEMA_VERSION
    replay_schema_version: str = REPLAY_SCHEMA_VERSION

    safety_limits: SafetyLimitsConfig = field(default_factory=SafetyLimitsConfig)
    correlation_window_seconds: float = 300.0       # 5-minute window for adjacent correlations
    approximation_tolerance_seconds: float = 86400.0 # 24-hour max delta for nearest-snapshot approximation
    include_structural_events: bool = True
    include_attribute_events: bool = True
