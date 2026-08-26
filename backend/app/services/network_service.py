from typing import List, Optional
from ..models.graph import NetworkGraphResponse, MultiHopGraphResponse
from ..database.db import db
from ..graph.network_manager import graph_manager


class NetworkService:
    """Service to handle Graph queries and multi-hop link analysis."""

    def get_full_network_graph(self) -> NetworkGraphResponse:
        entities = db.get_all_entities()
        relationships = db.get_all_relationships()
        high_risk_count = sum(1 for e in entities if e.riskScore >= 80)

        return NetworkGraphResponse(
            nodes=entities,
            edges=relationships,
            totalNodes=len(entities),
            totalEdges=len(relationships),
            highRiskNodesCount=high_risk_count,
        )

    def get_entity_network(self, entity_id: str, hops: int = 2) -> Optional[MultiHopGraphResponse]:
        return graph_manager.get_multi_hop_subgraph(entity_id, max_hops=hops)


network_service = NetworkService()
