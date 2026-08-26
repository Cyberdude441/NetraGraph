from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .entity import Entity


class AnalysisRequest(BaseModel):
    query: str = Field(..., description="Investigative reasoning question or directive")
    targetEntityId: Optional[str] = Field(default=None, description="Optional focus subject ID")
    scopeNetwork: Optional[str] = Field(default="Ghost Ledger", description="Syndicate cluster to query")
    includePathfinding: Optional[bool] = Field(default=True, description="Calculate shortest path between flagged nodes")


class PathSegment(BaseModel):
    sourceName: str
    targetName: str
    relationshipType: str
    detail: str


class AnalysisResponse(BaseModel):
    query: str
    reasoning: str
    keyFindings: List[str]
    flaggedEntities: List[Entity]
    identifiedBridges: List[str]
    suggestedActions: List[str]
    confidenceScore: float = Field(default=0.92, ge=0.0, le=1.0)
    graphPath: Optional[List[PathSegment]] = Field(default_factory=list)
