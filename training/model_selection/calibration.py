"""
Calibration module — Platt scaling and Isotonic regression.
Calibration is fitted on inner validation data ONLY, never on the final test set.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss


def evaluate_calibration(
    y_val: np.ndarray,
    raw_proba: np.ndarray,
    n_bins: int = 10,
) -> Dict[str, Any]:
    """
    Computes calibration metrics on a VALIDATION set (never the test set).

    Parameters
    ----------
    y_val     : True validation labels.
    raw_proba : Raw model probability estimates on the validation set.
    n_bins    : Number of bins for reliability diagram and ECE calculation.

    Returns
    -------
    {
        "brier_score": float,
        "log_loss": float,
        "expected_calibration_error": float,
        "calibration_curve": { "fraction_of_positives": ..., "mean_predicted_value": ... }
    }
    """
    # Flatten to binary positive class probability
    if raw_proba.ndim > 1:
        prob_pos = raw_proba[:, 1]
    else:
        prob_pos = raw_proba

    brier = float(brier_score_loss(y_val, prob_pos))
    ll = float(log_loss(y_val, prob_pos))

    # Calibration curve (reliability diagram)
    frac_pos, mean_pred = calibration_curve(y_val, prob_pos, n_bins=n_bins, strategy="uniform")

    # Expected Calibration Error
    ece = float(np.mean(np.abs(frac_pos - mean_pred)))

    return {
        "brier_score": round(brier, 6),
        "log_loss": round(ll, 6),
        "expected_calibration_error": round(ece, 6),
        "calibration_curve": {
            "fraction_of_positives": frac_pos.tolist(),
            "mean_predicted_value": mean_pred.tolist(),
        },
        "note": "All calibration metrics computed on inner validation data, not the final test partition.",
    }


def apply_platt_scaling(
    y_cal: np.ndarray,
    raw_proba_cal: np.ndarray,
    raw_proba_test: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Applies Platt scaling (logistic regression on log-odds of raw probabilities).
    Fitted on calibration split, applied to test split.
    Returns (calibrated_val_proba, calibrated_test_proba).
    """
    if raw_proba_cal.ndim > 1:
        p_cal = raw_proba_cal[:, 1].reshape(-1, 1)
        p_te  = raw_proba_test[:, 1].reshape(-1, 1)
    else:
        p_cal = raw_proba_cal.reshape(-1, 1)
        p_te  = raw_proba_test.reshape(-1, 1)

    lr = LogisticRegression(C=1e5, solver="lbfgs", max_iter=500)
    lr.fit(p_cal, y_cal)
    cal_val  = lr.predict_proba(p_cal)[:, 1]
    cal_test = lr.predict_proba(p_te)[:, 1]
    return cal_val, cal_test


def apply_isotonic_regression(
    y_cal: np.ndarray,
    raw_proba_cal: np.ndarray,
    raw_proba_test: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Applies Isotonic Regression calibration.
    Fitted on calibration split only.
    """
    if raw_proba_cal.ndim > 1:
        p_cal = raw_proba_cal[:, 1]
        p_te  = raw_proba_test[:, 1]
    else:
        p_cal = raw_proba_cal
        p_te  = raw_proba_test

    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(p_cal, y_cal)
    cal_val  = iso.predict(p_cal)
    cal_test = iso.predict(p_te)
    return cal_val, cal_test
