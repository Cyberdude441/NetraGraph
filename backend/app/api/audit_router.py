"""Security, Chain of Custody & Compliance Audit Router."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, Query

from ..database.db import db
from ..models.audit import AuditLog

try:
    from services.security_service import security_service, Permission
except ImportError:
    from ...services.security_service import security_service, Permission

router = APIRouter(prefix="/audit", tags=["Security & Compliance Audit"])


@router.get("/logs", response_model=List[AuditLog])
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    user_id: Optional[str] = Query(None, description="Filter by officer user ID"),
    action: Optional[str] = Query(None, description="Filter by audit action"),
    x_user_id: Optional[str] = Header("IN-BOSE-4417", alias="X-User-ID"),
):
    """
    Retrieve official immutable audit logs for compliance with IT Act §69B & Official Secrets Act.
    Allows filtering by case, user, action, and date range.
    """
    logs = db.get_audit_logs(limit=500)

    if case_id:
        logs = [
            l for l in logs
            if l.details.get("case_id") == case_id
            or case_id in (l.resource or "")
        ]

    if user_id:
        logs = [l for l in logs if l.userId == user_id]

    if action:
        logs = [l for l in logs if l.action.value.upper() == action.upper() or action.upper() in l.action.value.upper()]

    return logs[:limit]
