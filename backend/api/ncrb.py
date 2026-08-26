from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional
try:
    from connectors.ncrb import ncrb_connector
    from services.analytics import analytics_service
except ImportError:
    from ..connectors.ncrb import ncrb_connector
    from ..services.analytics import analytics_service

router = APIRouter(prefix="/ncrb", tags=["NCRB Open Government Data APIs"])


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
    Matches schema: { "state": "Odisha", "year": 2020, "crime_motive": "Fraud", "cases": 1200 }
    """
    target_year = year or 2020
    dataset_key = "ogd-motives-2019" if target_year == 2019 else "ogd-motives-2020"
    records = ncrb_connector.get_dataset_records(dataset_key)
    if not records:
        records = ncrb_connector._generate_verified_ogd_records(dataset_key)

    filtered = []
    for r in records:
        # Check state filter
        r_state = r.get("state", "National")
        if state and state.lower() != "all" and r_state.lower() != state.lower():
            continue

        # Check year filter
        if year and r.get("year") != year:
            continue

        # Check motive filter
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
