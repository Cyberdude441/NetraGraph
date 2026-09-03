"""Risk trajectory modeling, slope velocity, and acceleration analysis."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .config import RiskTrajectoryConfig, TrajectoryType


@dataclass
class RiskTrajectoryResult:
    """Quantitative trajectory of risk evolution over chronological observation windows."""
    target_id: str
    trajectory_type: TrajectoryType
    trajectory_score: float                  # Bounded [0, 1] escalation score
    velocity: float                          # Average slope of risk per step
    acceleration: float                      # Change in slope (second derivative)
    raw_scores: List[float] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    narrative: str = ""


class RiskTrajectoryAnalyzer:
    """Analyzes directional trends, sudden spikes, and volatility in risk trajectories."""

    def __init__(self, config: Optional[RiskTrajectoryConfig] = None):
        self.config = config or RiskTrajectoryConfig()

    def analyze_trajectory(
        self,
        target_id: str,
        observations: List[Tuple[float, float]], # List of (timestamp, risk_score)
    ) -> RiskTrajectoryResult:
        """Evaluates a chronological series of (timestamp, risk_score) pairs.

        Invariant: Does NOT modify any underlying risk score. Produces an independent trajectory signal.
        """
        if not observations:
            return RiskTrajectoryResult(
                target_id=target_id,
                trajectory_type=TrajectoryType.STABLE,
                trajectory_score=0.0,
                velocity=0.0,
                acceleration=0.0,
                narrative="No temporal risk observations available.",
            )

        # Sort chronologically
        sorted_obs = sorted(observations, key=lambda x: x[0])
        timestamps = [x[0] for x in sorted_obs]
        scores = [max(0.0, min(1.0, float(x[1]))) for x in sorted_obs]

        if len(scores) == 1:
            # Single observation
            single_score = scores[0]
            is_sustained = single_score >= self.config.sustained_elevation_threshold
            t_type = TrajectoryType.SUSTAINED_ELEVATION if is_sustained else TrajectoryType.STABLE
            return RiskTrajectoryResult(
                target_id=target_id,
                trajectory_type=t_type,
                trajectory_score=round(single_score, 4),
                velocity=0.0,
                acceleration=0.0,
                raw_scores=scores,
                timestamps=timestamps,
                narrative=f"Single observation baseline established with score {single_score:.2f}.",
            )

        # Calculate step differences
        diffs = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
        avg_velocity = sum(diffs) / len(diffs)

        # Calculate acceleration (second derivative across steps)
        if len(diffs) >= 2:
            second_diffs = [diffs[i] - diffs[i - 1] for i in range(1, len(diffs))]
            acceleration = sum(second_diffs) / len(second_diffs)
        else:
            acceleration = 0.0

        # Variance for volatility check
        variance = float(np.var(scores))
        max_step_jump = max(diffs) if diffs else 0.0
        all_high = all(s >= self.config.sustained_elevation_threshold for s in scores)

        # Classify trajectory type
        if max_step_jump >= self.config.sudden_spike_delta:
            t_type = TrajectoryType.SUDDEN_SPIKE
            urgency = min(1.0, 0.70 + 0.30 * (max_step_jump / 1.0))
            narrative = f"Abrupt risk jump detected (+{max_step_jump:.2f}) across observation intervals."

        elif avg_velocity >= self.config.rapid_escalation_slope:
            t_type = TrajectoryType.RAPID_ESCALATION
            urgency = min(1.0, 0.60 + 0.40 * (avg_velocity / 0.50))
            narrative = f"Rapid upward risk escalation (velocity +{avg_velocity:.3f}/step)."

        elif all_high:
            t_type = TrajectoryType.SUSTAINED_ELEVATION
            urgency = min(1.0, sum(scores) / len(scores))
            narrative = f"Sustained elevated risk across all {len(scores)} observation windows (mean {urgency:.2f})."

        elif avg_velocity <= -0.10:
            t_type = TrajectoryType.DE_ESCALATING
            urgency = max(0.10, scores[-1])
            narrative = f"Risk trajectory is de-escalating (velocity {avg_velocity:.3f}/step)."

        elif variance >= self.config.volatility_variance_threshold:
            t_type = TrajectoryType.VOLATILE
            urgency = min(1.0, 0.50 + 0.50 * math.sqrt(variance))
            narrative = f"Volatile oscillatory risk behavior detected (variance {variance:.3f})."

        else:
            t_type = TrajectoryType.STABLE
            urgency = max(0.05, scores[-1] * 0.50)
            narrative = f"Risk trajectory remained stable (mean velocity {avg_velocity:.3f})."

        return RiskTrajectoryResult(
            target_id=target_id,
            trajectory_type=t_type,
            trajectory_score=round(max(0.0, min(1.0, urgency)), 4),
            velocity=round(avg_velocity, 4),
            acceleration=round(acceleration, 4),
            raw_scores=scores,
            timestamps=timestamps,
            narrative=narrative,
        )
