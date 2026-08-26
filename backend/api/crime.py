from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional
try:
    from connectors.ncrb import ncrb_connector
    from services.analytics import analytics_service
    from services.graph_builder import graph_builder
except ImportError:
    from ..connectors.ncrb import ncrb_connector
    from ..services.analytics import analytics_service
    from ..services.graph_builder import graph_builder

router = APIRouter(prefix="/crime", tags=["NCRB Crime Statistics"])


@router.get("/overview")
async def get_crime_overview():
    """Retrieve high-level national NCRB cyber crime totals, growth metrics, and top hotspots."""
    return analytics_service.get_overview()


@router.get("/states")
async def get_statewise_crime(limit: Optional[int] = Query(None, description="Limit top states")):
    """Retrieve state/UT comparative cyber crime statistics, conviction rates, and rates per lakh."""
    return analytics_service.get_statewise_summary(limit=limit)


@router.get("/it-act")
async def get_it_act_sections():
    """Retrieve statutory offense breakdown under Information Technology Act & IPC sections."""
    return analytics_service.get_it_act_sections()


@router.post("/sync")
async def sync_live_ncrb_feeds():
    """Trigger live synchronization across all official Open Government Data NCRB feeds."""
    try:
        sync_res = await ncrb_connector.synchronize_all_datasets()
        graph_res = graph_builder.rebuild_graph()
        return {
            "status": "SUCCESS",
            "message": "Successfully synchronized live data.gov.in NCRB feeds and rebuilt Neo4j graph.",
            "sync": sync_res,
            "graph": graph_res,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync NCRB feeds: {str(e)}")
