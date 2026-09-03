"""Network topology evolution metrics and structural velocity detectors."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from .config import TopologyEvolutionConfig
from .snapshots import GraphSnapshot, TemporalSnapshotSequence


@dataclass
class TopologyMetrics:
    """Quantitative topology differences observed across two graph snapshots."""
    snapshot_prior_id: str
    snapshot_curr_id: str
    delta_seconds: float

    prior_nodes: int = 0
    curr_nodes: int = 0
    node_growth_rate: float = 0.0
    nodes_added_count: int = 0
    nodes_removed_count: int = 0
    node_churn: float = 0.0

    prior_edges: int = 0
    curr_edges: int = 0
    edge_growth_rate: float = 0.0
    edges_added_count: int = 0
    edges_removed_count: int = 0
    edge_churn: float = 0.0

    density_prior: float = 0.0
    density_curr: float = 0.0
    density_delta: float = 0.0

    components_prior: int = 0
    components_curr: int = 0
    components_delta: int = 0

    topology_velocity_score: float = 0.0   # Normalized [0, 1] composite velocity
    anomalous_expansion_detected: bool = False
    narrative: str = ""


class TopologyEvolutionDetector:
    """Computes deterministic structural changes across temporal snapshots."""

    def __init__(self, config: Optional[TopologyEvolutionConfig] = None):
        self.config = config or TopologyEvolutionConfig()

    def _build_nx_graph(self, snapshot: GraphSnapshot) -> nx.Graph:
        """Constructs an undirected simple NetworkX graph for topology metrics."""
        G = nx.Graph()
        for nid, n in snapshot.nodes.items():
            G.add_node(nid, **n.attributes)
        for e in snapshot.edges:
            G.add_edge(e.source_id, e.target_id, weight=e.weight)
        return G

    def compare_snapshots(
        self,
        prior: GraphSnapshot,
        curr: GraphSnapshot,
        delta_seconds: float,
    ) -> TopologyMetrics:
        """Calculates exact differences between prior and current snapshots."""
        G_prior = self._build_nx_graph(prior)
        G_curr = self._build_nx_graph(curr)

        n_p, n_c = len(G_prior), len(G_curr)
        e_p, e_c = G_prior.number_of_edges(), G_curr.number_of_edges()

        # Growth rates
        node_growth = float(n_c - n_p) / max(1, n_p)
        edge_growth = float(e_c - e_p) / max(1, e_p)

        # Churn calculations
        p_nodes, c_nodes = set(G_prior.nodes()), set(G_curr.nodes())
        added_nodes = len(c_nodes - p_nodes)
        removed_nodes = len(p_nodes - c_nodes)
        total_unique_nodes = max(1, len(p_nodes | c_nodes))
        node_churn = (added_nodes + removed_nodes) / total_unique_nodes

        p_edges = {tuple(sorted((u, v))) for u, v in G_prior.edges()}
        c_edges = {tuple(sorted((u, v))) for u, v in G_curr.edges()}
        added_edges = len(c_edges - p_edges)
        removed_edges = len(p_edges - c_edges)
        total_unique_edges = max(1, len(p_edges | c_edges))
        edge_churn = (added_edges + removed_edges) / total_unique_edges

        # Densities
        den_p = nx.density(G_prior) if n_p > 1 else 0.0
        den_c = nx.density(G_curr) if n_c > 1 else 0.0
        density_delta = den_c - den_p

        # Connected components
        comp_p = nx.number_connected_components(G_prior) if n_p > 0 else 0
        comp_c = nx.number_connected_components(G_curr) if n_c > 0 else 0

        # Composite topology velocity score in [0, 1]
        velocity = (
            0.30 * min(1.0, max(0.0, node_growth))
            + 0.30 * min(1.0, max(0.0, edge_growth))
            + 0.20 * min(1.0, node_churn)
            + 0.20 * min(1.0, edge_churn)
        )
        velocity = round(max(0.0, min(1.0, velocity)), 4)

        anomalous = (
            node_growth >= self.config.node_growth_rate_threshold
            or edge_growth >= self.config.edge_growth_rate_threshold
            or node_churn >= self.config.node_churn_threshold
            or edge_churn >= self.config.edge_churn_threshold
        )

        narrative_parts = []
        if node_growth >= self.config.node_growth_rate_threshold:
            narrative_parts.append(f"Node count expanded by {node_growth * 100:.1f}%.")
        if edge_growth >= self.config.edge_growth_rate_threshold:
            narrative_parts.append(f"Edge count expanded by {edge_growth * 100:.1f}%.")
        if edge_churn >= self.config.edge_churn_threshold:
            narrative_parts.append(f"High edge churn observed ({edge_churn * 100:.1f}%).")
        if not narrative_parts:
            narrative_parts.append("Network topology remained structurally stable.")

        return TopologyMetrics(
            snapshot_prior_id=prior.snapshot_id,
            snapshot_curr_id=curr.snapshot_id,
            delta_seconds=delta_seconds,
            prior_nodes=n_p,
            curr_nodes=n_c,
            node_growth_rate=round(node_growth, 4),
            nodes_added_count=added_nodes,
            nodes_removed_count=removed_nodes,
            node_churn=round(node_churn, 4),
            prior_edges=e_p,
            curr_edges=e_c,
            edge_growth_rate=round(edge_growth, 4),
            edges_added_count=added_edges,
            edges_removed_count=removed_edges,
            edge_churn=round(edge_churn, 4),
            density_prior=round(den_p, 4),
            density_curr=round(den_c, 4),
            density_delta=round(density_delta, 4),
            components_prior=comp_p,
            components_curr=comp_c,
            components_delta=comp_c - comp_p,
            topology_velocity_score=velocity,
            anomalous_expansion_detected=anomalous,
            narrative=" ".join(narrative_parts),
        )

    def analyze_sequence(self, sequence: TemporalSnapshotSequence) -> List[TopologyMetrics]:
        """Analyzes all consecutive snapshot transitions across a temporal sequence."""
        results = []
        for prior, curr, dt in sequence.get_pairwise_deltas():
            res = self.compare_snapshots(prior, curr, dt)
            results.append(res)
        return results
