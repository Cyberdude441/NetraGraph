from fastapi import APIRouter
from typing import Any, Dict, List
try:
    from services.analytics import analytics_service
except ImportError:
    from ..services.analytics import analytics_service

router = APIRouter(prefix="/analytics", tags=["Crime Analytics & Telemetry"])


@router.get("/motives")
async def get_dominant_motives():
    """Retrieve breakdown of cyber crime motives from official NCRB Data.gov.in records."""
    return analytics_service.get_dominant_motives()


@router.get("/police-pendency")
async def get_police_pendency():
    """Retrieve police investigative pendency and disposal efficiency per crime head."""
    return analytics_service.get_police_pendency()


@router.get("/court-efficiency")
async def get_court_efficiency():
    """Retrieve court trial outcome and conviction rates per crime head."""
    return analytics_service.get_court_efficiency()


@router.get("/arrests")
async def get_arrest_trends():
    """Retrieve persons arrested, chargesheeted, and convicted across crime categories."""
    return analytics_service.get_arrest_trends()
