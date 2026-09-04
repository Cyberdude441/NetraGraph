"""Data quality & multi-modal ingestion pipeline drift detector.

REAL DATA AVAILABILITY INVARIANT:
Uses actual ingestion receipts and audit log events.
If historical ingestion logs or failure rates are unindexed or unavailable,
the detector explicitly returns DATA_UNAVAILABLE or INSUFFICIENT_DATA.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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
from .statistics import compute_jsd, compute_missingness_delta, deterministic_subsample


class DataQualityDriftDetector:
    """Detects throughput shifts, schema anomalies, and missing-field spikes in ingestion pipelines."""

    def __init__(self, policy: Optional[DriftThresholdPolicy] = None):
        self.policy = policy or DriftThresholdPolicy()

    def evaluate_quality_drift(
        self,
        reference_baseline: ReferenceBaseline,
        ingestion_records: Optional[List[Dict[str, Any]]],
        pipeline_name: str = "MultiModalIngestion",
        comparison_window_start: Optional[str] = None,
        comparison_window_end: Optional[str] = None,
    ) -> DriftObservationRecord:
        """
        Evaluates ingestion quality, missing field frequencies, and validation failure rates.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        if ingestion_records is None:
            explanation = DriftExplanation(
                summary=(
                    f"Historical raw ingestion records and validation failure logs for pipeline "
                    f"'{pipeline_name}' are not indexed for this window. Status: DATA_UNAVAILABLE."
                ),
                dimension_deltas=[],
                recommended_actions=["Supply an evaluated ingestion batch or audit receipt for quality analysis."],
                limitations=["No synthetic ingestion records are generated."],
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )
            empty_cmp = ComparisonWindow(
                start_timestamp=comparison_window_start or now_iso,
                end_timestamp=comparison_window_end or now_iso,
                sample_count=0,
                data_digest=compute_data_digest("DATA_UNAVAILABLE"),
            )
            obs_id = compute_analytical_observation_id(
                domain=DriftDomain.DATA_QUALITY.value,
                target=pipeline_name,
                reference_baseline_id=reference_baseline.baseline_id,
                comparison_data_digest=empty_cmp.data_digest,
                metric_name=DriftMetricType.MISSINGNESS_DELTA.value,
                algorithm_version=DEFAULT_ALGORITHM_VERSION,
                threshold_policy_version=self.policy.policy_version,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.DATA_QUALITY,
                target_name=pipeline_name,
                parent_target="IngestionGateway",
                metric_name=DriftMetricType.MISSINGNESS_DELTA,
                metric_value=None,
                reference_baseline_id=reference_baseline.baseline_id,
                reference_window=reference_baseline.window,
                comparison_window=empty_cmp,
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

        n_samples = len(ingestion_records)
        sampled_records = deterministic_subsample(ingestion_records, max_samples=self.policy.max_samples_per_compute)
        cmp_digest = compute_data_digest(sampled_records)

        cmp_window = ComparisonWindow(
            start_timestamp=comparison_window_start or now_iso,
            end_timestamp=comparison_window_end or now_iso,
            sample_count=n_samples,
            data_digest=cmp_digest,
        )

        obs_id = compute_analytical_observation_id(
            domain=DriftDomain.DATA_QUALITY.value,
            target=pipeline_name,
            reference_baseline_id=reference_baseline.baseline_id,
            comparison_data_digest=cmp_digest,
            metric_name=DriftMetricType.MISSINGNESS_DELTA.value,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
            threshold_policy_version=self.policy.policy_version,
        )

        # Minimum sample size check
        if n_samples < self.policy.min_sample_size:
            explanation = DriftExplanation(
                summary=(
                    f"Ingestion sample size (N={n_samples}) is below policy minimum threshold "
                    f"(N_min={self.policy.min_sample_size}). Quality drift calculation is provisional."
                ),
                dimension_deltas=[
                    DriftDimensionDelta(
                        dimension_name="sample_count",
                        reference_value=reference_baseline.window.sample_count,
                        comparison_value=n_samples,
                        delta_absolute=n_samples - reference_baseline.window.sample_count,
                    )
                ],
                recommended_actions=["Process additional forensic ingestion batches to achieve statistical significance."],
                limitations=["Insufficient sample size for statistically valid data quality divergence."],
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.DATA_QUALITY,
                target_name=pipeline_name,
                parent_target="IngestionGateway",
                metric_name=DriftMetricType.MISSINGNESS_DELTA,
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

        # Count module distribution and failure rates
        cmp_module_counts: Dict[str, int] = {}
        missing_field_instances = 0
        total_fields_checked = 0
        validation_failures = 0

        for r in sampled_records:
            mod = str(r.get("module", r.get("connector", "UnknownModule")))
            cmp_module_counts[mod] = cmp_module_counts.get(mod, 0) + 1
            if r.get("validation_failed") or r.get("error"):
                validation_failures += 1
            # Check fields
            fields = r.get("fields", r)
            if isinstance(fields, dict):
                for k, v in fields.items():
                    total_fields_checked += 1
                    if v is None or v == "":
                        missing_field_instances += 1

        cmp_missing_rate = round(float(missing_field_instances / max(1, total_fields_checked)), 4)
        cmp_failure_rate = round(float(validation_failures / n_samples), 4)

        # Baseline values
        ref_dist = reference_baseline.feature_distributions
        ref_module_dist = ref_dist.get("module_distribution", {})
        ref_missing_rate = float(ref_dist.get("missing_field_rate", 0.02))
        ref_failure_rate = float(ref_dist.get("failure_rate", 0.01))

        # Metrics
        module_jsd = compute_jsd(ref_module_dist, cmp_module_counts)
        missing_delta = compute_missingness_delta(ref_missing_rate, cmp_missing_rate)
        failure_delta = abs(cmp_failure_rate - ref_failure_rate)

        primary_metric = round(float(max(missing_delta, failure_delta)), 7)

        # Severity
        if primary_metric >= self.policy.missingness_critical or module_jsd >= self.policy.jsd_critical:
            severity = DriftSeverity.CRITICAL
        elif primary_metric >= self.policy.missingness_elevated or module_jsd >= self.policy.jsd_elevated:
            severity = DriftSeverity.ELEVATED
        elif primary_metric >= self.policy.missingness_watch or module_jsd >= self.policy.jsd_watch:
            severity = DriftSeverity.WATCH
        else:
            severity = DriftSeverity.NORMAL

        deltas: List[DriftDimensionDelta] = [
            DriftDimensionDelta(
                dimension_name="missing_field_rate_delta",
                reference_value=ref_missing_rate,
                comparison_value=cmp_missing_rate,
                delta_absolute=round(missing_delta, 4),
                interpretation=f"Missing field rate shifted by {missing_delta:+.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="validation_failure_rate_delta",
                reference_value=ref_failure_rate,
                comparison_value=cmp_failure_rate,
                delta_absolute=round(failure_delta, 4),
                interpretation=f"Validation failure rate shifted by {failure_delta:+.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="module_traffic_distribution_jsd",
                reference_value=ref_module_dist,
                comparison_value=cmp_module_counts,
                delta_absolute=module_jsd,
                interpretation=f"Module volume divergence is {module_jsd:.4f}.",
            ),
        ]

        summary_text = (
            f"Ingestion data quality divergence is {primary_metric:.4f} ({severity.value}) "
            f"relative to baseline '{reference_baseline.baseline_id}'. Missing field delta is {missing_delta:.4f}."
        )

        recommended_actions = []
        if severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL):
            recommended_actions.append("Inspect ingestion connector parsers for unexpected schema mutations or null field spikes.")
            recommended_actions.append("Verify format compliance for recently submitted FIR, CDR, or finance batch documents.")

        explanation = DriftExplanation(
            summary=summary_text,
            dimension_deltas=deltas,
            recommended_actions=recommended_actions,
            limitations=["Evaluates syntactic field presence and validation status; does not evaluate evidentiary veracity."],
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )

        return DriftObservationRecord(
            drift_observation_id=obs_id,
            domain=DriftDomain.DATA_QUALITY,
            target_name=pipeline_name,
            parent_target="IngestionGateway",
            metric_name=DriftMetricType.MISSINGNESS_DELTA,
            metric_value=primary_metric,
            reference_baseline_id=reference_baseline.baseline_id,
            reference_window=reference_baseline.window,
            comparison_window=cmp_window,
            severity=severity,
            status=ObservationStatus.COMPLETED,
            is_statistically_valid=True,
            threshold_policy_version=self.policy.policy_version,
            threshold_applied=self.policy.missingness_elevated,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
            explanation=explanation,
            computed_at=now_iso,
            run_id=generate_run_id(),
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )
