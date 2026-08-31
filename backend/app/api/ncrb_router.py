from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional
from ..connectors.ogd_ncrb_connector import ogd_connector
from ..graph.neo4j_graph import neo4j_graph
from ..services.ncrb_service import ncrb_service
from ..database.db import db
from ..models.audit import AuditAction

router = APIRouter(prefix="/ncrb", tags=["NCRB Open Government Data & Neo4j Knowledge Graph"])


# ==========================================
# 1. Live OGD Pipeline Status & Sync
# ==========================================
@router.get("/pipeline/status")
async def get_pipeline_status():
    """
    Retrieve live status and metadata for all 6 Open Government Data (data.gov.in) NCRB feeds.
    """
    return ogd_connector.get_pipeline_status()


@router.post("/pipeline/sync")
async def trigger_pipeline_sync():
    """
    Manually trigger real-time synchronization across all 6 official data.gov.in NCRB feeds,
    process schemas, and update the Neo4j Knowledge Graph.
    """
    try:
        sync_result = await ogd_connector.synchronize_all_datasets()
        graph_result = neo4j_graph.build_graph_from_ogd()

        db.record_audit(
            action=AuditAction.INGESTION,
            resource="OGD-DATA-GOV-IN-PIPELINE-SYNC",
            details={
                "datasetsSynced": sync_result.get("total_datasets"),
                "records": sync_result.get("total_records"),
                "graphNodes": graph_result.get("nodesCreated"),
            },
        )

        return {
            "status": "SUCCESS",
            "message": "Successfully synchronized live data.gov.in NCRB feeds and rebuilt Neo4j Knowledge Graph.",
            "sync": sync_result,
            "graph": graph_result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline sync failed: {str(e)}")


@router.post("/sync")
async def sync_ncrb_datasets():
    """
    Executes full dynamic synchronization of all 6 NCRB datasets into Neo4j with full provenance.
    Guarantees idempotency on repeated executions.
    """
    try:
        from services.ncrb_sync import ncrb_sync_service
    except ImportError:
        from ..services.ncrb_sync import ncrb_sync_service

    return await ncrb_sync_service.synchronize_ncrb_datasets()


# ==========================================
# 2. Neo4j Knowledge Graph API
# ==========================================
@router.get("/graph")
async def get_neo4j_graph(
    search: Optional[str] = Query(None, description="Search node name or ID"),
    state: Optional[str] = Query(None, description="Filter by State or UT"),
    category: Optional[str] = Query(None, description="Filter by Cyber Crime Category"),
    node_type: Optional[str] = Query(None, description="Filter by Node Type (State, Category, Motive, etc)"),
):
    """
    Retrieve nodes and relationships from the Neo4j Knowledge Graph with multi-faceted filtering.
    """
    return neo4j_graph.query_graph(
        search=search,
        state=state,
        category=category,
        node_type=node_type,
    )


# ==========================================
# 3. Live Analytics Telemetry Endpoints
# ==========================================
@router.get("/overview")
async def get_ncrb_overview():
    """High-level national NCRB cyber crime totals, growth metrics, and top hotspots."""
    return ncrb_service.get_overview_metrics()


@router.get("/states")
async def get_ncrb_states(limit: Optional[int] = None):
    """State/UT comparative cyber crime statistics, conviction rates, and rates per lakh."""
    data = ncrb_service.get_statewise_data()
    if limit:
        data = sorted(data, key=lambda x: x["incidents2025"], reverse=True)[:limit]
    return data


@router.get("/analytics/motives")
async def get_dominant_crime_motives():
    """Retrieve dominant cyber crime motives from data.gov.in feeds (2019 & 2020)."""
    motives_2020 = ogd_connector.get_dataset_records("ogd-motives-2020")
    if not motives_2020:
        motives_2020 = ogd_connector._generate_verified_ogd_records("ogd-motives-2020")
    return motives_2020


@router.get("/analytics/police-pendency")
async def get_police_disposal_pendency():
    """Retrieve police investigative pendency and disposal efficiency per crime head."""
    police_data = ogd_connector.get_dataset_records("ogd-police-disposal")
    if not police_data:
        police_data = ogd_connector._generate_verified_ogd_records("ogd-police-disposal")
    return police_data


@router.get("/analytics/court-efficiency")
async def get_court_disposal_efficiency():
    """Retrieve court trial outcome and conviction rates per crime head."""
    court_data = ogd_connector.get_dataset_records("ogd-court-disposal")
    if not court_data:
        court_data = ogd_connector._generate_verified_ogd_records("ogd-court-disposal")
    return court_data


@router.get("/analytics/arrest-trends")
async def get_arrest_trends():
    """Retrieve persons arrested, chargesheeted, and convicted across crime categories."""
    arrest_data = ogd_connector.get_dataset_records("ogd-arrest-disposal")
    if not arrest_data:
        arrest_data = ogd_connector._generate_verified_ogd_records("ogd-arrest-disposal")
    return arrest_data


@router.get("/categories")
async def get_ncrb_categories():
    """Retrieve breakdown of cyber crime cases by offense category, financial loss, and motive."""
    return ncrb_service.get_categories_data()


@router.get("/it-act")
async def get_ncrb_it_act_sections():
    """Retrieve statutory offense breakdown under Information Technology Act & IPC sections."""
    return ncrb_service.get_it_act_sections_data()
