"""FastAPI router exposing Emerging Threat & Early-Warning Intelligence endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from ml.emerging_threat.config import DETECTOR_VERSION, EVENT_SCHEMA_VERSION
from ml.emerging_threat.events import EmergingThreatEvent
from ml.emerging_threat.service import emerging_threat_service
from ml.emerging_threat.snapshots import (
    EntitySnapshot,
    GraphSnapshot,
    RelationshipSnapshot,
    TemporalSnapshotSequence,
)

router = APIRouter(prefix="/emerging-threat", tags=["Emerging Threat & Early-Warning"])


class EntitySnapshotInput(BaseModel):
    id: str
    entity_type: Optional[str] = "Unknown"
    risk_score: Optional[float] = None
    confidence: Optional[float] = 0.80
    timestamp: Optional[float] = 0.0
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RelationshipSnapshotInput(BaseModel):
    source_id: str
    target_id: str
    rel_type: Optional[str] = "ASSOCIATED_WITH"
    weight: Optional[float] = 1.0
    timestamp: Optional[float] = 0.0
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GraphSnapshotInput(BaseModel):
    snapshot_id: Optional[str] = None
    timestamp: float = Field(..., description="Snapshot observation Unix epoch seconds")
    nodes: Optional[List[EntitySnapshotInput]] = Field(default_factory=list)
    edges: Optional[List[RelationshipSnapshotInput]] = Field(default_factory=list)
    dt_gnn_anomaly_score: Optional[float] = None
    fusion_risk_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EmergingThreatAnalyzeRequest(BaseModel):
    network_id: str = Field(..., description="Target network or case identifier")
    snapshots: List[GraphSnapshotInput] = Field(..., description="Chronological sequence of graph snapshots")
    dt_gnn_anomaly_score: Optional[float] = None
    fusion_risk_score: Optional[float] = None


class EmergingThreatHealthResponse(BaseModel):
    status: str
    detector_version: str
    event_schema_version: str
    active_events_count: int


@router.get("/health", response_model=EmergingThreatHealthResponse, status_code=status.HTTP_200_OK)
def get_emerging_threat_health() -> EmergingThreatHealthResponse:
    """Returns operational health, versioning, and active event count for the engine."""
    events = emerging_threat_service.list_events(limit=1000)
    return EmergingThreatHealthResponse(
        status="ONLINE",
        detector_version=DETECTOR_VERSION,
        event_schema_version=EVENT_SCHEMA_VERSION,
        active_events_count=len(events),
    )


@router.post("/analyze", response_model=EmergingThreatEvent, status_code=status.HTTP_200_OK)
def analyze_emerging_threats(payload: EmergingThreatAnalyzeRequest) -> EmergingThreatEvent:
    """Analyzes a temporal sequence of graph snapshots and generates an early-warning event."""
    snapshots: List[GraphSnapshot] = []

    for s_in in payload.snapshots:
        node_map: Dict[str, EntitySnapshot] = {}
        for n_in in s_in.nodes or []:
            node_map[n_in.id] = EntitySnapshot(
                id=n_in.id,
                entity_type=n_in.entity_type or "Unknown",
                risk_score=n_in.risk_score,
                confidence=n_in.confidence if n_in.confidence is not None else 0.80,
                timestamp=n_in.timestamp or s_in.timestamp,
                attributes=n_in.attributes or {},
            )

        edge_list: List[RelationshipSnapshot] = []
        for e_in in s_in.edges or []:
            edge_list.append(
                RelationshipSnapshot(
                    source_id=e_in.source_id,
                    target_id=e_in.target_id,
                    rel_type=e_in.rel_type or "ASSOCIATED_WITH",
                    weight=e_in.weight if e_in.weight is not None else 1.0,
                    timestamp=e_in.timestamp or s_in.timestamp,
                    attributes=e_in.attributes or {},
                )
            )

        snap = GraphSnapshot(
            snapshot_id=s_in.snapshot_id or f"SNP-{int(s_in.timestamp)}",
            timestamp=s_in.timestamp,
            nodes=node_map,
            edges=edge_list,
            dt_gnn_anomaly_score=s_in.dt_gnn_anomaly_score,
            fusion_risk_score=s_in.fusion_risk_score,
            metadata=s_in.metadata or {},
        )
        snapshots.append(snap)

    sequence = TemporalSnapshotSequence(snapshots)

    return emerging_threat_service.analyze_network_sequence(
        network_id=payload.network_id,
        sequence=sequence,
        external_dt_gnn_score=payload.dt_gnn_anomaly_score,
        external_fusion_score=payload.fusion_risk_score,
    )


@router.post("/network/{network_id}", response_model=EmergingThreatEvent, status_code=status.HTTP_200_OK)
def analyze_network_by_id(
    network_id: str = Path(..., description="Target network or case identifier"),
    snapshots: Optional[List[GraphSnapshotInput]] = None,
) -> EmergingThreatEvent:
    """Evaluates early-warning indicators for a network using provided snapshots."""
    input_snapshots: List[GraphSnapshot] = []
    if snapshots:
        for s_in in snapshots:
            node_map = {
                n_in.id: EntitySnapshot(
                    id=n_in.id,
                    entity_type=n_in.entity_type or "Unknown",
                    risk_score=n_in.risk_score,
                    timestamp=n_in.timestamp or s_in.timestamp,
                )
                for n_in in s_in.nodes or []
            }
            edge_list = [
                RelationshipSnapshot(
                    source_id=e_in.source_id,
                    target_id=e_in.target_id,
                    rel_type=e_in.rel_type or "ASSOCIATED_WITH",
                    timestamp=e_in.timestamp or s_in.timestamp,
                )
                for e_in in s_in.edges or []
            ]
            input_snapshots.append(
                GraphSnapshot(
                    snapshot_id=s_in.snapshot_id or f"SNP-{int(s_in.timestamp)}",
                    timestamp=s_in.timestamp,
                    nodes=node_map,
                    edges=edge_list,
                )
            )

    sequence = TemporalSnapshotSequence(input_snapshots)
    return emerging_threat_service.analyze_network_sequence(network_id, sequence)


@router.get("/events", response_model=List[EmergingThreatEvent], status_code=status.HTTP_200_OK)
def list_emerging_threat_events(
    network_id: Optional[str] = Query(None, description="Filter by network ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
) -> List[EmergingThreatEvent]:
    """Retrieves active early-warning events with optional filtering."""
    return emerging_threat_service.list_events(network_id=network_id, severity=severity, limit=limit)


@router.get("/events/{event_id}", response_model=EmergingThreatEvent, status_code=status.HTTP_200_OK)
def get_emerging_threat_event(
    event_id: str = Path(..., description="Event UUID or SHA-256 fingerprint"),
) -> EmergingThreatEvent:
    """Retrieves a specific early-warning event by ID or fingerprint."""
    event = emerging_threat_service.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Early-warning event '{event_id}' not found.",
        )
    return event
