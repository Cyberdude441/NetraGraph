from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from ..models.graph import MultiHopGraphResponse, NetworkGraphResponse
from ..services.network_service import network_service

router = APIRouter(prefix="/network", tags=["Network Graph"])


@router.get(
    "",
    response_model=NetworkGraphResponse,
    summary="Get full network graph overview",
    description="Returns all active nodes and relationship edges across all criminal syndicates.",
)
async def get_network_overview() -> NetworkGraphResponse:
    return network_service.get_full_network_graph()


@router.get(
    "/{entity_id}",
    response_model=MultiHopGraphResponse,
    summary="Get multi-hop subgraph for an entity",
    description="Computes 1-hop, 2-hop, or 3-hop neighborhood around a root entity with centrality metrics using NetworkX.",
)
async def get_entity_subgraph(
    entity_id: str,
    hops: Optional[int] = Query(2, ge=1, le=4, description="Multi-hop expansion depth (1-4 hops)"),
) -> MultiHopGraphResponse:
    subgraph = network_service.get_entity_network(entity_id, hops=hops)
    if not subgraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{entity_id}' not found in the criminal network graph.",
        )
    return subgraph
