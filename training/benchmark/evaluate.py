"""Standardized Cybersecurity Evaluation & Metric Computation Engine."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray],
    is_multiclass: bool = False,
    train_time_sec: float = 0.0,
    inference_time_sec: float = 0.0,
    n_features: int = 0,
    n_train: int = 0,
    n_test: int = 0,
) -> Dict[str, Any]:
    """Calculates all standardized evaluation metrics for classification models."""
    acc = float(accuracy_score(y_true, y_pred))

    if not is_multiclass:
        # Binary Classification Metrics
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        cm = confusion_matrix(y_true, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
            fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        else:
            fpr = 0.0
            fnr = 0.0

        roc_auc = None
        pr_auc = None
        if y_proba is not None:
            try:
                # Handle single-column or 2-column proba
                pos_proba = y_proba[:, 1] if y_proba.ndim == 2 else y_proba
                roc_auc = float(roc_auc_score(y_true, pos_proba))
                pr_auc = float(average_precision_score(y_true, pos_proba))
            except Exception:
                pass

        # Threshold sweeps for security-sensitive operational bounds
        best_f1_at_fpr_1pct, recall_at_fpr_1pct, thresh_1pct = find_best_at_fpr_limit(y_true, y_proba, max_fpr=0.01)
        best_f1_at_fpr_01pct, recall_at_fpr_01pct, thresh_01pct = find_best_at_fpr_limit(y_true, y_proba, max_fpr=0.001)

        return {
            "accuracy": round(acc, 5),
            "precision": round(prec, 5),
            "recall": round(rec, 5),
            "f1": round(f1, 5),
            "roc_auc": round(roc_auc, 5) if roc_auc is not None else "N/A",
            "pr_auc": round(pr_auc, 5) if pr_auc is not None else "N/A",
            "fpr": round(fpr, 5),
            "fnr": round(fnr, 5),
            "training_time_sec": round(train_time_sec, 3),
            "inference_time_sec": round(inference_time_sec, 4),
            "inference_per_sample_us": round((inference_time_sec / max(1, n_test)) * 1_000_000, 2),
            "num_features": n_features,
            "num_train_samples": n_train,
            "num_test_samples": n_test,
            "confusion_matrix": cm.tolist(),
            "fpr_1pct_metrics": {
                "recall_at_fpr_1pct": round(recall_at_fpr_1pct, 5),
                "f1_at_fpr_1pct": round(best_f1_at_fpr_1pct, 5),
                "threshold": round(thresh_1pct, 5),
            },
            "fpr_01pct_metrics": {
                "recall_at_fpr_01pct": round(recall_at_fpr_01pct, 5),
                "f1_at_fpr_01pct": round(best_f1_at_fpr_01pct, 5),
                "threshold": round(thresh_01pct, 5),
            },
        }

    else:
        # Multiclass Classification Metrics
        macro_prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
        macro_rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
        macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
        weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

        cm = confusion_matrix(y_true, y_pred)
        # Macro FPR / FNR estimation
        fp = cm.sum(axis=0) - np.diag(cm)
        fn = cm.sum(axis=1) - np.diag(cm)
        tp = np.diag(cm)
        tn = cm.sum() - (fp + fn + tp)
        macro_fpr = float(np.mean(fp / np.maximum(1, fp + tn)))
        macro_fnr = float(np.mean(fn / np.maximum(1, fn + tp)))

        roc_auc = None
        if y_proba is not None and y_proba.ndim == 2 and y_proba.shape[1] > 1:
            try:
                roc_auc = float(roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro"))
            except Exception:
                pass

        return {
            "accuracy": round(acc, 5),
            "precision": round(macro_prec, 5),
            "recall": round(macro_rec, 5),
            "f1": round(macro_f1, 5),
            "macro_f1": round(macro_f1, 5),
            "weighted_f1": round(weighted_f1, 5),
            "roc_auc": round(roc_auc, 5) if roc_auc is not None else "N/A",
            "pr_auc": "N/A (Multiclass)",
            "fpr": round(macro_fpr, 5),
            "fnr": round(macro_fnr, 5),
            "training_time_sec": round(train_time_sec, 3),
            "inference_time_sec": round(inference_time_sec, 4),
            "inference_per_sample_us": round((inference_time_sec / max(1, n_test)) * 1_000_000, 2),
            "num_features": n_features,
            "num_train_samples": n_train,
            "num_test_samples": n_test,
            "confusion_matrix": cm.tolist(),
        }


def find_best_at_fpr_limit(
    y_true: np.ndarray,
    y_proba: Optional[np.ndarray],
    max_fpr: float = 0.01,
) -> Tuple[float, float, float]:
    """Sweeps thresholds to find best F1 and Recall achievable while constraining FPR <= max_fpr."""
    if y_proba is None:
        return 0.0, 0.0, 0.5

    pos_proba = y_proba[:, 1] if y_proba.ndim == 2 else y_proba
    fprs, tprs, thresholds = roc_curve(y_true, pos_proba)

    valid_indices = np.where(fprs <= max_fpr)[0]
    if len(valid_indices) == 0:
        return 0.0, 0.0, 0.5

    best_f1 = 0.0
    best_recall = 0.0
    best_thresh = 0.5

    for idx in valid_indices:
        thresh = thresholds[idx]
        pred = (pos_proba >= thresh).astype(int)
        cm = confusion_matrix(y_true, pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            actual_fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            if actual_fpr <= max_fpr:
                cur_f1 = f1_score(y_true, pred, zero_division=0)
                cur_rec = recall_score(y_true, pred, zero_division=0)
                if cur_f1 > best_f1 or (cur_f1 == best_f1 and cur_rec > best_recall):
                    best_f1 = cur_f1
                    best_recall = cur_rec
                    best_thresh = thresh

    return float(best_f1), float(best_recall), float(best_thresh)
