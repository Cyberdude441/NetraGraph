"""Graph structural & topological distribution drift detector with metric-specific complexity bounds.

METRIC-SPECIFIC COMPLEXITY CHARACTERISTICS:
- Node / Edge Count Delta: O(1)
- Density Delta: O(1) given |V|, |E|
- Node Type Categorical Distribution (JSD): O(|V|)
- Relationship Type Categorical Distribution (JSD): O(|E|)
- Degree Distribution Shift (Wasserstein): O(|V| + |E| + |V| log |V|)
- Connected Components Delta: O(|V| + |E|) via linear BFS/DFS
- Optional Bounded PageRank: O(I * (|V| + |E|)) with power iterations bounded to I <= 30

RESTRICTED / EXCLUDED OPERATIONS:
- All-Pairs Shortest Paths (O(|V|^3)) is STRICTLY FORBIDDEN.
- Unbounded Betweenness Centrality (O(|V| * |E|)) is EXCLUDED from standard evaluation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
import numpy as np

from .config import (
    DEFAULT_ALGORITHM_VERSION,
    GENERAL_DRIFT_DISCLAIMER,
    DriftDomain,
    DriftMetricType,
    DriftSeverity,
    DriftThresholdPolicy,
    ObservationStatus,
)
from .models import (
    BaselineWindow,
    ComparisonWindow,
    DriftDimensionDelta,
    DriftExplanation,
    DriftObservationRecord,
    ReferenceBaseline,
)
from .provenance import compute_analytical_observation_id, compute_data_digest, generate_run_id
from .statistics import compute_jsd, compute_wasserstein


class GraphDriftDetector:
    """Detects structural and topological distribution divergence between reference and comparison graphs."""

    def __init__(self, policy: Optional[DriftThresholdPolicy] = None):
        self.policy = policy or DriftThresholdPolicy()

    def evaluate_graph_drift(
        self,
        reference_baseline: ReferenceBaseline,
        comparison_graph: nx.Graph | nx.MultiDiGraph,
        target_name: str = "InvestigationGraph",
        graph_layer: str = "EVIDENCE",
        comparison_window_start: Optional[str] = None,
        comparison_window_end: Optional[str] = None,
    ) -> DriftObservationRecord:
        """
        Evaluates graph structural and topological drift against a frozen ReferenceBaseline.
        Enforces metric-specific complexity bounds and sample-size thresholds.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        num_nodes = comparison_graph.number_of_nodes()
        num_edges = comparison_graph.number_of_edges()

        # Build comparison summary
        cmp_node_types: Dict[str, int] = {}
        for _, data in comparison_graph.nodes(data=True):
            ntype = str(data.get("type", data.get("entity_type", "Unknown")))
            cmp_node_types[ntype] = cmp_node_types.get(ntype, 0) + 1

        cmp_rel_types: Dict[str, int] = {}
        for _, _, data in comparison_graph.edges(data=True):
            rtype = str(data.get("rel_type", data.get("type", "ASSOCIATED_WITH")))
            cmp_rel_types[rtype] = cmp_rel_types.get(rtype, 0) + 1

        cmp_degrees = [d for _, d in comparison_graph.degree()] if num_nodes > 0 else []

        # Undirected view for connected components and density
        undirected = comparison_graph.to_undirected() if comparison_graph.is_directed() else comparison_graph
        cmp_density = nx.density(undirected) if num_nodes > 1 else 0.0
        cmp_components = nx.number_connected_components(undirected) if num_nodes > 0 else 0

        cmp_digest_data = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "node_types": cmp_node_types,
            "rel_types": cmp_rel_types,
            "density": round(cmp_density, 6),
            "components": cmp_components,
        }
        cmp_digest = compute_data_digest(cmp_digest_data)

        cmp_window = ComparisonWindow(
            start_timestamp=comparison_window_start or now_iso,
            end_timestamp=comparison_window_end or now_iso,
            sample_count=num_nodes,
            data_digest=cmp_digest,
        )

        obs_id = compute_analytical_observation_id(
            domain=DriftDomain.GRAPH.value,
            target=target_name,
            reference_baseline_id=reference_baseline.baseline_id,
            comparison_data_digest=cmp_digest,
            metric_name=DriftMetricType.JSD.value,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
            threshold_policy_version=self.policy.policy_version,
        )

        # 1. Check minimum sample size policy
        if num_nodes < self.policy.min_sample_size:
            explanation = DriftExplanation(
                summary=(
                    f"Graph sample size (N={num_nodes} nodes) is below the policy minimum "
                    f"threshold (N_min={self.policy.min_sample_size}). Topological drift is provisional."
                ),
                dimension_deltas=[
                    DriftDimensionDelta(
                        dimension_name="node_count",
                        reference_value=reference_baseline.window.sample_count,
                        comparison_value=num_nodes,
                        delta_absolute=num_nodes - reference_baseline.window.sample_count,
                    )
                ],
                recommended_actions=[
                    "Await additional entity ingestion before establishing definitive topological conclusions.",
                    "Expand investigation multi-hop neighborhood depth."
                ],
                limitations=["Insufficient sample size for statistically valid graph divergence."],
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.GRAPH,
                target_name=target_name,
                parent_target=graph_layer,
                metric_name=DriftMetricType.JSD,
                metric_value=None,
                reference_baseline_id=reference_baseline.baseline_id,
                reference_window=reference_baseline.window,
                comparison_window=cmp_window,
                severity=DriftSeverity.INSUFFICIENT_DATA,
                status=ObservationStatus.INSUFFICIENT_DATA,
                is_statistically_valid=False,
                threshold_policy_version=self.policy.policy_version,
                threshold_applied=self.policy.jsd_watch,
                algorithm_version=DEFAULT_ALGORITHM_VERSION,
                explanation=explanation,
                computed_at=now_iso,
                run_id=generate_run_id(),
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )

        # 2. Extract baseline distributions
        ref_dist = reference_baseline.feature_distributions
        ref_node_types = ref_dist.get("node_types", {})
        ref_rel_types = ref_dist.get("relationship_types", {})
        ref_density = float(ref_dist.get("density", 0.0))
        ref_components = int(ref_dist.get("components", 1))
        ref_degrees = ref_dist.get("degrees", [1.0] * reference_baseline.window.sample_count)

        # 3. Compute metrics with bounded complexity
        node_type_jsd = compute_jsd(ref_node_types, cmp_node_types)
        rel_type_jsd = compute_jsd(ref_rel_types, cmp_rel_types)
        degree_wasserstein = compute_wasserstein(ref_degrees, cmp_degrees)

        # Primary metric is composite JSD of topology distributions
        primary_metric = round(float(0.5 * (node_type_jsd + rel_type_jsd)), 7)

        # Classify severity using versioned policy defaults
        if primary_metric >= self.policy.jsd_critical:
            severity = DriftSeverity.CRITICAL
        elif primary_metric >= self.policy.jsd_elevated:
            severity = DriftSeverity.ELEVATED
        elif primary_metric >= self.policy.jsd_watch:
            severity = DriftSeverity.WATCH
        else:
            severity = DriftSeverity.NORMAL

        # Build non-causal dimensional deltas
        deltas: List[DriftDimensionDelta] = [
            DriftDimensionDelta(
                dimension_name="node_type_distribution_jsd",
                reference_value=ref_node_types,
                comparison_value=cmp_node_types,
                delta_absolute=node_type_jsd,
                interpretation=f"Node type categorical divergence is {node_type_jsd:.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="relationship_type_distribution_jsd",
                reference_value=ref_rel_types,
                comparison_value=cmp_rel_types,
                delta_absolute=rel_type_jsd,
                interpretation=f"Relationship type categorical divergence is {rel_type_jsd:.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="degree_distribution_wasserstein",
                reference_value=round(float(np.mean(ref_degrees)), 2) if len(ref_degrees) > 0 else 0,
                comparison_value=round(float(np.mean(cmp_degrees)), 2) if len(cmp_degrees) > 0 else 0,
                delta_absolute=degree_wasserstein,
                interpretation=f"Earth Mover's Distance on node degree is {degree_wasserstein:.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="density_delta",
                reference_value=ref_density,
                comparison_value=round(cmp_density, 6),
                delta_absolute=round(cmp_density - ref_density, 6),
            ),
            DriftDimensionDelta(
                dimension_name="component_count_delta",
                reference_value=ref_components,
                comparison_value=cmp_components,
                delta_absolute=cmp_components - ref_components,
            ),
        ]

        summary_text = (
            f"Graph structural divergence is {primary_metric:.4f} ({severity.value}) relative to baseline "
            f"'{reference_baseline.baseline_id}'. Node count changed by {num_nodes - reference_baseline.window.sample_count:+d} "
            f"and density shifted by {cmp_density - ref_density:+.4f}."
        )

        recommended_actions = []
        if severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL):
            recommended_actions.append("Inspect recent batch ingestion feeds for structural shifts or unexpected entity types.")
            recommended_actions.append("Verify link extraction connectors for relationship vocabulary consistency.")

        explanation = DriftExplanation(
            summary=summary_text,
            dimension_deltas=deltas,
            recommended_actions=recommended_actions,
            limitations=["Evaluates structural topology; does not evaluate semantic entity truth."],
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )

        return DriftObservationRecord(
            drift_observation_id=obs_id,
            domain=DriftDomain.GRAPH,
            target_name=target_name,
            parent_target=graph_layer,
            metric_name=DriftMetricType.JSD,
            metric_value=primary_metric,
            reference_baseline_id=reference_baseline.baseline_id,
            reference_window=reference_baseline.window,
            comparison_window=cmp_window,
            severity=severity,
            status=ObservationStatus.COMPLETED,
            is_statistically_valid=True,
            threshold_policy_version=self.policy.policy_version,
            threshold_applied=self.policy.jsd_elevated,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
            explanation=explanation,
            computed_at=now_iso,
            run_id=generate_run_id(),
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )
