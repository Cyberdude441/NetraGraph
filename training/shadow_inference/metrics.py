"""
Security Metrics & Evaluation Suite for NetraGraph Shadow Inference.

Calculates standard classification metrics (TP, TN, FP, FN, Accuracy, Precision, Recall,
F1, FPR, FNR, ROC-AUC, PR-AUC) for retrospective evaluation, and latency percentiles
(mean, median, p95, p99).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
)

from comparator import normalize_prediction


def compute_security_metrics(
    y_true: Union[np.ndarray, List[Any]],
    y_pred: Union[np.ndarray, List[Any]],
    y_scores: Optional[Union[np.ndarray, List[float]]] = None,
    is_multiclass: bool = False,
) -> Dict[str, Any]:
    """
    Calculate comprehensive security and forensic classification metrics.
    Labels are evaluated strictly retrospectively.
    """
    # Normalize labels to binary 0/1 (or keep integers if multiclass)
    if is_multiclass:
        y_t = np.array(y_true, dtype=int)
        y_p = np.array(y_pred, dtype=int)
        avg = "macro"
    else:
        y_t = np.array([1 if normalize_prediction(val) == "MALICIOUS" else 0 for val in y_true])
        y_p = np.array([1 if normalize_prediction(val) == "MALICIOUS" else 0 for val in y_pred])
        avg = "binary"

    acc = float(accuracy_score(y_t, y_p))
    prec = float(precision_score(y_t, y_p, average=avg, zero_division=0))
    rec = float(recall_score(y_t, y_p, average=avg, zero_division=0))
    f1 = float(f1_score(y_t, y_p, average=avg, zero_division=0))

    tp, tn, fp, fn = 0, 0, 0, 0
    fpr, fnr = 0.0, 0.0

    if not is_multiclass:
        tn, fp, fn, tp = confusion_matrix(y_t, y_p, labels=[0, 1]).ravel()
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    roc_auc = None
    pr_auc = None

    if y_scores is not None and len(y_scores) == len(y_t):
        scores_arr = np.array(y_scores, dtype=float)
        try:
            if is_multiclass:
                if scores_arr.ndim > 1:
                    roc_auc = float(roc_auc_score(y_t, scores_arr, multi_class="ovr", average="macro"))
            else:
                roc_auc = float(roc_auc_score(y_t, scores_arr))
                pr_auc = float(average_precision_score(y_t, scores_arr))
        except Exception:
            pass

    return {
        "accuracy": round(acc, 5),
        "precision": round(prec, 5),
        "recall": round(rec, 5),
        "f1": round(f1, 5),
        "fpr": round(fpr, 6),
        "fnr": round(fnr, 6),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "roc_auc": round(roc_auc, 5) if roc_auc is not None else None,
        "pr_auc": round(pr_auc, 5) if pr_auc is not None else None,
    }


def compute_latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    """
    Calculate mean, median (p50), p90, p95, and p99 latency percentiles in milliseconds.
    """
    if not latencies_ms:
        return {"mean": 0.0, "median": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "min": 0.0, "max": 0.0}

    arr = np.array(latencies_ms, dtype=float)
    return {
        "mean": round(float(np.mean(arr)), 4),
        "median": round(float(np.median(arr)), 4),
        "p90": round(float(np.percentile(arr, 90.0)), 4),
        "p95": round(float(np.percentile(arr, 95.0)), 4),
        "p99": round(float(np.percentile(arr, 99.0)), 4),
        "min": round(float(np.min(arr)), 4),
        "max": round(float(np.max(arr)), 4),
    }


def compare_model_metrics(
    production_metrics: Dict[str, Any],
    adaptive_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute deltas (Adaptive - Production) across all security metrics.
    """
    delta: Dict[str, Any] = {}
    for metric in ["f1", "accuracy", "precision", "recall", "fpr", "fnr", "roc_auc", "pr_auc"]:
        prod_val = production_metrics.get(metric)
        adapt_val = adaptive_metrics.get(metric)
        if prod_val is not None and adapt_val is not None:
            delta[f"{metric}_delta"] = round(adapt_val - prod_val, 6)
    return delta
