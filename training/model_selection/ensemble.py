"""
Ensemble mode evaluator — hard voting, soft voting, and weighted soft voting.
Weights derived ONLY from training/validation evidence, never the final test set.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score


def _safe_f1(y_true, y_pred, avg="binary"):
    try:
        return float(f1_score(y_true, y_pred, average=avg, zero_division=0))
    except Exception:
        return 0.0


def _safe_roc_auc(y_true, y_proba, multi=False):
    try:
        if multi:
            return float(roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro"))
        if y_proba.ndim > 1:
            y_proba = y_proba[:, 1]
        return float(roc_auc_score(y_true, y_proba))
    except Exception:
        return 0.5


def evaluate_ensemble_modes(
    model_predictions: Dict[str, np.ndarray],
    model_probas: Dict[str, np.ndarray],
    model_val_f1s: Dict[str, float],
    y_true: np.ndarray,
    is_multiclass: bool,
) -> Dict[str, Any]:
    """
    Evaluates Hard Voting, Soft Voting, and Weighted Soft Voting ensembles
    and compares them against the best individual model.

    Parameters
    ----------
    model_predictions : {alg_name: predicted_labels}
    model_probas      : {alg_name: class_probability_array}
    model_val_f1s     : {alg_name: validation_F1} — used to derive ensemble weights
                        (MUST come from validation folds, NEVER from y_true test labels)
    y_true            : Ground-truth test labels.
    is_multiclass     : Whether the task is multiclass.

    Returns
    -------
    Comparison dict of each ensemble mode vs best individual.
    """
    algorithms = list(model_predictions.keys())
    avg = "macro" if is_multiclass else "binary"

    # ── Best Individual Model ─────────────────────────────────────────────────
    best_alg, best_f1 = max(model_val_f1s.items(), key=lambda x: x[1])
    best_preds = model_predictions[best_alg]
    best_test_f1 = _safe_f1(y_true, best_preds, avg)

    results = {
        "best_individual": {
            "algorithm": best_alg,
            "validation_f1": round(best_f1, 5),
            "test_f1": round(best_test_f1, 5),
        }
    }

    # ── Hard Voting ───────────────────────────────────────────────────────────
    all_preds = np.stack([model_predictions[a] for a in algorithms], axis=1)
    hard_vote_preds = np.apply_along_axis(
        lambda row: np.bincount(row.astype(int), minlength=int(y_true.max()) + 1).argmax(),
        axis=1, arr=all_preds
    )
    results["hard_voting"] = {
        "algorithms": algorithms,
        "test_f1": round(_safe_f1(y_true, hard_vote_preds, avg), 5),
        "method": "Majority class vote across all models.",
    }

    # ── Soft Voting ───────────────────────────────────────────────────────────
    if all(a in model_probas for a in algorithms):
        probas = [model_probas[a] for a in algorithms]
        # Align shape (ensure all probas have same num_classes dimension)
        max_classes = max(p.shape[1] if p.ndim > 1 else 2 for p in probas)
        padded = []
        for p in probas:
            if p.ndim == 1:
                p = np.column_stack([1 - p, p])
            if p.shape[1] < max_classes:
                pad = np.zeros((p.shape[0], max_classes - p.shape[1]))
                p = np.hstack([p, pad])
            padded.append(p)

        mean_proba = np.mean(np.stack(padded, axis=0), axis=0)
        soft_preds = np.argmax(mean_proba, axis=1)
        results["soft_voting"] = {
            "algorithms": algorithms,
            "test_f1": round(_safe_f1(y_true, soft_preds, avg), 5),
            "method": "Average class probability across all models.",
        }

        # ── Weighted Soft Voting ──────────────────────────────────────────────
        total_val_f1 = sum(model_val_f1s[a] for a in algorithms)
        weights = [model_val_f1s[a] / max(1e-8, total_val_f1) for a in algorithms]
        weighted_proba = np.average(np.stack(padded, axis=0), axis=0, weights=weights)
        weighted_preds = np.argmax(weighted_proba, axis=1)
        results["weighted_soft_voting"] = {
            "algorithms": algorithms,
            "weights": {a: round(w, 4) for a, w in zip(algorithms, weights)},
            "test_f1": round(_safe_f1(y_true, weighted_preds, avg), 5),
            "method": (
                "Probability average weighted by each model's validation-fold F1. "
                "Weights derived from training evidence ONLY — not the test set."
            ),
        }

    return results
