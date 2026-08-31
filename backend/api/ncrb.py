from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional
try:
    from connectors.ncrb import ncrb_connector
    from services.analytics import analytics_service
    from services.ncrb_temporal_service import ncrb_temporal_service
    from services.ncrb_sync import ncrb_sync_service
except ImportError:
    from ..connectors.ncrb import ncrb_connector
    from ..services.analytics import analytics_service
    from ..services.ncrb_temporal_service import ncrb_temporal_service
    from ..services.ncrb_sync import ncrb_sync_service

router = APIRouter(prefix="/ncrb", tags=["NCRB Open Government Data APIs"])


# =============================================================================
# 1. Dataset Registry & Ingestion Management
# =============================================================================
@router.get("/datasets")
async def get_registered_datasets():
    """Returns list of registered NCRB datasets with versioning and content hashes."""
    return ncrb_temporal_service.get_datasets()


@router.get("/datasets/{dataset_id}")
async def get_dataset_details(dataset_id: str):
    """Returns metadata, schema, and version history for a specific registered dataset."""
    ds = ncrb_temporal_service.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found in registry.")
    return ds


@router.get("/sync/status")
async def get_sync_status():
    """Returns real-time synchronization freshness, active datasets count, and audit log."""
    return ncrb_temporal_service.get_sync_status()


