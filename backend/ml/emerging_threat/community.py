"""Community restructuring, syndicate merging, and fragmentation analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from .config import CommunityEvolutionConfig
from .snapshots import GraphSnapshot


@dataclass
class CommunityEvolutionMetrics:
    """Quantitative evolution of modular community structures across snapshots."""
    prior_snapshot_id: str
    curr_snapshot_id: str
    prior_communities_count: int = 0
    curr_communities_count: int = 0
    new_communities_formed: int = 0
    communities_merged: int = 0
    communities_fragmented: int = 0
    membership_churn: float = 0.0
    community_evolution_score: float = 0.0   # Bounded [0, 1] evolution urgency
    narrative: str = ""


class CommunityEvolutionDetector:
    """Detects cluster emergence, mergers, splits, and membership reorganization."""

    def __init__(self, config: Optional[CommunityEvolutionConfig] = None):
        self.config = config or CommunityEvolutionConfig()

    def _extract_communities(self, snapshot: GraphSnapshot) -> List[Set[str]]:
        """Extracts modular communities using NetworkX algorithms."""
        G = nx.Graph()
        for nid in snapshot.nodes:
            G.add_node(nid)
        for e in snapshot.edges:
            G.add_edge(e.source_id, e.target_id)

        if G.number_of_nodes() < 2 or G.number_of_edges() == 0:
            return [{n} for n in G.nodes()]

        try:
            communities = list(greedy_modularity_communities(G))
            return [set(c) for c in communities]
        except Exception:
            return [set(c) for c in nx.connected_components(G)]

    def compare_communities(
        self,
        prior: GraphSnapshot,
        curr: GraphSnapshot,
    ) -> CommunityEvolutionMetrics:
        """Calculates exact community evolution metrics across two snapshots."""
        p_comms = self._extract_communities(prior)
        c_comms = self._extract_communities(curr)

        if not p_comms or not c_comms:
            return CommunityEvolutionMetrics(
                prior_snapshot_id=prior.snapshot_id,
                curr_snapshot_id=curr.snapshot_id,
                narrative="Insufficient nodes to evaluate community evolution.",
            )

        # Compute pairwise Jaccard similarities: J(P_i, C_j) = |P_i & C_j| / |P_i | C_j|
        new_formed = 0
        merged = 0
        fragmented = 0

        # Check for new communities in curr that don't match any in prior
        for c in c_comms:
            max_sim = max((len(c & p) / max(1, len(c | p)) for p in p_comms), default=0.0)
            if max_sim < 0.20 and len(c) >= 3:
                new_formed += 1

        # Check for mergers (multiple prior communities having substantial overlap with one current community)
        for c in c_comms:
            matching_p = [p for p in p_comms if len(c & p) >= 2 and (len(c & p) / len(p)) >= 0.40]
            if len(matching_p) >= 2:
                merged += 1

        # Check for fragmentation (one prior community splitting into multiple current communities)
        for p in p_comms:
            matching_c = [c for c in c_comms if len(p & c) >= 2 and (len(p & c) / len(c)) >= 0.40]
            if len(matching_c) >= 2:
                fragmented += 1

        # Community evolution score in [0, 1]
        raw_score = (
            0.40 * min(1.0, new_formed / 2.0)
            + 0.35 * min(1.0, merged / 2.0)
            + 0.25 * min(1.0, fragmented / 2.0)
        )
        score = round(max(0.0, min(1.0, raw_score)), 4)

        narratives = []
        if new_formed > 0:
            narratives.append(f"{new_formed} new cohesive analytical cluster(s) emerged.")
        if merged > 0:
            narratives.append(f"{merged} community merger event(s) detected.")
        if fragmented > 0:
            narratives.append(f"{fragmented} community fragmentation event(s) observed.")
        if not narratives:
            narratives.append("Community partitions remained stable across snapshots.")

        return CommunityEvolutionMetrics(
            prior_snapshot_id=prior.snapshot_id,
            curr_snapshot_id=curr.snapshot_id,
            prior_communities_count=len(p_comms),
            curr_communities_count=len(c_comms),
            new_communities_formed=new_formed,
            communities_merged=merged,
            communities_fragmented=fragmented,
            community_evolution_score=score,
            narrative=" ".join(narratives),
        )
