"""FastAPI router for Investigation Timeline, Graph Replay, and Snapshot Reconstruction."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

try:
    from ml.dynamic_gnn.data import parse_iso_timestamp
    from ml.emerging_threat.snapshots import (
        EntitySnapshot,
        GraphSnapshot,
        RelationshipSnapshot,
        TemporalSnapshotSequence,
    )
    from ml.investigation_timeline import (
        EVENT_SCHEMA_VERSION,
        REPLAY_SCHEMA_VERSION,
        TIMELINE_ENGINE_VERSION,
        InvestigationTimelineEvent,
        InvestigatorMarkerRequest,
        ProvenanceType,
        ReconstructedGraphState,
        ReplayManifest,
        TimelineEventType,
        investigation_timeline_service,
    )
except ImportError:
    from ...ml.dynamic_gnn.data import parse_iso_timestamp
    from ...ml.emerging_threat.snapshots import (
        EntitySnapshot,
        GraphSnapshot,
        RelationshipSnapshot,
        TemporalSnapshotSequence,
    )
    from ...ml.investigation_timeline import (
        EVENT_SCHEMA_VERSION,
        REPLAY_SCHEMA_VERSION,
        TIMELINE_ENGINE_VERSION,
        InvestigationTimelineEvent,
        InvestigatorMarkerRequest,
        ProvenanceType,
        ReconstructedGraphState,
        ReplayManifest,
        TimelineEventType,
        investigation_timeline_service,
    )

logger = logging.getLogger("InvestigationTimelineRouter")

router = APIRouter(
    prefix="/investigation-timeline",
    tags=["Investigation Timeline & Graph Replay"],
)


# ============================================================
# Request Schemas
# ============================================================

class TimelineAnalysisRequest(BaseModel):
    network_id: str = Field(..., min_length=1, max_length=100)
    snapshots: List[Dict[str, Any]] = Field(default_factory=list)
    external_dt_gnn_signals: Optional[List[Dict[str, Any]]] = None
    external_fusion_signals: Optional[List[Dict[str, Any]]] = None


class ReplayRequest(BaseModel):
    network_id: str = Field(..., min_length=1, max_length=100)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    snapshots: Optional[List[Dict[str, Any]]] = None
    external_dt_gnn_signals: Optional[List[Dict[str, Any]]] = None
    external_fusion_signals: Optional[List[Dict[str, Any]]] = None


def _parse_sequence_from_payload(raw_snapshots: List[Dict[str, Any]]) -> TemporalSnapshotSequence:
    """Helper to convert API dict payloads into a normalized TemporalSnapshotSequence."""
    converted_snapshots: List[GraphSnapshot] = []

    for idx, s in enumerate(raw_snapshots):
        s_id = s.get("snapshot_id") or f"SNP-{idx:03d}"
        raw_ts = s.get("timestamp")
        if raw_ts is None:
            ts = float(idx)
        elif isinstance(raw_ts, (int, float)):
            ts = float(raw_ts)
        else:
            ts = parse_iso_timestamp(str(raw_ts))

        # Nodes
        nodes_dict: Dict[str, EntitySnapshot] = {}
        raw_nodes = s.get("nodes", {})
        if isinstance(raw_nodes, dict):
            for nid, ndata in raw_nodes.items():
                if isinstance(ndata, dict):
                    nodes_dict[str(nid)] = EntitySnapshot(
                        id=str(nid),
                        entity_type=str(ndata.get("entity_type", "UNKNOWN")),
                        risk_score=float(ndata["risk_score"]) if ndata.get("risk_score") is not None else None,
                        confidence=float(ndata["confidence"]) if ndata.get("confidence") is not None else None,
                        timestamp=ts,
                        attributes=dict(ndata.get("attributes") or {}),
                    )
                else:
                    nodes_dict[str(nid)] = EntitySnapshot(id=str(nid), timestamp=ts)
        elif isinstance(raw_nodes, list):
            for item in raw_nodes:
                if isinstance(item, dict) and "id" in item:
                    nid = str(item["id"])
                    nodes_dict[nid] = EntitySnapshot(
                        id=nid,
                        entity_type=str(item.get("entity_type", "UNKNOWN")),
                        risk_score=float(item["risk_score"]) if item.get("risk_score") is not None else None,
                        confidence=float(item["confidence"]) if item.get("confidence") is not None else None,
                        timestamp=ts,
                        attributes=dict(item.get("attributes") or {}),
                    )

        # Edges
        edges_list: List[RelationshipSnapshot] = []
        raw_edges = s.get("edges", [])
        if isinstance(raw_edges, list):
            for e in raw_edges:
                if isinstance(e, dict):
                    src = str(e.get("source_id") or e.get("source", ""))
                    dst = str(e.get("target_id") or e.get("target", ""))
                    if src and dst:
                        edges_list.append(
                            RelationshipSnapshot(
                                source_id=src,
                                target_id=dst,
                                rel_type=str(e.get("rel_type") or e.get("type", "RELATED_TO")),
                                weight=float(e.get("weight", 1.0)),
                                timestamp=ts,
                                attributes=dict(e.get("attributes") or {}),
                            )
                        )

        converted_snapshots.append(
            GraphSnapshot(
                snapshot_id=s_id,
                timestamp=ts,
                nodes=nodes_dict,
                edges=edges_list,
                dt_gnn_anomaly_score=s.get("dt_gnn_anomaly_score"),
                fusion_risk_score=s.get("fusion_risk_score"),
                metadata=dict(s.get("metadata") or {}),
            )
        )

    return TemporalSnapshotSequence(converted_snapshots)


# ============================================================
# Endpoints
# ============================================================

@router.get("/health", summary="Investigation Timeline Engine Health & Config")
async def get_timeline_health() -> Dict[str, Any]:
    """Return health status, engine versions, and safety limits."""
    return {
        "status": "HEALTHY",
        "engine_version": TIMELINE_ENGINE_VERSION,
        "event_schema_version": EVENT_SCHEMA_VERSION,
        "replay_schema_version": REPLAY_SCHEMA_VERSION,
        "safety_limits": {
            "max_snapshots": investigation_timeline_service.config.safety_limits.max_snapshots,
            "max_nodes": investigation_timeline_service.config.safety_limits.max_nodes,
            "max_edges": investigation_timeline_service.config.safety_limits.max_edges,
            "max_replay_frames": investigation_timeline_service.config.safety_limits.max_replay_frames,
        },
    }


@router.post("/analyze", response_model=List[InvestigationTimelineEvent], summary="Analyze Timeline Events")
async def analyze_timeline(req: TimelineAnalysisRequest) -> List[InvestigationTimelineEvent]:
    """
    Ingest a sequence of snapshots and compute a chronological investigation timeline.
    Rejects oversized requests with HTTP 413.
    """
    try:
        sequence = _parse_sequence_from_payload(req.snapshots)
        events = investigation_timeline_service.analyze_network_timeline(
            network_id=req.network_id,
            sequence=sequence,
            external_dt_gnn_signals=req.external_dt_gnn_signals,
            external_fusion_signals=req.external_fusion_signals,
        )
        return events
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to analyze timeline: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/replay", response_model=ReplayManifest, summary="Generate Investigation Replay Manifest")
async def generate_replay(req: ReplayRequest) -> ReplayManifest:
    """
    Generate frame-by-frame graph replay sequence across specified window.
    Rejects oversized requests with HTTP 413.
    """
    try:
        sequence = _parse_sequence_from_payload(req.snapshots) if req.snapshots else None
        manifest = investigation_timeline_service.generate_replay(
            network_id=req.network_id,
            sequence=sequence,
            start_time=req.start_time,
            end_time=req.end_time,
            external_dt_gnn_signals=req.external_dt_gnn_signals,
            external_fusion_signals=req.external_fusion_signals,
        )
        return manifest
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to generate replay: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{network_id}", summary="Get Network Timeline Status")
async def get_network_status(network_id: str) -> Dict[str, Any]:
    """Retrieve metadata and event count for a cached network timeline."""
    events = investigation_timeline_service.get_events(network_id)
    return {
        "network_id": network_id,
        "event_count": len(events),
        "status": "ACTIVE" if events else "UNINITIALIZED",
    }


@router.get("/{network_id}/events", response_model=List[InvestigationTimelineEvent], summary="Query Network Timeline Events")
async def get_network_events(
    network_id: str,
    start_time: Optional[float] = Query(None, description="Earliest timestamp"),
    end_time: Optional[float] = Query(None, description="Latest timestamp"),
    event_type: Optional[TimelineEventType] = Query(None, description="Filter by event type"),
    entity_id: Optional[str] = Query(None, description="Filter by affected entity ID"),
    provenance_type: Optional[ProvenanceType] = Query(None, description="Filter by provenance type"),
) -> List[InvestigationTimelineEvent]:
    """Query and filter events for a specific network timeline."""
    event_types = [event_type] if event_type else None
    entity_ids = [entity_id] if entity_id else None
    prov_types = [provenance_type] if provenance_type else None

    return investigation_timeline_service.get_events(
        network_id=network_id,
        start_time=start_time,
        end_time=end_time,
        event_types=event_types,
        entity_ids=entity_ids,
        provenance_types=prov_types,
    )


@router.get("/{network_id}/snapshot", response_model=ReconstructedGraphState, summary="Reconstruct Graph State at Time T")
async def reconstruct_snapshot_at_time(
    network_id: str,
    target_timestamp: float = Query(..., description="Unix epoch timestamp to reconstruct"),
) -> ReconstructedGraphState:
    """Reconstruct graph state at target timestamp with exact or approximate semantics."""
    return investigation_timeline_service.reconstruct_snapshot(
        network_id=network_id,
        target_timestamp=target_timestamp,
    )


@router.post("/{network_id}/markers", response_model=InvestigationTimelineEvent, summary="Add Investigator Marker")
async def add_investigator_marker(
    network_id: str,
    req: InvestigatorMarkerRequest,
) -> InvestigationTimelineEvent:
    """Add a human investigator annotation marker to the network timeline."""
    return investigation_timeline_service.add_marker(
        network_id=network_id,
        request=req,
    )
