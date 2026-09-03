"""FastAPI router exposing Dynamic Temporal Graph Neural Network (DT-GNN) capabilities."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ml.dynamic_gnn.service import dt_gnn_service

router = APIRouter(prefix="/gnn", tags=["dynamic-gnn"])


class GNNNodeInput(BaseModel):
    id: str = Field(..., description="Unique entity ID")
    type: Optional[str] = Field(default="Unknown", description="Entity categorical classification")
    riskScore: Optional[float] = Field(default=50.0, description="Heuristic or prior risk score (0-100)")
    confidence: Optional[float] = Field(default=0.95, description="Entity confidence score (0-1)")
    timestamp: Optional[float] = Field(default=0.0, description="Creation epoch timestamp in seconds")
    model_predictions: Optional[Dict[str, float]] = Field(default_factory=dict, description="Optional Models A-E predictions")


class GNNEdgeInput(BaseModel):
    sourceId: str = Field(..., description="Source entity ID")
    targetId: str = Field(..., description="Target entity ID")
    type: Optional[str] = Field(default="ASSOCIATED_WITH", description="Relationship type")
    weight: Optional[float] = Field(default=1.0, description="Relationship weight (1-10)")
    confidence: Optional[float] = Field(default=0.90, description="Link confidence (0-1)")
    timestamp: Optional[float] = Field(default=0.0, description="Link event epoch timestamp in seconds")


class GNNAnalyzeRequest(BaseModel):
    case_id: Optional[str] = Field(default="CASE-DIRECT", description="Case or session ID")
    nodes: Optional[List[GNNNodeInput]] = Field(default=None, description="Direct node payloads (if omitted, queries active evidence graph)")
    edges: Optional[List[GNNEdgeInput]] = Field(default=None, description="Direct edge payloads (if omitted, queries active evidence graph)")
    num_snapshots: Optional[int] = Field(default=3, ge=1, le=10, description="Number of temporal windows to discretize")


class GNNHealthResponse(BaseModel):
    status: str
    model_name: str
    version: str
    device: str
    num_spatial_layers: int
    temporal_aggregator: str
    model_fusion_enabled: bool


@router.get("/health", response_model=GNNHealthResponse, status_code=status.HTTP_200_OK)
def get_gnn_health() -> GNNHealthResponse:
    """Returns runtime health and architectural configuration of the DT-GNN model."""
    config = dt_gnn_service.config
    engine = dt_gnn_service.engine
    return GNNHealthResponse(
        status="ONLINE",
        model_name="DynamicTemporalGNN",
        version="v1.0",
        device=str(engine.device),
        num_spatial_layers=config.num_spatial_layers,
        temporal_aggregator=config.temporal_aggregator.value,
        model_fusion_enabled=config.model_fusion.enabled,
    )


@router.post("/analyze", status_code=status.HTTP_200_OK)
def analyze_dynamic_graph(payload: GNNAnalyzeRequest) -> Dict[str, Any]:
    """Performs dynamic temporal graph neural inference on an investigative network.

    If nodes/edges are provided in the payload, analyzes them directly.
    Otherwise, extracts the active evidence graph from Neo4j/in-memory database for the case_id.
    """
    case_id = payload.case_id or "CASE-DIRECT"

    if payload.nodes is not None and payload.edges is not None:
        raw_nodes = [n.model_dump() for n in payload.nodes]
        raw_edges = [e.model_dump() for e in payload.edges]
        return dt_gnn_service.analyze_graph_data(
            nodes=raw_nodes,
            edges=raw_edges,
            case_id=case_id,
            num_snapshots=payload.num_snapshots or 3,
        )

    # Fallback to querying active case graph from Neo4j / Evidence store
    return dt_gnn_service.analyze_active_case_graph(case_id=case_id)
