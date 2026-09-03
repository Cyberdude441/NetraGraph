"""Emerging subgraph pattern identification and candidate extraction."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from .snapshots import GraphSnapshot


@dataclass
class EmergingSubgraphCandidate:
    """Candidate network structure exhibiting converging early-warning indicators."""
    subgraph_id: str = field(default_factory=lambda: f"SUB-{uuid.uuid4().hex[:10].upper()}")
    node_ids: List[str] = field(default_factory=list)
    edge_count: int = 0
    density: float = 0.0
    average_node_risk: float = 0.0
    convergence_score: float = 0.0           # Bounded [0, 1] multi-indicator intensity
    emerging_indicators: List[str] = field(default_factory=list)
    label: str = "emerging high-risk analytical subgraph"
    narrative: str = ""


class EmergingSubgraphDetector:
    """Extracts candidate network subgraphs showing rapid structural growth and elevated risk."""

    def extract_candidate_subgraphs(
        self,
        snapshot: GraphSnapshot,
        high_risk_node_threshold: float = 0.60,
    ) -> List[EmergingSubgraphCandidate]:
        """Identifies connected components containing clusters of elevated risk or high connectivity."""
        G = nx.Graph()
        for nid, node in snapshot.nodes.items():
            G.add_node(nid, risk=node.risk_score or 0.0)
        for e in snapshot.edges:
            G.add_edge(e.source_id, e.target_id, weight=e.weight)

        candidates: List[EmergingSubgraphCandidate] = []
        if G.number_of_nodes() < 2:
            return candidates

        # Evaluate connected components
        for comp in nx.connected_components(G):
            if len(comp) < 2:
                continue

            sub = G.subgraph(comp)
            node_risks = [sub.nodes[n].get("risk", 0.0) for n in comp]
            avg_risk = sum(node_risks) / len(node_risks) if node_risks else 0.0
            density = nx.density(sub)

            indicators = []
            if avg_risk >= high_risk_node_threshold:
                indicators.append("HIGH_AVERAGE_NODE_RISK")
            if len(comp) >= 5:
                indicators.append("RAPID_NODAL_EXPANSION")
            if density >= 0.40:
                indicators.append("DENSE_RELATIONSHIP_CLUSTERING")

            if len(indicators) >= 2 or avg_risk >= 0.70:
                convergence = round(
                    max(0.0, min(1.0, 0.50 * avg_risk + 0.30 * density + 0.20 * min(1.0, len(comp) / 10.0))),
                    4,
                )
                candidates.append(
                    EmergingSubgraphCandidate(
                        node_ids=sorted(list(comp)),
                        edge_count=sub.number_of_edges(),
                        density=round(density, 4),
                        average_node_risk=round(avg_risk, 4),
                        convergence_score=convergence,
                        emerging_indicators=indicators,
                        label="emerging high-risk analytical subgraph",
                        narrative=(
                            f"Identified candidate emerging subgraph of {len(comp)} nodes and {sub.number_of_edges()} edges "
                            f"(density {density:.2f}, avg risk {avg_risk:.2f}) with indicators: {', '.join(indicators)}. "
                            "Network pattern requiring human investigation."
                        ),
                    )
                )

        # Sort by convergence score descending
        return sorted(candidates, key=lambda c: c.convergence_score, reverse=True)
