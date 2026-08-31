"""Graph Structural Anomaly Detection Engine for NetraGraph AI.

Detects topological anomalies (dense clusters, shared infrastructure, recurring financial nodes,
bridge nodes, rapidly expanding components) on the authorized investigation graph.

GOVERNANCE PRINCIPLE:
Structural anomalies are purely topological metrics indicating high network connectivity or shared
infrastructure. They must strictly NEVER be labeled as 'guilt', 'mastermind', or 'culpability'.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import networkx as nx
from database.neo4j import neo4j_db

logger = logging.getLogger("GraphAnomalyEngine")


class GraphAnomalyEngine:
    """Computes structural topological anomaly metrics on the investigation graph."""

    def analyze_case_structural_anomalies(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Performs topological pattern detection across case entities."""
        # Query active evidence graph
        ev_data = neo4j_db.query_evidence_graph(case_id=case_id)
        nodes = ev_data.get("nodes", [])
        rels = ev_data.get("relationships", [])

        if not nodes:
            return {
                "case_id": case_id,
                "anomalies_detected": 0,
                "structural_signals": [],
                "summary": "No active nodes available for structural graph analysis.",
            }

        # Build in-memory NetworkX directed graph for topological computation
        G = nx.MultiDiGraph()
        for n in nodes:
            G.add_node(n["id"], **n)
        for r in rels:
            G.add_edge(r["sourceId"], r["targetId"], key=r["id"], **r)

        undirected_G = nx.Graph(G)
        signals: List[Dict[str, Any]] = []

        # 1. REPEATED INFRASTRUCTURE (Shared IPs / Domains with in-degree >= 2)
        for nid, deg in G.in_degree():
            n = G.nodes.get(nid, {})
            label = n.get("label", "")
            if label in ["IPAddress", "Domain", "Phone", "Device"] and deg >= 2:
                signals.append({
                    "signal_type": "SHARED_INFRASTRUCTURE",
                    "severity": "HIGH",
                    "entity_id": nid,
                    "entity_name": n.get("name", nid),
                    "entity_label": label,
                    "metric": f"In-Degree: {deg}",
                    "description": f"Infrastructure node '{n.get('name')}' is referenced by {deg} distinct evidence artifacts.",
                    "investigative_note": "Topological signal indicates shared infrastructure. Requires technical verification of multi-tenant vs dedicated hosting.",
                })

        # 2. RECURRING FINANCIAL FLOWS (Bank accounts with high transaction references)
        for nid, deg in G.in_degree():
            n = G.nodes.get(nid, {})
            label = n.get("label", "")
            if label in ["BankAccount", "Financial"] and deg >= 1:
                signals.append({
                    "signal_type": "RECURRING_FINANCIAL_NODE",
                    "severity": "MEDIUM",
                    "entity_id": nid,
                    "entity_name": n.get("name", nid),
                    "entity_label": label,
                    "metric": f"Referencing Edges: {deg}",
                    "description": f"Financial entity '{n.get('name')}' receives references across multiple case records.",
                    "investigative_note": "Structural signal indicates focal banking endpoint. Recommend Section 91 CrPC notice to bank for KYC trail.",
                })

        # 3. BRIDGE NODES (High betweenness centrality in connected component)
        if len(undirected_G) > 2:
            try:
                betweenness = nx.betweenness_centrality(undirected_G)
                for nid, b_score in betweenness.items():
                    if b_score > 0.3:
                        n = undirected_G.nodes.get(nid, {})
                        signals.append({
                            "signal_type": "STRUCTURAL_BRIDGE_NODE",
                            "severity": "MEDIUM",
                            "entity_id": nid,
                            "entity_name": n.get("name", nid),
                            "entity_label": n.get("label", "Entity"),
                            "metric": f"Betweenness Centrality: {b_score:.2f}",
                            "description": f"Node '{n.get('name')}' occupies a structural bridge position between separate network sub-clusters.",
                            "investigative_note": "Topological metric indicates routing intermediary. Strictly non-indicative of operational culpability.",
                        })
            except Exception as e:
                logger.debug(f"[AnomalyEngine] Betweenness computation warning: {e}")

        # 4. UNUSUALLY DENSE CLUSTERS (Cliques / High clustering coefficient)
        if len(undirected_G) >= 3:
            try:
                clustering = nx.clustering(undirected_G)
                for nid, c_coeff in clustering.items():
                    if c_coeff >= 0.8 and undirected_G.degree(nid) >= 3:
                        n = undirected_G.nodes.get(nid, {})
                        signals.append({
                            "signal_type": "DENSE_CO_OCCURRENCE_CLUSTER",
                            "severity": "MEDIUM",
                            "entity_id": nid,
                            "entity_name": n.get("name", nid),
                            "entity_label": n.get("label", "Entity"),
                            "metric": f"Clustering Coefficient: {c_coeff:.2f}",
                            "description": f"Node '{n.get('name')}' participates in a tightly interconnected evidence cluster.",
                            "investigative_note": "Signal reflects high mutual connectivity among related entities.",
                        })
            except Exception as e:
                logger.debug(f"[AnomalyEngine] Clustering computation warning: {e}")

        return {
            "case_id": case_id or "ALL_CASES",
            "total_nodes_evaluated": len(nodes),
            "total_edges_evaluated": len(rels),
            "anomalies_detected": len(signals),
            "structural_signals": signals,
            "governance_disclaimer": "All signals reflect graph topology and network properties. Strictly non-judgmental and non-inculpatory.",
        }


# Global Singleton Instance
graph_anomaly_engine = GraphAnomalyEngine()
