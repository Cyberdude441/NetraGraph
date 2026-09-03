"""Centrality shift tracking and bridge node emergence analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from .config import CentralityEvolutionConfig
from .snapshots import GraphSnapshot


@dataclass
class CentralityShift:
    """Individual entity centrality dynamics between two snapshots."""
    entity_id: str
    prior_degree: float = 0.0
    curr_degree: float = 0.0
    degree_shift: float = 0.0

    prior_raw_degree: int = 0
    curr_raw_degree: int = 0
    raw_degree_shift: int = 0

    prior_betweenness: float = 0.0
    curr_betweenness: float = 0.0
    betweenness_shift: float = 0.0

    prior_pagerank: float = 0.0
    curr_pagerank: float = 0.0
    pagerank_shift: float = 0.0

    is_emerging_bridge: bool = False
    centrality_velocity_score: float = 0.0  # Bounded [0, 1]
    narrative: str = ""


class CentralityEvolutionDetector:
    """Computes dynamic shifts in node centrality and identifies newly emerged bridge brokers."""

    def __init__(self, config: Optional[CentralityEvolutionConfig] = None):
        self.config = config or CentralityEvolutionConfig()

    def _calculate_metrics(self, snapshot: GraphSnapshot) -> Dict[str, Dict[str, float]]:
        """Calculates degree, betweenness, and PageRank for all nodes in snapshot."""
        G = nx.Graph()
        for nid in snapshot.nodes:
            G.add_node(nid)
        for e in snapshot.edges:
            G.add_edge(e.source_id, e.target_id)

        n = G.number_of_nodes()
        if n == 0:
            return {}

        deg = nx.degree_centrality(G)
        bet = nx.betweenness_centrality(G) if n > 2 else {nid: 0.0 for nid in G.nodes()}
        try:
            pr = nx.pagerank(G, max_iter=200)
        except Exception:
            pr = {nid: round(1.0 / n, 4) for nid in G.nodes()}

        results = {}
        for nid in G.nodes():
            results[nid] = {
                "degree": deg.get(nid, 0.0),
                "betweenness": bet.get(nid, 0.0),
                "pagerank": pr.get(nid, 0.0),
                "raw_degree": int(G.degree(nid)),
            }
        return results

    def compare_centralities(
        self,
        prior: GraphSnapshot,
        curr: GraphSnapshot,
    ) -> Dict[str, CentralityShift]:
        """Calculates centrality shifts for all shared or newly active entities."""
        p_metrics = self._calculate_metrics(prior)
        c_metrics = self._calculate_metrics(curr)

        all_nodes = set(p_metrics.keys()) | set(c_metrics.keys())
        shifts: Dict[str, CentralityShift] = {}

        for nid in all_nodes:
            p = p_metrics.get(nid, {"degree": 0.0, "betweenness": 0.0, "pagerank": 0.0, "raw_degree": 0})
            c = c_metrics.get(nid, {"degree": 0.0, "betweenness": 0.0, "pagerank": 0.0, "raw_degree": 0})

            d_shift = c["degree"] - p["degree"]
            b_shift = c["betweenness"] - p["betweenness"]
            pr_shift = c["pagerank"] - p["pagerank"]
            p_raw = int(p.get("raw_degree", 0))
            c_raw = int(c.get("raw_degree", 0))
            raw_d_shift = c_raw - p_raw

            is_bridge = bool(
                c["betweenness"] >= self.config.bridge_betweenness_threshold
                and b_shift >= self.config.betweenness_shift_threshold
            )

            # Combined velocity score in [0, 1]
            raw_vel = (
                0.35 * min(1.0, max(0.0, d_shift * 2.0))
                + 0.45 * min(1.0, max(0.0, b_shift * 2.5))
                + 0.20 * min(1.0, max(0.0, pr_shift * 3.0))
            )
            vel_score = round(max(0.0, min(1.0, raw_vel)), 4)

            narratives = []
            if b_shift >= self.config.betweenness_shift_threshold:
                narratives.append(f"Betweenness increased by {b_shift:+.3f} (brokerage velocity).")
            if d_shift >= self.config.degree_centrality_shift_threshold:
                narratives.append(f"Degree centrality increased by {d_shift:+.3f}.")
            if is_bridge:
                narratives.append("Entity emerged as a structural bridge connecting disjoint network components.")
            if not narratives:
                narratives.append("Centrality indicators remained within baseline thresholds.")

            shifts[nid] = CentralityShift(
                entity_id=nid,
                prior_degree=round(p["degree"], 4),
                curr_degree=round(c["degree"], 4),
                degree_shift=round(d_shift, 4),
                prior_raw_degree=p_raw,
                curr_raw_degree=c_raw,
                raw_degree_shift=raw_d_shift,
                prior_betweenness=round(p["betweenness"], 4),
                curr_betweenness=round(c["betweenness"], 4),
                betweenness_shift=round(b_shift, 4),
                prior_pagerank=round(p["pagerank"], 4),
                curr_pagerank=round(c["pagerank"], 4),
                pagerank_shift=round(pr_shift, 4),
                is_emerging_bridge=is_bridge,
                centrality_velocity_score=vel_score,
                narrative=" ".join(narratives),
            )

        return shifts
