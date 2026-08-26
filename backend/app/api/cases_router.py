from fastapi import APIRouter, HTTPException, Header
from typing import List, Optional
from ..models.cases import Case, CaseCreate
from ..database.db import db
from ..models.audit import AuditAction

router = APIRouter(prefix="/cases", tags=["Investigation Cases"])


@router.get("", response_model=List[Case])
async def get_all_cases():
    """Retrieve all registered investigation cases."""
    return db.get_all_cases()


@router.post("", response_model=Case)
async def create_case(
    payload: CaseCreate,
    x_user_id: Optional[str] = Header("IN-BOSE-4417", alias="X-User-ID"),
):
    """Create and open a new Cyber Cell investigation case."""
    case_id = payload.firNumber or f"CS-{len(db.get_all_cases()) + 2200}"
    new_case = Case(
        id=case_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        lead=payload.lead,
        suspects=payload.suspects or 0,
        progress=payload.progress or 15,
        category=payload.category or "Cyber Crime",
        firNumber=payload.firNumber,
    )
    saved = db.save_case(new_case)
    db.record_audit(
        action=AuditAction.INGESTION,
        resource=f"CASE-{case_id}",
        user_id=x_user_id,
        details={"title": payload.title, "priority": payload.priority},
    )
    return saved


@router.get("/{case_id}", response_model=Case)
async def get_case_by_id(case_id: str):
    """Retrieve details for a specific case file."""
    c = db.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case file not found")
    return c
