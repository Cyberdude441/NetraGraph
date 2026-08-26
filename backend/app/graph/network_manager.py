import networkx as nx
from typing import Dict, List, Optional, Set, Tuple
from ..models.entity import Entity
from ..models.relationship import Relationship
from ..models.graph import NodeCentrality, MultiHopGraphResponse
from ..database.db import db


class NetworkGraphManager:
    """NetworkX Graph Engine for Criminal Network Link Analysis."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.undirected_graph = nx.Graph()
        self._sync_with_db()

    def _sync_with_db(self):
        """Build NetworkX graph from database records."""
        self.graph.clear()
        self.undirected_graph.clear()

        entities = db.get_all_entities()
        for e in entities:
            self.graph.add_node(
                e.id,
                name=e.name,
                type=e.type.value,
                riskScore=e.riskScore,
                metadata=e.metadata.model_dump(),
            )
            self.undirected_graph.add_node(e.id, name=e.name, riskScore=e.riskScore)

        relationships = db.get_all_relationships()
        for r in relationships:
            weight = r.metadata.weight or 5
            self.graph.add_edge(
                r.sourceId,
                r.targetId,
                key=r.id,
                rel_type=r.type.value,
                weight=weight,
                confidence=r.confidence,
                metadata=r.metadata.model_dump(),
            )
            self.undirected_graph.add_edge(
                r.sourceId,
                r.targetId,
                weight=weight,
                rel_id=r.id,
            )

    def add_entity_node(self, entity: Entity):
        """Add or update an entity in the graph."""
        self.graph.add_node(
            entity.id,
            name=entity.name,
            type=entity.type.value,
            riskScore=entity.riskScore,
            metadata=entity.metadata.model_dump(),
        )
        self.undirected_graph.add_node(entity.id, name=entity.name, riskScore=entity.riskScore)

    def add_relationship_edge(self, rel: Relationship):
        """Add or update a relationship link in the graph."""
        weight = rel.metadata.weight or 5
        self.graph.add_edge(
            rel.sourceId,
            rel.targetId,
            key=rel.id,
            rel_type=rel.type.value,
            weight=weight,
            confidence=rel.confidence,
            metadata=rel.metadata.model_dump(),
        )
        self.undirected_graph.add_edge(
            rel.sourceId,
            rel.targetId,
            weight=weight,
            rel_id=rel.id,
        )

    def calculate_centralities(self) -> Dict[str, NodeCentrality]:
        """Compute degree, betweenness, closeness, and PageRank for all graph nodes."""
        if self.graph.number_of_nodes() == 0:
            return {}

        undirected = self.undirected_graph
        degree_dict = dict(undirected.degree())
        betweenness_dict = nx.betweenness_centrality(undirected) if len(undirected) > 2 else {n: 0.0 for n in undirected}
        closeness_dict = nx.closeness_centrality(undirected) if len(undirected) > 1 else {n: 0.0 for n in undirected}
        
        try:
            pagerank_dict = nx.pagerank(self.graph, weight="weight")
        except Exception:
            pagerank_dict = {n: 1.0 / len(self.graph) for n in self.graph}

        centrality_map: Dict[str, NodeCentrality] = {}
        for node_id in self.graph.nodes():
            centrality_map[node_id] = NodeCentrality(
                degree=degree_dict.get(node_id, 0),
                betweenness=round(betweenness_dict.get(node_id, 0.0), 3),
                closeness=round(closeness_dict.get(node_id, 0.0), 3),
                pagerank=round(pagerank_dict.get(node_id, 0.0), 3),
                communityId=1 if degree_dict.get(node_id, 0) > 3 else 2,
            )

        return centrality_map

    def get_multi_hop_subgraph(self, root_id: str, max_hops: int = 2) -> Optional[MultiHopGraphResponse]:
        """Extract multi-hop neighborhood around root entity."""
        if not self.graph.has_node(root_id):
            return None

        # NetworkX BFS ego-graph
        subgraph_nodes: Set[str] = set()
        subgraph_nodes.add(root_id)

        current_level = {root_id}
        for _ in range(max_hops):
            next_level = set()
            for n in current_level:
                if self.undirected_graph.has_node(n):
                    neighbors = set(self.undirected_graph.neighbors(n))
                    next_level.update(neighbors)
            next_level.difference_update(subgraph_nodes)
            subgraph_nodes.update(next_level)
            current_level = next_level
            if not current_level:
                break

        # Retrieve full entities from DB
        entities = [db.get_entity_by_id(nid) for nid in subgraph_nodes if db.get_entity_by_id(nid) is not None]

        # Retrieve relevant relationships
        all_rels = db.get_all_relationships()
        edges = [
            r for r in all_rels
            if r.sourceId in subgraph_nodes and r.targetId in subgraph_nodes
        ]

        centralities = self.calculate_centralities()
        subgraph_centrality = {nid: centralities.get(nid) for nid in subgraph_nodes if nid in centralities}

        return MultiHopGraphResponse(
            rootEntityId=root_id,
            hopDepth=max_hops,
            nodes=[e for e in entities if e is not None],
            edges=edges,
            centrality=subgraph_centrality,
            subgraphStats={
                "totalNodes": len(entities),
                "totalEdges": len(edges),
                "density": round(nx.density(self.undirected_graph.subgraph(subgraph_nodes)), 3) if len(subgraph_nodes) > 1 else 0.0,
            }
        )

    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find the shortest connection path between two criminal nodes."""
        if not (self.undirected_graph.has_node(source_id) and self.undirected_graph.has_node(target_id)):
            return None
        try:
            return nx.shortest_path(self.undirected_graph, source=source_id, target=target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None


# Global singleton instance
graph_manager = NetworkGraphManager()
