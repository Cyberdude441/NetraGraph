"""Threat Intelligence & OSINT source behavior, freshness, and conflict frequency drift detector.

PHASE 15 INTEGRATION INVARIANT:
Reads Phase 15 Threat Intelligence state strictly READ-ONLY.
Preserves Phase 15 SourceTrustPolicy, multi-dimensional ConfidenceProfiles, and CTI disclaimer.
Does NOT alter correlation decisions, conflict records, or provenance DAGs.
"""
from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import numpy as np

from .config import (
    CTI_OSINT_DRIFT_DISCLAIMER,
    DEFAULT_ALGORITHM_VERSION,
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
from .statistics import compute_jsd, compute_wasserstein, deterministic_subsample


class CTISourceDriftDetector:
    """Evaluates behavioral shifts, conflict rates, and freshness degradation across external threat feeds."""

    def __init__(self, policy: Optional[DriftThresholdPolicy] = None):
        self.policy = policy or DriftThresholdPolicy()

    def evaluate_source_drift(
        self,
        reference_baseline: ReferenceBaseline,
        indicators: Optional[List[Dict[str, Any]]],
        conflicts: Optional[List[Dict[str, Any]]] = None,
        correlations: Optional[List[Dict[str, Any]]] = None,
        feed_name: str = "ExternalCTIFeeds",
        comparison_window_start: Optional[str] = None,
        comparison_window_end: Optional[str] = None,
    ) -> DriftObservationRecord:
        """
        Evaluates source contribution distributions, conflict rate spikes, and freshness degradation.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        now_epoch = time.time()

        if not indicators:
            explanation = DriftExplanation(
                summary=(
                    f"No active threat intelligence or OSINT indicator records populated "
                    f"in the requested comparison window. Status: INSUFFICIENT_DATA."
                ),
                dimension_deltas=[],
                recommended_actions=["Ingest threat intelligence feeds via Phase 15 Threat Intelligence APIs."],
                limitations=["No synthetic indicators are fabricated."],
                disclaimer=CTI_OSINT_DRIFT_DISCLAIMER,
            )
            empty_cmp = ComparisonWindow(
                start_timestamp=comparison_window_start or now_iso,
                end_timestamp=comparison_window_end or now_iso,
                sample_count=0,
                data_digest=compute_data_digest("INSUFFICIENT_DATA"),
            )
            obs_id = compute_analytical_observation_id(
                domain=DriftDomain.CTI_SOURCE.value,
                target=feed_name,
                reference_baseline_id=reference_baseline.baseline_id,
                comparison_data_digest=empty_cmp.data_digest,
                metric_name=DriftMetricType.JSD.value,
                algorithm_version=DEFAULT_ALGORITHM_VERSION,
                threshold_policy_version=self.policy.policy_version,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.CTI_SOURCE,
                target_name=feed_name,
                parent_target="ThreatIntelligenceEngine",
                metric_name=DriftMetricType.JSD,
                metric_value=None,
                reference_baseline_id=reference_baseline.baseline_id,
                reference_window=reference_baseline.window,
                comparison_window=empty_cmp,
                severity=DriftSeverity.INSUFFICIENT_DATA,
                status=ObservationStatus.INSUFFICIENT_DATA,
                is_statistically_valid=False,
                threshold_policy_version=self.policy.policy_version,
                threshold_applied=None,
                algorithm_version=DEFAULT_ALGORITHM_VERSION,
                explanation=explanation,
                computed_at=now_iso,
                run_id=generate_run_id(),
                disclaimer=CTI_OSINT_DRIFT_DISCLAIMER,
            )

        n_samples = len(indicators)
        sampled_iocs = deterministic_subsample(indicators, max_samples=self.policy.max_samples_per_compute)
        cmp_digest = compute_data_digest(sampled_iocs)

        cmp_window = ComparisonWindow(
            start_timestamp=comparison_window_start or now_iso,
            end_timestamp=comparison_window_end or now_iso,
            sample_count=n_samples,
            data_digest=cmp_digest,
        )

        obs_id = compute_analytical_observation_id(
            domain=DriftDomain.CTI_SOURCE.value,
            target=feed_name,
            reference_baseline_id=reference_baseline.baseline_id,
            comparison_data_digest=cmp_digest,
            metric_name=DriftMetricType.JSD.value,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
            threshold_policy_version=self.policy.policy_version,
        )

        # Minimum sample size check
        if n_samples < self.policy.min_sample_size:
            explanation = DriftExplanation(
                summary=(
                    f"CTI indicator sample size (N={n_samples}) is below policy minimum "
                    f"threshold (N_min={self.policy.min_sample_size}). Source drift calculation is provisional."
                ),
                dimension_deltas=[
                    DriftDimensionDelta(
                        dimension_name="sample_count",
                        reference_value=reference_baseline.window.sample_count,
                        comparison_value=n_samples,
                        delta_absolute=n_samples - reference_baseline.window.sample_count,
                    )
                ],
                recommended_actions=["Ingest additional CTI telemetry before assessing feed reliability shifts."],
                limitations=["Insufficient sample size for statistically valid source divergence."],
                disclaimer=CTI_OSINT_DRIFT_DISCLAIMER,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.CTI_SOURCE,
                target_name=feed_name,
                parent_target="ThreatIntelligenceEngine",
                metric_name=DriftMetricType.JSD,
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
                disclaimer=CTI_OSINT_DRIFT_DISCLAIMER,
            )

        # Build comparison distributions
        cmp_source_dist: Dict[str, int] = {}
        cmp_type_dist: Dict[str, int] = {}
        cmp_ages_days: List[float] = []

        for ioc in sampled_iocs:
            src = str(ioc.get("source_id", "UnknownSource"))
            cmp_source_dist[src] = cmp_source_dist.get(src, 0) + 1
            itype = str(ioc.get("type", ioc.get("ioc_type", "UNKNOWN")))
            cmp_type_dist[itype] = cmp_type_dist.get(itype, 0) + 1
            last_obs = ioc.get("last_observed_timestamp") or ioc.get("timestamp") or now_epoch
            age_days = max(0.0, (now_epoch - float(last_obs)) / 86400.0)
            cmp_ages_days.append(age_days)

        # Compute conflict rate and unresolved correlation rate
        n_conflicts = len(conflicts) if conflicts else 0
        cmp_conflict_rate = round(float(n_conflicts / n_samples), 4)

        n_unresolved = 0
        if correlations:
            n_unresolved = sum(1 for c in correlations if str(c.get("review_status", "")).upper() == "REVIEW_REQUIRED")
            cmp_unresolved_rate = round(float(n_unresolved / len(correlations)), 4)
        else:
            cmp_unresolved_rate = 0.0

        # Extract baseline distributions
        ref_dist = reference_baseline.feature_distributions
        ref_source_dist = ref_dist.get("source_distribution", {})
        ref_type_dist = ref_dist.get("type_distribution", {})
        ref_conflict_rate = float(ref_dist.get("conflict_rate", 0.02))
        ref_ages = ref_dist.get("ages_days", [5.0] * reference_baseline.window.sample_count)

        # Compute metrics
        source_jsd = compute_jsd(ref_source_dist, cmp_source_dist)
        type_jsd = compute_jsd(ref_type_dist, cmp_type_dist)
        age_wasserstein = compute_wasserstein(ref_ages, cmp_ages_days)
        conflict_delta = abs(cmp_conflict_rate - ref_conflict_rate)

        primary_metric = round(float(0.6 * source_jsd + 0.4 * type_jsd), 7)

        # Classify severity using versioned policy defaults
        if primary_metric >= self.policy.jsd_critical or conflict_delta >= self.policy.missingness_critical:
            severity = DriftSeverity.CRITICAL
        elif primary_metric >= self.policy.jsd_elevated or conflict_delta >= self.policy.missingness_elevated:
            severity = DriftSeverity.ELEVATED
        elif primary_metric >= self.policy.jsd_watch or conflict_delta >= self.policy.missingness_watch:
            severity = DriftSeverity.WATCH
        else:
            severity = DriftSeverity.NORMAL

        deltas: List[DriftDimensionDelta] = [
            DriftDimensionDelta(
                dimension_name="source_contribution_jsd",
                reference_value=ref_source_dist,
                comparison_value=cmp_source_dist,
                delta_absolute=source_jsd,
                interpretation=f"Source contribution divergence is {source_jsd:.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="indicator_type_jsd",
                reference_value=ref_type_dist,
                comparison_value=cmp_type_dist,
                delta_absolute=type_jsd,
                interpretation=f"Indicator type divergence is {type_jsd:.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="conflict_rate_delta",
                reference_value=ref_conflict_rate,
                comparison_value=cmp_conflict_rate,
                delta_absolute=round(conflict_delta, 4),
                interpretation=f"Conflict frequency shifted by {conflict_delta:+.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="freshness_wasserstein_days",
                reference_value=round(float(np.mean(ref_ages)), 1) if len(ref_ages) > 0 else 0,
                comparison_value=round(float(np.mean(cmp_ages_days)), 1) if len(cmp_ages_days) > 0 else 0,
                delta_absolute=age_wasserstein,
                interpretation=f"Mean indicator age divergence is {age_wasserstein:.2f} days.",
            ),
        ]

        summary_text = (
            f"CTI source behavior divergence is {primary_metric:.4f} ({severity.value}) relative to baseline "
            f"'{reference_baseline.baseline_id}'. Conflict rate delta is {conflict_delta:.4f}."
        )

        recommended_actions = []
        if severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL):
            recommended_actions.append("Review SourceTrustPolicy tiers for newly dominant or conflicting intelligence sources.")
            recommended_actions.append("Audit unreviewed correlation candidates in Phase 15 human review queue.")

        explanation = DriftExplanation(
            summary=summary_text,
            dimension_deltas=deltas,
            recommended_actions=recommended_actions,
            limitations=["Evaluates intelligence feed volume and consistency; does not verify external intelligence veracity."],
            disclaimer=CTI_OSINT_DRIFT_DISCLAIMER,
        )

        return DriftObservationRecord(
            drift_observation_id=obs_id,
            domain=DriftDomain.CTI_SOURCE,
            target_name=feed_name,
            parent_target="ThreatIntelligenceEngine",
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
            disclaimer=CTI_OSINT_DRIFT_DISCLAIMER,
        )
