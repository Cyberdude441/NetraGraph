from fastapi import APIRouter
from typing import List
from ..models.audit import AuditLog
from ..database.db import db

router = APIRouter(prefix="/audit", tags=["Security & Compliance Audit"])


@router.get("/logs", response_model=List[AuditLog])
async def get_audit_logs(limit: int = 50):
    """Retrieve official audit logs for compliance with IT Act §69B & Official Secrets Act."""
    return db.get_audit_logs(limit=limit)
