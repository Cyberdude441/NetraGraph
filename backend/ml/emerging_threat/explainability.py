"""Structured explainability generation and factor attributions for early-warning events."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from .events import GOVERNANCE_DISCLAIMER


class EarlyWarningExplainabilityEngine:
    """Produces structured, reproducible explanations for early-warning events."""

    def generate_explanation(
        self,
        network_id: str,
        early_warning_score: float,
        confidence_score: float,
        severity: str,
        contributions: Dict[str, float],
        trajectory_info: Dict[str, Any],
        topology_info: Dict[str, Any],
        burst_info: Dict[str, Any],
        community_info: Dict[str, Any],
        subgraph_candidates: List[Dict[str, Any]],
        dt_gnn_signals: Dict[str, Any],
        fusion_signals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synthesizes structured factors and narrative evidence into an auditable explanation."""
        # Identify top drivers by weight contribution
        sorted_drivers = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
        primary_driver = sorted_drivers[0][0] if sorted_drivers else "multi_factor_convergence"

        supporting_factors: List[Dict[str, Any]] = []
        contradicting_factors: List[Dict[str, Any]] = []

        # Trajectory factor
        t_type = trajectory_info.get("trajectory_type", "STABLE")
        t_score = trajectory_info.get("trajectory_score", 0.0)
        if t_type in ["RAPID_ESCALATION", "SUDDEN_SPIKE", "SUSTAINED_ELEVATION"]:
            supporting_factors.append({
                "factor": "risk_trajectory",
                "indicator": t_type,
                "score": t_score,
                "detail": trajectory_info.get("narrative", ""),
            })
        else:
            contradicting_factors.append({
                "factor": "risk_trajectory",
                "indicator": t_type,
                "score": t_score,
                "detail": trajectory_info.get("narrative", "Trajectory remained stable."),
            })

        # Topology velocity factor
        top_vel = topology_info.get("topology_velocity_score", 0.0)
        if top_vel >= 0.35:
            supporting_factors.append({
                "factor": "topology_velocity",
                "score": top_vel,
                "detail": topology_info.get("narrative", ""),
            })
        else:
            contradicting_factors.append({
                "factor": "topology_velocity",
                "score": top_vel,
                "detail": "Network topology growth was within normal baseline.",
            })

        # Temporal burst factor
        burst_score = burst_info.get("burst_score", 0.0)
        if burst_info.get("burst_detected", False):
            supporting_factors.append({
                "factor": "temporal_burst",
                "score": burst_score,
                "detail": burst_info.get("narrative", ""),
            })

        # Community factor
        comm_score = community_info.get("community_evolution_score", 0.0)
        if comm_score >= 0.30:
            supporting_factors.append({
                "factor": "community_evolution",
                "score": comm_score,
                "detail": community_info.get("narrative", ""),
            })

        # Synthesize analytical narrative
        narrative_parts = [
            f"Early-warning alert for network '{network_id}' indicates {severity} emerging activity "
            f"(score: {early_warning_score:.2f}, confidence: {confidence_score:.2f}) with primary driver: '{primary_driver}'."
        ]

        if supporting_factors:
            top_sup = supporting_factors[0]
            narrative_parts.append(f"Key dynamic pattern: {top_sup['factor']} ({top_sup.get('detail', '')}).")

        if subgraph_candidates:
            narrative_parts.append(
                f"Isolated {len(subgraph_candidates)} candidate emerging high-risk analytical subgraph(s) "
                "warranting investigative attention."
            )

        if contradicting_factors:
            top_contra = contradicting_factors[0]
            narrative_parts.append(f"Mitigating observation: {top_contra.get('detail', '')}.")

        summary_narrative = " ".join(narrative_parts)

        return {
            "overall_warning_score": early_warning_score,
            "confidence": confidence_score,
            "severity": severity,
            "primary_driver": primary_driver,
            "contributions_breakdown": contributions,
            "supporting_factors": supporting_factors,
            "contradicting_factors": contradicting_factors,
            "subgraph_candidates_count": len(subgraph_candidates),
            "summary_narrative": summary_narrative,
            "disclaimer": GOVERNANCE_DISCLAIMER,
        }
