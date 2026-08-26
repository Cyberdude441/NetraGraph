from typing import List, Optional
from pydantic import BaseModel, Field
from .entity import Entity
from .relationship import Relationship


class ThreatAxis(BaseModel):
    axis: str
    score: int = Field(..., ge=0, le=100)


class TimelineEvent(BaseModel):
    date: str
    title: str
    detail: str


class CriminalProfileResponse(BaseModel):
    entity: Entity
    threatRadar: List[ThreatAxis]
    offenses: List[str]
    timeline: List[TimelineEvent]
    directAssociates: List[Entity]
    linkedRelationships: List[Relationship]
    networkCentralityRank: int
    intelligenceBrief: str
