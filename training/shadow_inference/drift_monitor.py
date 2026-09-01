"""
Distribution-Shift & Telemetry Drift Monitor for NetraGraph Shadow Inference.

Monitors feature distribution shift (PSI, KS test), prediction distribution shift,
confidence drift, and model-selection transition shifts without triggering
automated changes in production.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from training.shadow_inference.config import (
        DRIFT_HIGH,
        DRIFT_LOW,
        DRIFT_MEDIUM,
        KS_ALPHA,
        PSI_HIGH_THRESHOLD,
        PSI_LOW_THRESHOLD,
    )
    from training.shadow_inference.schemas import DriftReport
except ImportError:
    from config import (
        DRIFT_HIGH,
        DRIFT_LOW,
        DRIFT_MEDIUM,
        KS_ALPHA,
        PSI_HIGH_THRESHOLD,
        PSI_LOW_THRESHOLD,
    )
    from schemas import DriftReport


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_bins: int = 10,
    eps: float = 1e-4,
) -> float:
    """
    Compute Population Stability Index (PSI) between reference (expected) and current (actual) distributions.
    """
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(expected, quantiles)
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf
    bin_edges = np.unique(bin_edges)

    exp_counts, _ = np.histogram(expected, bins=bin_edges)
    act_counts, _ = np.histogram(actual, bins=bin_edges)

    exp_pct = np.maximum(exp_counts / len(expected), eps)
    act_pct = np.maximum(act_counts / len(actual), eps)

    exp_pct = exp_pct / np.sum(exp_pct)
    act_pct = act_pct / np.sum(act_pct)

    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(psi_val)


class DriftMonitor:
    """
    Research-only telemetry and distribution-shift monitor.
    """

    def __init__(self, reference_data: Optional[pd.DataFrame] = None):
        self.reference_data = reference_data
        self._history_selections: List[str] = []
        self._history_confidences: List[float] = []
        self._history_predictions: List[str] = []

    def set_reference(self, reference_df: pd.DataFrame) -> None:
        """Set the baseline reference dataset for drift calculation."""
        self.reference_data = reference_df.copy()

    def record_telemetry(
        self,
        selected_model: str,
        confidence: float,
        prediction: str,
    ) -> None:
        """Record live shadow telemetry point."""
        self._history_selections.append(selected_model)
        self._history_confidences.append(confidence)
        self._history_predictions.append(str(prediction))

    def evaluate_feature_drift(
        self,
        current_data: pd.DataFrame,
        numeric_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute per-feature PSI and KS-test statistics against the reference distribution.
        """
        if self.reference_data is None or current_data is None:
            return {"psi": {}, "ks_pvalues": {}, "overall_psi": 0.0, "severity": DRIFT_LOW}

        if numeric_columns is None:
            numeric_columns = [
                c for c in current_data.columns
                if c in self.reference_data.columns and current_data[c].dtype.kind in "biufc"
            ]

        psi_dict: Dict[str, float] = {}
        ks_dict: Dict[str, float] = {}

        for col in numeric_columns:
            ref_col = self.reference_data[col].dropna().values
            curr_col = current_data[col].dropna().values

            if len(ref_col) < 5 or len(curr_col) < 5:
                continue

            psi_val = calculate_psi(ref_col, curr_col)
            psi_dict[col] = psi_val

            ks_res = stats.ks_2samp(ref_col, curr_col)
            ks_dict[col] = float(ks_res.pvalue)

        overall_psi = float(np.mean(list(psi_dict.values()))) if psi_dict else 0.0

        # Overall severity based on mean feature PSI
        if overall_psi >= PSI_HIGH_THRESHOLD:
            severity = DRIFT_HIGH
        elif overall_psi >= PSI_LOW_THRESHOLD:
            severity = DRIFT_MEDIUM
        else:
            severity = DRIFT_LOW

        return {
            "psi": psi_dict,
            "ks_pvalues": ks_dict,
            "overall_psi": overall_psi,
            "severity": severity,
        }

    def generate_drift_report(
        self,
        current_data: Optional[pd.DataFrame] = None,
        reference_predictions: Optional[List[str]] = None,
        current_predictions: Optional[List[str]] = None,
    ) -> DriftReport:
        """
        Compile full telemetry and feature drift report.
        """
        ref_size = len(self.reference_data) if self.reference_data is not None else 0
        curr_size = len(current_data) if current_data is not None else 0

        feat_drift = self.evaluate_feature_drift(current_data) if current_data is not None else {
            "psi": {}, "ks_pvalues": {}, "overall_psi": 0.0, "severity": DRIFT_LOW
        }

        pred_shift = 0.0
        if reference_predictions and current_predictions:
            ref_series = pd.Series(reference_predictions).value_counts(normalize=True)
            curr_series = pd.Series(current_predictions).value_counts(normalize=True)
            all_classes = set(ref_series.index).union(set(curr_series.index))
            ref_dist = np.array([ref_series.get(c, 0.0) for c in all_classes])
            curr_dist = np.array([curr_series.get(c, 0.0) for c in all_classes])
            pred_shift = float(np.sum(np.abs(curr_dist - ref_dist)) / 2.0)

        conf_shift = 0.0
        if len(self._history_confidences) >= 10:
            first_half = self._history_confidences[:len(self._history_confidences)//2]
            second_half = self._history_confidences[len(self._history_confidences)//2:]
            conf_shift = float(abs(np.mean(first_half) - np.mean(second_half)))

        severity = feat_drift["severity"]
        if pred_shift > 0.30 or conf_shift > 0.20:
            severity = DRIFT_HIGH if severity != DRIFT_LOW else DRIFT_MEDIUM

        return DriftReport(
            feature_psi=feat_drift["psi"],
            overall_feature_psi=feat_drift["overall_psi"],
            feature_ks_pvalues=feat_drift["ks_pvalues"],
            prediction_distribution_shift=pred_shift,
            confidence_shift=conf_shift,
            drift_severity=severity,
            sample_size_reference=ref_size,
            sample_size_current=curr_size,
        )

    def get_model_selection_distribution(self) -> Dict[str, float]:
        """Return percentage breakdown of model selections recorded in telemetry."""
        if not self._history_selections:
            return {"XGBoost": 0.0, "LightGBM": 0.0, "CatBoost": 0.0, "Random Forest": 0.0}

        counts = pd.Series(self._history_selections).value_counts(normalize=True)
        return {k: round(float(v) * 100.0, 2) for k, v in counts.items()}
