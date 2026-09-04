"""Input feature distribution and missingness drift detector.

REAL DATA AVAILABILITY INVARIANT:
If historical raw feature observations are unavailable for a requested operational window,
the detector MUST explicitly return DATA_UNAVAILABLE rather than generating synthetic data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Union
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
from .statistics import (
    compute_jsd,
    compute_missingness_delta,
    compute_psi,
    compute_wasserstein,
    deterministic_subsample,
)


class FeatureDriftDetector:
    """Evaluates distribution shifts and missingness deltas across continuous and categorical model inputs."""

    def __init__(self, policy: Optional[DriftThresholdPolicy] = None):
        self.policy = policy or DriftThresholdPolicy()

    def evaluate_feature_drift(
        self,
        reference_baseline: ReferenceBaseline,
        comparison_records: Optional[List[Dict[str, Any]]],
        feature_name: str,
        parent_model: str,
        is_categorical: bool = False,
        comparison_window_start: Optional[str] = None,
        comparison_window_end: Optional[str] = None,
    ) -> DriftObservationRecord:
        """
        Evaluates drift for an individual input feature.
        If comparison_records is None or empty, returns DATA_UNAVAILABLE.
        If sample size is below policy minimum, returns INSUFFICIENT_DATA.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        metric_type = DriftMetricType.JSD if is_categorical else DriftMetricType.PSI

        # 1. Real Data Availability Check
        if comparison_records is None:
            explanation = DriftExplanation(
                summary=(
                    f"Historical raw feature observations for feature '{feature_name}' (model '{parent_model}') "
                    f"are not logged in persistent storage for this window. Status: DATA_UNAVAILABLE."
                ),
                dimension_deltas=[],
                recommended_actions=[
                    "Provide an evaluated batch dataset or historical feature extraction receipt for comparison.",
                    "Enable live feature ingestion logging if continuous monitoring is desired."
                ],
                limitations=["No synthetic operational data is generated."],
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )
            empty_cmp_window = ComparisonWindow(
                start_timestamp=comparison_window_start or now_iso,
                end_timestamp=comparison_window_end or now_iso,
                sample_count=0,
                data_digest=compute_data_digest("DATA_UNAVAILABLE"),
            )
            obs_id = compute_analytical_observation_id(
                domain=DriftDomain.FEATURE.value,
                target=feature_name,
                reference_baseline_id=reference_baseline.baseline_id,
                comparison_data_digest=empty_cmp_window.data_digest,
                metric_name=metric_type.value,
                algorithm_version=DEFAULT_ALGORITHM_VERSION,
                threshold_policy_version=self.policy.policy_version,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.FEATURE,
                target_name=feature_name,
                parent_target=parent_model,
                metric_name=metric_type,
                metric_value=None,
                reference_baseline_id=reference_baseline.baseline_id,
                reference_window=reference_baseline.window,
                comparison_window=empty_cmp_window,
                severity=DriftSeverity.DATA_UNAVAILABLE,
                status=ObservationStatus.DATA_UNAVAILABLE,
                is_statistically_valid=False,
                threshold_policy_version=self.policy.policy_version,
                threshold_applied=None,
                algorithm_version=DEFAULT_ALGORITHM_VERSION,
                explanation=explanation,
                computed_at=now_iso,
                run_id=generate_run_id(),
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )

        # 2. Extract values and compute missingness
        raw_values = [rec.get(feature_name) for rec in comparison_records]
        total_count = len(raw_values)
        non_null_values = [v for v in raw_values if v is not None and (not isinstance(v, float) or not np.isnan(v))]
        valid_count = len(non_null_values)
        cmp_missing_rate = round(float((total_count - valid_count) / total_count), 4) if total_count > 0 else 1.0

        # Subsample if exceeding policy limits
        sampled_values = deterministic_subsample(non_null_values, max_samples=self.policy.max_samples_per_compute)
        cmp_digest = compute_data_digest(sampled_values)

        cmp_window = ComparisonWindow(
            start_timestamp=comparison_window_start or now_iso,
            end_timestamp=comparison_window_end or now_iso,
            sample_count=total_count,
            data_digest=cmp_digest,
        )

        obs_id = compute_analytical_observation_id(
            domain=DriftDomain.FEATURE.value,
            target=feature_name,
            reference_baseline_id=reference_baseline.baseline_id,
            comparison_data_digest=cmp_digest,
            metric_name=metric_type.value,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
            threshold_policy_version=self.policy.policy_version,
        )

        # 3. Minimum Sample Size Check
        if valid_count < self.policy.min_sample_size:
            explanation = DriftExplanation(
                summary=(
                    f"Feature '{feature_name}' sample size (N={valid_count}) is below policy minimum "
                    f"threshold (N_min={self.policy.min_sample_size}). Drift calculation is provisional."
                ),
                dimension_deltas=[
                    DriftDimensionDelta(
                        dimension_name="sample_count",
                        reference_value=reference_baseline.window.sample_count,
                        comparison_value=valid_count,
                        delta_absolute=valid_count - reference_baseline.window.sample_count,
                    ),
                    DriftDimensionDelta(
                        dimension_name="missingness_rate",
                        reference_value=reference_baseline.feature_distributions.get("missing_rate", 0.0),
                        comparison_value=cmp_missing_rate,
                        delta_absolute=round(cmp_missing_rate - reference_baseline.feature_distributions.get("missing_rate", 0.0), 4),
                    ),
                ],
                recommended_actions=["Collect additional feature observations before establishing statistical significance."],
                limitations=["Insufficient sample size for robust divergence measurement."],
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.FEATURE,
                target_name=feature_name,
                parent_target=parent_model,
                metric_name=metric_type,
                metric_value=None,
                reference_baseline_id=reference_baseline.baseline_id,
                reference_window=reference_baseline.window,
                comparison_window=cmp_window,
                severity=DriftSeverity.INSUFFICIENT_DATA,
                status=ObservationStatus.INSUFFICIENT_DATA,
                is_statistically_valid=False,
                threshold_policy_version=self.policy.policy_version,
                threshold_applied=None,
                algorithm_version=DEFAULT_ALGORITHM_VERSION,
                explanation=explanation,
                computed_at=now_iso,
                run_id=generate_run_id(),
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )

        # 4. Compute Statistical Divergence
        ref_dist = reference_baseline.feature_distributions
        ref_missing_rate = float(ref_dist.get("missing_rate", 0.0))
        missing_delta = compute_missingness_delta(ref_missing_rate, cmp_missing_rate)

        if is_categorical:
            ref_counts = ref_dist.get("category_counts", {})
            cmp_counts: Dict[str, int] = {}
            for v in sampled_values:
                k = str(v)
                cmp_counts[k] = cmp_counts.get(k, 0) + 1
            divergence = compute_jsd(ref_counts, cmp_counts)
            threshold_applied = self.policy.jsd_elevated
            critical_thresh = self.policy.jsd_critical
            watch_thresh = self.policy.jsd_watch
        else:
            ref_samples = ref_dist.get("samples")
            if ref_samples is None:
                # If baseline stored quantiles, approximate reference sample
                quantiles = ref_dist.get("quantiles", [0.0] * 11)
                ref_samples = quantiles
            divergence = compute_psi(ref_samples, sampled_values)
            threshold_applied = self.policy.psi_elevated
            critical_thresh = self.policy.psi_critical
            watch_thresh = self.policy.psi_watch

        # Check severity against configurable policy defaults
        if divergence >= critical_thresh or missing_delta >= self.policy.missingness_critical:
            severity = DriftSeverity.CRITICAL
        elif divergence >= threshold_applied or missing_delta >= self.policy.missingness_elevated:
            severity = DriftSeverity.ELEVATED
        elif divergence >= watch_thresh or missing_delta >= self.policy.missingness_watch:
            severity = DriftSeverity.WATCH
        else:
            severity = DriftSeverity.NORMAL

        # Dimension deltas
        deltas: List[DriftDimensionDelta] = [
            DriftDimensionDelta(
                dimension_name="divergence_score",
                reference_value=0.0,
                comparison_value=divergence,
                delta_absolute=divergence,
                interpretation=f"{metric_type.value} is {divergence:.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="missingness_rate",
                reference_value=ref_missing_rate,
                comparison_value=cmp_missing_rate,
                delta_absolute=round(missing_delta, 4),
                interpretation=f"Missingness rate changed by {missing_delta:+.4f}.",
            ),
        ]

        if not is_categorical and len(sampled_values) > 0:
            cmp_mean = float(np.mean(sampled_values))
            ref_mean = float(ref_dist.get("mean", cmp_mean))
            deltas.append(
                DriftDimensionDelta(
                    dimension_name="mean_value",
                    reference_value=round(ref_mean, 4),
                    comparison_value=round(cmp_mean, 4),
                    delta_absolute=round(cmp_mean - ref_mean, 4),
                )
            )

        summary_text = (
            f"Feature '{feature_name}' divergence is {divergence:.4f} ({severity.value}) "
            f"using metric {metric_type.value} relative to baseline '{reference_baseline.baseline_id}'. "
            f"Missingness delta is {missing_delta:.4f}."
        )

        recommended_actions = []
        if severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL):
            recommended_actions.append(f"Inspect upstream ETL ingestion pipelines feeding '{feature_name}'.")
            recommended_actions.append(f"Review sensor or parser configuration for field '{feature_name}'.")

        explanation = DriftExplanation(
            summary=summary_text,
            dimension_deltas=deltas,
            recommended_actions=recommended_actions,
            limitations=["Evaluates statistical divergence; does not indicate model corruption."],
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )

        return DriftObservationRecord(
            drift_observation_id=obs_id,
            domain=DriftDomain.FEATURE,
            target_name=feature_name,
            parent_target=parent_model,
            metric_name=metric_type,
            metric_value=divergence,
            reference_baseline_id=reference_baseline.baseline_id,
            reference_window=reference_baseline.window,
            comparison_window=cmp_window,
            severity=severity,
            status=ObservationStatus.COMPLETED,
            is_statistically_valid=True,
            threshold_policy_version=self.policy.policy_version,
            threshold_applied=threshold_applied,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
            explanation=explanation,
            computed_at=now_iso,
            run_id=generate_run_id(),
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )
