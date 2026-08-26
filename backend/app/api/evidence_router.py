from fastapi import APIRouter, HTTPException, Header
from typing import List, Optional
from ..database.db import db
from ..models.audit import AuditAction

router = APIRouter(prefix="/evidence", tags=["Evidence Vault & Chain of Custody"])


@router.get("")
async def get_all_evidence():
    """Retrieve all cryptographic evidence items stored in the vault."""
    return db.get_all_evidence()


@router.post("")
async def register_evidence(
    payload: dict,
    x_user_id: Optional[str] = Header("IN-BOSE-4417", alias="X-User-ID"),
):
    """Register and store an evidence item in the vault."""
    ev_id = payload.get("id") or f"EV-{len(db.get_all_evidence()) + 1000}"
    payload["id"] = ev_id
    saved = db.save_evidence(ev_id, payload)
    db.record_audit(
        action=AuditAction.UPDATE_EVIDENCE,
        resource=f"EVIDENCE-{ev_id}",
        user_id=x_user_id,
        details={"fileName": payload.get("fileName"), "hash": payload.get("hash")},
    )
    return saved
