from fastapi import APIRouter, Query, HTTPException
from typing import Any, Dict, List, Optional

try:
    from database.neo4j import neo4j_db
    from services.graph_builder import graph_builder
except ImportError:
    from ..database.neo4j import neo4j_db
    from ..services.graph_builder import graph_builder

router = APIRouter(prefix="/graph", tags=["Neo4j Cyber Intelligence Graph"])


@router.get("/network")
async def get_cyber_intelligence_network(
    graph_source: Optional[str] = Query("ncrb_public", description="Graph source: 'ncrb_public' or 'investigation_evidence'"),
    search: Optional[str] = Query(None, description="Search node by name or ID"),
    state: Optional[str] = Query(None, description="Filter by state jurisdiction"),
    crime_type: Optional[str] = Query(None, description="Filter by crime category/type"),
    case_id: Optional[str] = Query(None, description="Filter by case ID (for investigation graph)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    node_type: Optional[str] = Query(None, description="Filter by node type"),
):
    """
    Fetch the dual-layer Knowledge Graph based on requested graph source.
    """
    if graph_source == "investigation_evidence":
        return neo4j_db.query_evidence_graph(
            search=search,
            case_id=case_id,
            risk_level=risk_level,
            node_type=node_type,
        )
    else:
        return neo4j_db.query_ncrb_graph(
            search=search,
            state=state,
            crime_category=crime_type,
        )


@router.get("/ncrb-public")
async def get_ncrb_public_graph(
    state: Optional[str] = Query(None, description="Filter by state jurisdiction"),
    crime_category: Optional[str] = Query(None, description="Filter by crime category"),
):
    """
    Fetch Graph 1: Verified NCRB Public Statistical Knowledge Graph.
    Strictly contains only States, Years, IT Act Categories, Motives, Disposals.
    """
    return neo4j_db.query_ncrb_graph(state=state, crime_category=crime_category)


@router.get("/investigation-evidence")
async def get_investigation_evidence_graph(
    case_id: Optional[str] = Query(None, description="Filter by Case Docket ID"),
    search: Optional[str] = Query(None, description="Search suspect or entity"),
):
    """
    Fetch Graph 2: Case Investigation Evidence Graph.
    Contains authorized case dockets, suspects, devices, and financial flows.
    """
    return neo4j_db.query_evidence_graph(case_id=case_id, search=search)


@router.get("/shortest-path")
async def calculate_shortest_path(
    source_id: str = Query(..., description="Source entity ID"),
    target_id: str = Query(..., description="Target entity ID"),
    graph_source: str = Query("investigation_evidence", description="Graph source"),
):
    """
    Calculates the shortest intelligence connection path between two entities.
    """
    path = neo4j_db.find_shortest_path(source_id, target_id, graph_source=graph_source)
    if not path:
        return {"found": False, "path": [], "message": f"No direct path found between {source_id} and {target_id}"}

    nodes = [neo4j_db.get_node(nid) for nid in path if neo4j_db.get_node(nid)]
    return {
        "found": True,
        "pathLength": len(path) - 1,
        "pathNodeIds": path,
        "nodes": nodes,
    }


@router.post("/rebuild")
async def rebuild_knowledge_graphs():
    """
    Rebuilds both Graph 1 (NCRB Public) and Graph 2 (Investigation Evidence).
    """
    result = graph_builder.rebuild_all_graphs()
    return {"status": "SUCCESS", "result": result}
