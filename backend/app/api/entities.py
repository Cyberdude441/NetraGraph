from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from ..models.entity import Entity, EntityType
from ..database.db import db

router = APIRouter(prefix="/entities", tags=["Entities"])


@router.get(
    "",
    response_model=List[Entity],
    summary="Get all intelligence entities",
    description="Retrieve all indexed entities with optional filters by entity type, minimum risk score, syndicate network, or search keyword.",
)
async def get_entities(
    type: Optional[EntityType] = Query(None, description="Filter by entity type (Person, Org, Phone, etc.)"),
    min_risk: Optional[int] = Query(None, ge=0, le=100, description="Minimum threat risk score"),
    network: Optional[str] = Query(None, description="Filter by syndicate network name"),
    search: Optional[str] = Query(None, description="Search query matching name, alias, or ID"),
) -> List[Entity]:
    entities = db.get_all_entities()

    if type:
        entities = [e for e in entities if e.type == type]
    if min_risk is not None:
        entities = [e for e in entities if e.riskScore >= min_risk]
    if network:
        entities = [e for e in entities if (e.metadata.network or "").lower() == network.lower()]
    if search:
        s = search.lower()
        entities = [
            e for e in entities
            if s in e.name.lower()
            or s in (e.metadata.alias or "").lower()
            or s in e.id.lower()
        ]

    return entities


@router.get(
    "/{entity_id}",
    response_model=Entity,
    summary="Get entity by ID",
    description="Retrieve full structured profile details for a specific entity ID.",
)
async def get_entity_by_id(entity_id: str) -> Entity:
    entity = db.get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with ID '{entity_id}' not found in the intelligence index.",
        )
    return entity
