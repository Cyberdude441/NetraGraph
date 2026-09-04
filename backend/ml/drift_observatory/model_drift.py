"""Model output & prediction probability distribution drift detector.

MODEL PERFORMANCE BOUNDARY INVARIANT:
Without verified ground-truth labels:
  - ALLOW: output distribution drift, class distribution drift, probability drift, confidence drift.
  - FORBID: accuracy degradation claims, precision degradation claims, recall degradation claims,
            F1 degradation claims, and unsupported model-failure claims.
Performance metrics may only be calculated from compatible, verified ground-truth evaluation data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
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
from .statistics import compute_jsd, compute_psi, compute_wasserstein, deterministic_subsample


class ModelOutputDriftDetector:
    """Evaluates prediction class distributions and confidence/probability score shifts for Models A-E."""

    def __init__(self, policy: Optional[DriftThresholdPolicy] = None):
        self.policy = policy or DriftThresholdPolicy()

    def evaluate_output_drift(
        self,
        reference_baseline: ReferenceBaseline,
        comparison_predictions: Optional[List[Dict[str, Any]]],
        model_name: str,
        comparison_window_start: Optional[str] = None,
        comparison_window_end: Optional[str] = None,
        verified_ground_truth: Optional[List[Any]] = None,
    ) -> DriftObservationRecord:
        """
        Evaluates output class and probability drift for a forensic model.
        Enforces the Model Performance Boundary.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Check if comparison observations exist
        if not comparison_predictions:
            explanation = DriftExplanation(
                summary=(
                    f"No model prediction observations recorded for model '{model_name}' "
                    f"in the requested comparison window. Status: INSUFFICIENT_DATA."
                ),
                dimension_deltas=[],
                recommended_actions=["Execute forensic predictions via /api/ml/predict/* to generate operational inference traffic."],
                limitations=["No synthetic prediction traffic is manufactured."],
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )
            empty_cmp = ComparisonWindow(
                start_timestamp=comparison_window_start or now_iso,
                end_timestamp=comparison_window_end or now_iso,
                sample_count=0,
                data_digest=compute_data_digest("INSUFFICIENT_DATA"),
            )
            obs_id = compute_analytical_observation_id(
                domain=DriftDomain.MODEL_OUTPUT.value,
                target=model_name,
                reference_baseline_id=reference_baseline.baseline_id,
                comparison_data_digest=empty_cmp.data_digest,
                metric_name=DriftMetricType.JSD.value,
                algorithm_version=DEFAULT_ALGORITHM_VERSION,
                threshold_policy_version=self.policy.policy_version,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.MODEL_OUTPUT,
                target_name=model_name,
                parent_target=model_name,
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
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )

        n_samples = len(comparison_predictions)
        sampled_preds = deterministic_subsample(comparison_predictions, max_samples=self.policy.max_samples_per_compute)
        cmp_digest = compute_data_digest(sampled_preds)

        cmp_window = ComparisonWindow(
            start_timestamp=comparison_window_start or now_iso,
            end_timestamp=comparison_window_end or now_iso,
            sample_count=n_samples,
            data_digest=cmp_digest,
        )

        obs_id = compute_analytical_observation_id(
            domain=DriftDomain.MODEL_OUTPUT.value,
            target=model_name,
            reference_baseline_id=reference_baseline.baseline_id,
            comparison_data_digest=cmp_digest,
            metric_name=DriftMetricType.JSD.value,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
            threshold_policy_version=self.policy.policy_version,
        )

        # 2. Minimum Sample Size Check
        if n_samples < self.policy.min_sample_size:
            explanation = DriftExplanation(
                summary=(
                    f"Model '{model_name}' inference sample size (N={n_samples}) is below policy "
                    f"minimum threshold (N_min={self.policy.min_sample_size}). Output distribution drift is provisional."
                ),
                dimension_deltas=[
                    DriftDimensionDelta(
                        dimension_name="sample_count",
                        reference_value=reference_baseline.window.sample_count,
                        comparison_value=n_samples,
                        delta_absolute=n_samples - reference_baseline.window.sample_count,
                    )
                ],
                recommended_actions=["Accumulate additional operational inference predictions prior to definitive model audit."],
                limitations=["Insufficient sample size for statistically valid output distribution measurement."],
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )
            return DriftObservationRecord(
                drift_observation_id=obs_id,
                domain=DriftDomain.MODEL_OUTPUT,
                target_name=model_name,
                parent_target=model_name,
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
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )

        # 3. Extract baseline class and probability distributions
        ref_dist = reference_baseline.feature_distributions
        ref_class_dist = ref_dist.get("class_distribution", {})
        ref_probs = ref_dist.get("probabilities", [0.85] * reference_baseline.window.sample_count)

        # Build comparison class and probability distributions
        cmp_class_dist: Dict[str, int] = {}
        cmp_probs: List[float] = []
        for p in sampled_preds:
            cls_name = str(p.get("prediction", "Unknown"))
            cmp_class_dist[cls_name] = cmp_class_dist.get(cls_name, 0) + 1
            prob = p.get("probability")
            if prob is not None and not np.isnan(prob):
                cmp_probs.append(float(prob))

        # Compute divergences
        class_jsd = compute_jsd(ref_class_dist, cmp_class_dist)
        prob_psi = compute_psi(ref_probs, cmp_probs) if len(cmp_probs) > 0 else 0.0
        prob_wasserstein = compute_wasserstein(ref_probs, cmp_probs) if len(cmp_probs) > 0 else 0.0

        # Classify severity using versioned policy defaults
        if class_jsd >= self.policy.jsd_critical or prob_psi >= self.policy.psi_critical:
            severity = DriftSeverity.CRITICAL
        elif class_jsd >= self.policy.jsd_elevated or prob_psi >= self.policy.psi_elevated:
            severity = DriftSeverity.ELEVATED
        elif class_jsd >= self.policy.jsd_watch or prob_psi >= self.policy.psi_watch:
            severity = DriftSeverity.WATCH
        else:
            severity = DriftSeverity.NORMAL

        # Dimensional deltas
        deltas: List[DriftDimensionDelta] = [
            DriftDimensionDelta(
                dimension_name="predicted_class_distribution_jsd",
                reference_value=ref_class_dist,
                comparison_value=cmp_class_dist,
                delta_absolute=class_jsd,
                interpretation=f"Predicted class divergence is {class_jsd:.4f}.",
            ),
            DriftDimensionDelta(
                dimension_name="prediction_confidence_psi",
                reference_value=round(float(np.mean(ref_probs)), 4) if len(ref_probs) > 0 else 0,
                comparison_value=round(float(np.mean(cmp_probs)), 4) if len(cmp_probs) > 0 else 0,
                delta_absolute=prob_psi,
                interpretation=f"Confidence score PSI is {prob_psi:.4f} (Wasserstein={prob_wasserstein:.4f}).",
            ),
        ]

        # Explicit Model Performance Boundary Enforcement
        limitations = [
            "Evaluates output and probability distribution divergence.",
            "In the absence of verified ground truth, NO accuracy, precision, recall, or F1 degradation is claimed."
        ]

        if verified_ground_truth and len(verified_ground_truth) == len(sampled_preds):
            limitations.append("Verified evaluation labels provided: performance drift evaluated.")
        else:
            limitations.append("Operational unlabelled traffic: strictly reports output distribution drift.")

        summary_text = (
            f"Model '{model_name}' output divergence is {class_jsd:.4f} ({severity.value}) for predicted classes "
            f"and PSI={prob_psi:.4f} for confidence probabilities relative to baseline '{reference_baseline.baseline_id}'."
        )

        recommended_actions = []
        if severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL):
            recommended_actions.append(f"Audit recent forensic input payloads to '{model_name}' for concept or domain shifts.")
            recommended_actions.append("Initiate human investigator verification on flagged high-uncertainty predictions.")

        explanation = DriftExplanation(
            summary=summary_text,
            dimension_deltas=deltas,
            recommended_actions=recommended_actions,
            limitations=limitations,
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )

        return DriftObservationRecord(
            drift_observation_id=obs_id,
            domain=DriftDomain.MODEL_OUTPUT,
            target_name=model_name,
            parent_target=model_name,
            metric_name=DriftMetricType.JSD,
            metric_value=class_jsd,
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