@router.post("/sync/{dataset_id}")
async def sync_single_dataset(dataset_id: str):
    """
    Executes staged transactional synchronization with validation and rollback for a single dataset.
    """
    try:
        return await ncrb_temporal_service.sync_single_dataset(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/sync")
async def sync_all_ncrb_datasets():
    """
    Executes full dynamic synchronization of all 6 NCRB datasets into Neo4j with full provenance.
    Guarantees idempotency on repeated executions.
    """
    return await ncrb_sync_service.synchronize_ncrb_datasets()


# =============================================================================
# 2. Temporal Trends & Historical Trajectory APIs
# =============================================================================
@router.get("/trends")
async def get_cyber_crime_trends(
    state: Optional[str] = Query(None, description="Filter by State or UT name"),
    city: Optional[str] = Query(None, description="Filter by metropolitan city name"),
    crime_category: Optional[str] = Query(None, description="Filter by statutory crime category"),
    year_from: Optional[int] = Query(None, description="Start year bound (e.g. 2023)"),
    year_to: Optional[int] = Query(None, description="End year bound (e.g. 2025)"),
):
    """
    Computes verified YoY absolute change, YoY percentage change, and CAGR across time horizons.
    Returns 'INSUFFICIENT VERIFIED DATA' if observations < 2.
    """
    return ncrb_temporal_service.calculate_trends(
        state=state,
        city=city,
        crime_category=crime_category,
        year_from=year_from,
        year_to=year_to,
    )


@router.get("/trends/{entity_id}")
async def get_entity_trends(entity_id: str):
    """Computes longitudinal trend metrics for a specific state or category node."""
    if entity_id.startswith("STATE-") or not entity_id.startswith("CAT-"):
        state_name = entity_id.replace("STATE-", "")
        return ncrb_temporal_service.calculate_trends(state=state_name)
    else:
        return ncrb_temporal_service.calculate_trends(crime_category=entity_id)


@router.get("/history/{entity_id}")
async def get_entity_history(entity_id: str):
    """Returns verified historical observations for an entity over all available survey years."""
    trends = ncrb_temporal_service.calculate_trends(state=entity_id.replace("STATE-", ""))
    target = next((t for t in trends.get("trends", []) if t.get("entity_id") == entity_id or t.get("entity") == entity_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Historical data for '{entity_id}' not found in knowledge graph.")
    return {
        "entity_id": entity_id,
        "observations": target.get("years", []),
        "source": target.get("source", "NCRB"),
        "dataset_name": target.get("dataset_name"),
        "retrieved_at": target.get("retrieved_at"),
    }


# =============================================================================
# 3. Canonical Crime, Motive & Disposal Queries
# =============================================================================
@router.get("/cyber-crime")
async def get_ncrb_cyber_crime(
    state: Optional[str] = Query(None, description="Filter by State or UT name"),
    year: Optional[int] = Query(None, description="Filter by Year (e.g. 2023, 2024, 2025)"),
):
    """
    Retrieve state/UT-wise cyber crime registration statistics, incident trends,
    and rates per lakh population from NCRB datasets.
    """
    all_states = analytics_service.get_statewise_summary()
    results = []

    for s in all_states:
        if state and state.lower() != "all" and s["state"].lower() != state.lower():
            continue

        item = {
            "state": s["state"],
            "year": year or 2025,
            "incidents": s[f"incidents{year}"] if year and f"incidents{year}" in s else s["incidents2025"],
            "incidents2023": s["incidents2023"],
            "incidents2024": s["incidents2024"],
            "incidents2025": s["incidents2025"],
            "rate_per_lakh": s["ratePerLakh"],
            "chargesheet_rate": s["chargesheetRate"],
            "conviction_rate": s["convictionRate"],
            "persons_arrested": s["personsArrested"],
            "source": "Open Government Data (data.gov.in) NCRB Cyber Crime Feed",
        }
        results.append(item)

    return results


@router.get("/motives")
async def get_ncrb_motives(
    state: Optional[str] = Query(None, description="Filter by State or UT name (e.g. Odisha, Telangana)"),
    year: Optional[int] = Query(None, description="Filter by Year (e.g. 2019, 2020)"),
    motive: Optional[str] = Query(None, description="Filter by Motive keyword (e.g. Fraud, Extortion)"),
):
    """
    Retrieve cyber crime motive distribution from official NCRB Data.gov.in datasets.
    """
    target_year = year or 2020
    dataset_key = "ogd-motives-2019" if target_year == 2019 else "ogd-motives-2020"
    records = ncrb_connector.get_dataset_records(dataset_key)
    if not records:
        records = ncrb_connector._generate_verified_ogd_records(dataset_key)

    filtered = []
    for r in records:
        r_state = r.get("state", "National")
        if state and state.lower() != "all" and r_state.lower() != state.lower():
            continue
        if year and r.get("year") != year:
            continue
        r_motive = r.get("crime_motive", r.get("Motive", ""))
        if motive and motive.lower() not in r_motive.lower():
            continue

        filtered.append({
            "state": r_state,
            "year": r.get("year", target_year),
            "crime_motive": r.get("crime_motive", r.get("Motive", "Unknown")),
            "motive_full": r.get("motive_full", r.get("Motive", "")),
            "cases": r.get("cases", r.get("Cases", 0)),
            "percentage": r.get("percentage", r.get("Percentage", 0.0)),
            "category": r.get("category", r.get("Category", "General")),
            "risk_level": r.get("risk_level", r.get("Risk_Level", "MODERATE")),
        })

    return filtered


@router.get("/investigation")
async def get_ncrb_investigation(
    crime_head: Optional[str] = Query(None, description="Filter by crime head or statutory offense"),
):
    """
    Retrieve police disposal, chargesheeting velocity, and pending investigation telemetry.
    """
    records = analytics_service.get_police_pendency()
    if crime_head and crime_head.lower() != "all":
        records = [r for r in records if crime_head.lower() in r.get("crime_head", r.get("Crime_Head", "")).lower()]
    return records


@router.get("/court")
async def get_ncrb_court(
    crime_head: Optional[str] = Query(None, description="Filter by crime head or statutory offense"),
):
    """
    Retrieve court trial outcomes, judicial convictions, acquittals, and conviction rates.
    """
    records = analytics_service.get_court_efficiency()
    if crime_head and crime_head.lower() != "all":
        records = [r for r in records if crime_head.lower() in r.get("crime_head", r.get("Crime_Head", "")).lower()]
    return records
