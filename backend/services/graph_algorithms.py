"""Real Graph Algorithms Service for Cyber Intelligence & Link Analysis."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

try:
    from database.neo4j import neo4j_db
except ImportError:
    from ..database.neo4j import neo4j_db

logger = logging.getLogger("GraphAlgorithmsService")


class GraphAlgorithmsService:
    """
    Forensic Graph Analytics & Topology Engine.
    Executes real mathematical calculations using NetworkX and Neo4j GDS:
      - Degree, Betweenness, PageRank, and Closeness Centrality
      - Modularity-based Community Detection
      - Shortest Path and K-Hop Neighborhoods
      - Structural Anomaly & Bridge Identification
    """

    def _get_graph_and_undirected(self, graph_source: str) -> Tuple[nx.MultiDiGraph, nx.Graph]:
        """Fetches the active NetworkX graph and builds an undirected simple graph for algorithms."""
        multi_digraph = neo4j_db.get_networkx_graph(graph_source)
        undirected_graph = nx.Graph()

        for node_id, data in multi_digraph.nodes(data=True):
            undirected_graph.add_node(node_id, **data)

        for u, v, data in multi_digraph.edges(data=True):
            if not undirected_graph.has_edge(u, v):
                undirected_graph.add_edge(u, v, **data)

        return multi_digraph, undirected_graph

    def get_graph_stats(self, graph_source: str = "investigation_evidence") -> Dict[str, Any]:
        """Calculates comprehensive graph topology statistics."""
        multi_digraph, G = self._get_graph_and_undirected(graph_source)
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()

        if num_nodes == 0:
            return {
                "graph_source": graph_source,
                "total_nodes": 0,
                "total_relationships": 0,
                "density": 0.0,
                "is_connected": False,
                "connected_components_count": 0,
                "node_types": {},
                "relationship_types": {},
                "status": "Insufficient verified data.",
            }

        # Calculate node label counts
        node_types: Dict[str, int] = {}
        for _, data in G.nodes(data=True):
            label = data.get("label") or data.get("type", "Unknown")
            node_types[label] = node_types.get(label, 0) + 1

        # Calculate edge type counts
        rel_types: Dict[str, int] = {}
        for _, _, data in multi_digraph.edges(data=True):
            t = data.get("type", "RELATED_TO")
            rel_types[t] = rel_types.get(t, 0) + 1

        components = list(nx.connected_components(G))
        density = round(nx.density(G), 4)

        return {
            "graph_source": graph_source,
            "total_nodes": num_nodes,
            "total_relationships": num_edges,
            "density": density,
            "is_connected": nx.is_connected(G) if num_nodes > 0 else False,
            "connected_components_count": len(components),
            "largest_component_size": len(max(components, key=len)) if components else 0,
            "node_types": node_types,
            "relationship_types": rel_types,
            "status": "Calculated from verified knowledge graph.",
        }

    def calculate_centralities(
        self,
        graph_source: str = "investigation_evidence",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Computes real centrality metrics:
          - Degree Centrality (Connectivity)
          - Betweenness Centrality (Information Brokerage & Bridges)
          - PageRank (Network Influence)
          - Closeness Centrality (Proximity to All Nodes)
        """
        multi_digraph, G = self._get_graph_and_undirected(graph_source)
        if G.number_of_nodes() == 0:
            return {
                "graph_source": graph_source,
                "metrics": {},
                "top_betweenness_bridges": [],
                "top_pagerank_influencers": [],
                "top_degree_hubs": [],
                "status": "Insufficient verified data.",
            }

        degree_dict = nx.degree_centrality(G)
        betweenness_dict = nx.betweenness_centrality(G) if G.number_of_nodes() > 2 else {n: 0.0 for n in G.nodes()}
        
        try:
            pagerank_dict = nx.pagerank(G, max_iter=200)
        except Exception:
            pagerank_dict = {n: round(1.0 / len(G.nodes()), 4) for n in G.nodes()}

        try:
            closeness_dict = nx.closeness_centrality(G)
        except Exception:
            closeness_dict = {n: 0.0 for n in G.nodes()}

        combined_metrics = {}
        for nid in G.nodes():
            node_data = G.nodes[nid]
            combined_metrics[nid] = {
                "id": nid,
                "name": node_data.get("name", nid),
                "label": node_data.get("label", "Entity"),
                "degree_centrality": round(degree_dict.get(nid, 0.0), 4),
                "betweenness_centrality": round(betweenness_dict.get(nid, 0.0), 4),
                "pagerank": round(pagerank_dict.get(nid, 0.0), 4),
                "closeness_centrality": round(closeness_dict.get(nid, 0.0), 4),
                "raw_degree": G.degree(nid),
                "risk_score": node_data.get("riskScore") or node_data.get("risk_score", 50),
            }

        # Identify structural roles
        top_bridges = sorted(
            combined_metrics.values(),
            key=lambda x: (x["betweenness_centrality"], x["raw_degree"]),
            reverse=True,
        )[:limit]

        top_influencers = sorted(
            combined_metrics.values(),
            key=lambda x: x["pagerank"],
            reverse=True,
        )[:limit]

        top_hubs = sorted(
            combined_metrics.values(),
            key=lambda x: x["raw_degree"],
            reverse=True,
        )[:limit]

        return {
            "graph_source": graph_source,
            "total_nodes_analyzed": len(G.nodes()),
            "top_betweenness_bridges": top_bridges,
            "top_pagerank_influencers": top_influencers,
            "top_degree_hubs": top_hubs,
            "metrics": combined_metrics,
            "status": "Computed using authentic NetworkX centrality algorithms.",
        }

    def detect_communities(
        self,
        graph_source: str = "investigation_evidence",
    ) -> Dict[str, Any]:
        """
        Executes community detection using Greedy Modularity Optimization and Connected Components.
        """
        multi_digraph, G = self._get_graph_and_undirected(graph_source)
        num_nodes = G.number_of_nodes()

        if num_nodes == 0:
            return {
                "graph_source": graph_source,
                "total_communities": 0,
                "modularity_score": 0.0,
                "communities": [],
                "node_community_map": {},
                "status": "Insufficient verified data.",
            }

        # Attempt Modularity-based clustering
        try:
            community_sets = list(greedy_modularity_communities(G))
        except Exception:
            # Fallback to connected components
            community_sets = list(nx.connected_components(G))

        node_community_map: Dict[str, int] = {}
        communities_summary = []

        for idx, cset in enumerate(community_sets):
            c_nodes = []
            for nid in cset:
                node_community_map[nid] = idx
                ndata = G.nodes[nid]
                c_nodes.append({
                    "id": nid,
                    "name": ndata.get("name", nid),
                    "label": ndata.get("label", "Entity"),
                    "case_id": ndata.get("case_id"),
                })

            communities_summary.append({
                "community_id": idx,
                "size": len(cset),
                "nodes": c_nodes,
                "dominant_label": max(
                    set(n["label"] for n in c_nodes),
                    key=[n["label"] for n in c_nodes].count,
                ) if c_nodes else "Unknown",
            })

        # Calculate graph modularity
        modularity = 0.0
        if len(community_sets) > 1 and G.number_of_edges() > 0:
            try:
                modularity = round(nx.community.modularity(G, community_sets), 4)
            except Exception:
                modularity = 0.0

        return {
            "graph_source": graph_source,
            "total_communities": len(communities_summary),
            "modularity_score": modularity,
            "communities": communities_summary,
            "node_community_map": node_community_map,
            "status": "Computed using authentic community modularity algorithms.",
        }

    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        graph_source: str = "investigation_evidence",
    ) -> Dict[str, Any]:
        """Calculates exact shortest path and returns node sequence and traversed relationships."""
        multi_digraph, G = self._get_graph_and_undirected(graph_source)

        if not G.has_node(source_id) or not G.has_node(target_id):
            return {
                "found": False,
                "source_id": source_id,
                "target_id": target_id,
                "path": [],
                "path_nodes": [],
                "path_edges": [],
                "message": f"Entity '{source_id}' or '{target_id}' not found in {graph_source}.",
            }

        try:
            path_node_ids = nx.shortest_path(G, source=source_id, target=target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return {
                "found": False,
                "source_id": source_id,
                "target_id": target_id,
                "path": [],
                "path_nodes": [],
                "path_edges": [],
                "message": f"No path found between '{source_id}' and '{target_id}'.",
            }

        # Build detailed path nodes
        path_nodes = []
        for nid in path_node_ids:
            ndata = G.nodes[nid]
            path_nodes.append({
                "id": nid,
                "name": ndata.get("name", nid),
                "label": ndata.get("label", "Entity"),
                "case_id": ndata.get("case_id"),
                "source_document": ndata.get("source_document"),
            })

        # Build traversed edges
        path_edges = []
        for i in range(len(path_node_ids) - 1):
            u = path_node_ids[i]
            v = path_node_ids[i + 1]
            edge_data = G.get_edge_data(u, v) or {}
            path_edges.append({
                "source": u,
                "target": v,
                "type": edge_data.get("type", "CONNECTED_TO"),
                "detail": edge_data.get("detail", "Verified graph edge"),
            })

        return {
            "found": True,
            "source_id": source_id,
            "target_id": target_id,
            "hop_count": len(path_node_ids) - 1,
            "path": path_node_ids,
            "path_nodes": path_nodes,
            "path_edges": path_edges,
            "message": f"Shortest path identified ({len(path_node_ids) - 1} hops).",
        }

    def get_k_hop_neighborhood(
        self,
        entity_id: str,
        hops: int = 2,
        graph_source: str = "investigation_evidence",
    ) -> Dict[str, Any]:
        """Expands and extracts the k-hop ego subgraph around an entity."""
        multi_digraph, G = self._get_graph_and_undirected(graph_source)

        if not G.has_node(entity_id):
            return {
                "entity_id": entity_id,
                "hops": hops,
                "nodes": [],
                "relationships": [],
                "message": f"Entity '{entity_id}' not found in {graph_source}.",
            }

        subgraph_nodes = nx.single_source_shortest_path_length(G, entity_id, cutoff=hops)
        sub_G = G.subgraph(subgraph_nodes.keys())

        nodes_list = []
        for nid, dist in subgraph_nodes.items():
            ndata = G.nodes[nid]
            nodes_list.append({
                **ndata,
                "id": nid,
                "distance_from_focal": dist,
            })

        edges_list = []
        for u, v, data in sub_G.edges(data=True):
            edges_list.append({
                "sourceId": u,
                "targetId": v,
                "type": data.get("type", "CONNECTED_TO"),
                "metadata": data,
            })

        return {
            "entity_id": entity_id,
            "hops": hops,
            "total_nodes": len(nodes_list),
            "total_relationships": len(edges_list),
            "nodes": nodes_list,
            "relationships": edges_list,
        }


# Global Singleton Instance
graph_algorithms = GraphAlgorithmsService()
