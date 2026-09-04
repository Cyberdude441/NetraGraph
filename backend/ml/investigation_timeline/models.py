"""Pydantic contracts and data transfer objects for Investigation Timeline & Graph Replay."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .config import (
    EVENT_SCHEMA_VERSION,
    REPLAY_SCHEMA_VERSION,
    ProvenanceType,
    ReconstructionAccuracy,
    TimelineEventType,
)

MANDATORY_GOVERNANCE_DISCLAIMER: str = (
    "This timeline and graph replay are analytical decision-support outputs based on available source data. "
    "Temporal correlation or structural change does not establish causation, intent, guilt, or criminal "
    "responsibility. Investigators must independently validate findings against source evidence."
)


class GraphEntityState(BaseModel):
    """Point-in-time state of a network entity."""
    id: str
    entity_type: str = "UNKNOWN"
    risk_score: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GraphRelationshipState(BaseModel):
    """Point-in-time state of a relationship between two entities."""
    source_id: str
    target_id: str
    rel_type: str = "RELATED_TO"
    weight: float = 1.0
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ReconstructedGraphState(BaseModel):
    """Deterministic reconstructed network graph state at timestamp T."""
    timestamp: float
    state_hash: str
    accuracy: ReconstructionAccuracy = ReconstructionAccuracy.EXACT
    reference_snapshot_id: Optional[str] = None
    nodes: Dict[str, GraphEntityState] = Field(default_factory=dict)
    edges: List[GraphRelationshipState] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    data_quality_warnings: List[str] = Field(default_factory=list)


class GraphChangeSet(BaseModel):
    """Detected structural and attribute changes between two consecutive graph states."""
    from_timestamp: float
    to_timestamp: float
    added_nodes: List[str] = Field(default_factory=list)
    removed_nodes: List[str] = Field(default_factory=list)
    node_attribute_changes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    added_edges: List[Tuple[str, str, str]] = Field(default_factory=list)
    removed_edges: List[Tuple[str, str, str]] = Field(default_factory=list)
    edge_attribute_changes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    node_count_delta: int = 0
    edge_count_delta: int = 0
    density_delta: float = 0.0
    component_count_delta: int = 0
    is_empty: bool = False


class InvestigationTimelineEvent(BaseModel):
    """A single deterministic event in the chronological investigation timeline."""
    event_id: str
    event_fingerprint: str
    event_type: TimelineEventType
    timestamp: float
    network_id: str
    entity_ids: List[str] = Field(default_factory=list)
    edge_ids: List[str] = Field(default_factory=list)
    provenance_type: ProvenanceType
    source_reference: Optional[str] = None
    confidence: Optional[float] = None
    linked_intelligence_ids: List[str] = Field(default_factory=list)
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = EVENT_SCHEMA_VERSION
    disclaimer: str = MANDATORY_GOVERNANCE_DISCLAIMER


class ReplayFrame(BaseModel):
    """A discrete frame in an investigation replay sequence."""
    frame_index: int
    frame_id: str
    timestamp: float
    state_hash: str
    accuracy: ReconstructionAccuracy
    graph_state: ReconstructedGraphState
    change_from_previous: Optional[GraphChangeSet] = None
    active_events: List[InvestigationTimelineEvent] = Field(default_factory=list)
    provenance_type: ProvenanceType = ProvenanceType.DERIVED
    disclaimer: str = MANDATORY_GOVERNANCE_DISCLAIMER


class ReplayManifest(BaseModel):
    """Complete container for an ordered timeline replay across a specified window."""
    replay_id: str
    network_id: str
    start_time: float
    end_time: float
    total_frames: int
    frames: List[ReplayFrame] = Field(default_factory=list)
    summary_timeline: List[InvestigationTimelineEvent] = Field(default_factory=list)
    data_quality_warnings: List[str] = Field(default_factory=list)
    schema_version: str = REPLAY_SCHEMA_VERSION
    disclaimer: str = MANDATORY_GOVERNANCE_DISCLAIMER


class InvestigatorMarkerRequest(BaseModel):
    """User-supplied payload for adding an investigator marker to a timeline."""
    timestamp: float
    title: str = Field(..., min_length=1, max_length=100)
    note: str = Field(..., min_length=1, max_length=1000)
    linked_entities: List[str] = Field(default_factory=list)
    linked_edges: List[str] = Field(default_factory=list)
    actor_id: str = Field("ANALYST-USER", min_length=1, max_length=100)
