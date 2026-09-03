"""Multi-signal early-warning scoring and independent confidence modeling."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from .config import EarlyWarningWeightsConfig, EmergingThreatConfig, EventSeverity


def map_warning_severity(score: float, config: EmergingThreatConfig) -> EventSeverity:
    """Deterministically maps a continuous early-warning score into standardized severity tiers."""
    if score >= config.critical_warning_threshold:
        return EventSeverity.CRITICAL
    if score >= config.high_warning_threshold:
        return EventSeverity.HIGH
    if score >= config.medium_warning_threshold:
        return EventSeverity.MEDIUM
    return EventSeverity.LOW


class EarlyWarningScorer:
    """Combines heterogeneous dynamic signals into an early-warning score separate from static threat risk."""

    def __init__(self, config: Optional[EmergingThreatConfig] = None):
        self.config = config or EmergingThreatConfig()

    def calculate_score(
        self,
        trajectory_score: float = 0.0,
        topology_velocity_score: float = 0.0,
        centrality_velocity_score: float = 0.0,
        temporal_burst_score: float = 0.0,
        community_evolution_score: float = 0.0,
        dt_gnn_anomaly_score: Optional[float] = None,
        fusion_risk_score: Optional[float] = None,
        snapshot_count: int = 1,
        timespan_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculates early_warning_score and confidence_score.

        Strict Invariants:
        1. Early-warning score is distinct from underlying static threat risk.
        2. Early-warning score is distinct from confidence score.
        """
        w = self.config.weights
        contributions: Dict[str, float] = {}

        # Collect present weighted components
        components = [
            ("trajectory", trajectory_score, w.trajectory_weight),
            ("topology_velocity", topology_velocity_score, w.topology_velocity_weight),
            ("centrality_velocity", centrality_velocity_score, w.centrality_shift_weight),
            ("temporal_burst", temporal_burst_score, w.temporal_burst_weight),
            ("community_evolution", community_evolution_score, w.community_evolution_weight),
        ]

        if dt_gnn_anomaly_score is not None:
            components.append(("dt_gnn_anomaly", max(0.0, min(1.0, dt_gnn_anomaly_score)), w.dt_gnn_anomaly_weight))

        if fusion_risk_score is not None:
            components.append(("threat_fusion", max(0.0, min(1.0, fusion_risk_score)), w.threat_fusion_weight))

        total_weight = sum(comp[2] for comp in components)
        weighted_sum = sum(comp[1] * comp[2] for comp in components)

        early_warning_score = weighted_sum / max(0.001, total_weight)
        early_warning_score = max(0.0, min(1.0, early_warning_score))

        # Store breakdown
        for name, val, weight in components:
            contributions[name] = round(val * (weight / total_weight), 4)

        # Independent Confidence Modeling
        # Factors: snapshot count, timespan length, source availability
        snapshot_factor = min(1.0, snapshot_count / float(self.config.min_snapshots_for_confidence))
        timespan_factor = min(1.0, max(0.30, timespan_seconds / 3600.0)) # Adequate observation window
        source_factor = min(1.0, len(components) / 7.0)

        raw_confidence = (0.40 * snapshot_factor + 0.30 * timespan_factor + 0.30 * source_factor)
        final_confidence = max(
            self.config.min_confidence_floor,
            min(1.0, raw_confidence),
        )

        severity = map_warning_severity(early_warning_score, self.config)

        return {
            "early_warning_score": round(early_warning_score, 4),
            "confidence_score": round(final_confidence, 4),
            "severity": severity,
            "contributions": contributions,
            "components_present": [comp[0] for comp in components],
        }
