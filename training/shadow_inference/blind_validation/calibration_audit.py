"""
Confidence Calibration, Brier Score, ECE, and Reliability Curve Audit.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, log_loss


def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    r"""
    Compute Expected Calibration Error (ECE).
    $$ECE = \sum_{m=1}^{M} \frac{|B_m|}{N} |\text{acc}(B_m) - \text{conf}(B_m)|$$
    """
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)

    for i in range(n_bins):
        bin_mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1] if i < n_bins - 1 else y_prob <= bin_edges[i + 1])
        bin_count = np.sum(bin_mask)
        if bin_count > 0:
            bin_acc = np.mean(y_true[bin_mask])
            bin_conf = np.mean(y_prob[bin_mask])
            ece += (bin_count / total_samples) * abs(bin_acc - bin_conf)

    return float(ece)


def evaluate_calibration(
    y_true: np.ndarray,
    prod_probs: np.ndarray,
    adapt_probs: np.ndarray,
    n_bins: int = 10,
) -> Dict[str, Any]:
    """
    Compute comprehensive probability calibration metrics for both Production and Adaptive paths.
    """
    y_t = np.array(y_true, dtype=int)
    p_p = np.clip(np.array(prod_probs, dtype=float), 1e-6, 1.0 - 1e-6)
    a_p = np.clip(np.array(adapt_probs, dtype=float), 1e-6, 1.0 - 1e-6)

    # 1. Brier Score (lower is better, 0.0 is perfect)
    brier_prod = float(brier_score_loss(y_t, p_p))
    brier_adapt = float(brier_score_loss(y_t, a_p))

    # 2. Log-Loss (lower is better)
    logloss_prod = float(log_loss(y_t, p_p, labels=[0, 1]))
    logloss_adapt = float(log_loss(y_t, a_p, labels=[0, 1]))

    # 3. Expected Calibration Error (ECE)
    ece_prod = calculate_ece(y_t, p_p, n_bins=n_bins)
    ece_adapt = calculate_ece(y_t, a_p, n_bins=n_bins)

    # 4. Reliability Curves
    prob_true_p, prob_pred_p = calibration_curve(y_t, p_p, n_bins=n_bins)
    prob_true_a, prob_pred_a = calibration_curve(y_t, a_p, n_bins=n_bins)

    return {
        "production": {
            "brier_score": round(brier_prod, 5),
            "log_loss": round(logloss_prod, 5),
            "ece": round(ece_prod, 5),
            "reliability_curve": {
                "prob_pred": [round(float(v), 4) for v in prob_pred_p],
                "prob_true": [round(float(v), 4) for v in prob_true_p],
            },
        },
        "adaptive": {
            "brier_score": round(brier_adapt, 5),
            "log_loss": round(logloss_adapt, 5),
            "ece": round(ece_adapt, 5),
            "reliability_curve": {
                "prob_pred": [round(float(v), 4) for v in prob_pred_a],
                "prob_true": [round(float(v), 4) for v in prob_true_a],
            },
        },
        "delta": {
            "brier_score_delta": round(brier_adapt - brier_prod, 5),
            "log_loss_delta": round(logloss_adapt - logloss_prod, 5),
            "ece_delta": round(ece_adapt - ece_prod, 5),
        },
    }
