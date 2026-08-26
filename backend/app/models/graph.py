from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .entity import Entity
from .relationship import Relationship


class NodeCentrality(BaseModel):
    degree: int = Field(..., description="Number of direct links")
    betweenness: float = Field(..., description="Betweenness centrality bridge metric")
    closeness: float = Field(..., description="Closeness centrality score")
    pagerank: float = Field(..., description="PageRank importance score")
    communityId: Optional[int] = Field(default=0, description="Detected syndicate cluster group")


class MultiHopGraphResponse(BaseModel):
    rootEntityId: str
    hopDepth: int
    nodes: List[Entity]
    edges: List[Relationship]
    centrality: Dict[str, NodeCentrality]
    subgraphStats: Dict[str, Any] = Field(default_factory=dict)


class NetworkGraphResponse(BaseModel):
    nodes: List[Entity]
    edges: List[Relationship]
    totalNodes: int
    totalEdges: int
    highRiskNodesCount: int
