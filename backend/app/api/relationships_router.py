from typing import List, Optional
from fastapi import APIRouter
from ..models.relationship import Relationship
from ..database.db import db

router = APIRouter(prefix="/relationships", tags=["Relationships"])


@router.get("", response_model=List[Relationship])
async def get_relationships() -> List[Relationship]:
    """Retrieve all active relationship links across the intelligence network."""
    return db.get_all_relationships()
