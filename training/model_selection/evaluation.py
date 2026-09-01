"""
Evaluation module — rank stability, ablation study, distribution-shift analysis,
and threshold optimisation from benchmark evidence.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics import (
    f1_score,
    precision_recall_curve,
    roc_curve,
)


# ── Rank Stability ────────────────────────────────────────────────────────────

def compute_rank_stability(benchmark_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    For each algorithm compute: average rank, rank variance, wins, runner-up finishes.
    Rankings are based on empirical mean F1 from the repeated-validation results.
    """
    algorithms = ["Random Forest", "XGBoost", "LightGBM", "CatBoost"]
    datasets = list(benchmark_results.keys())

    # Build rank matrix: rank_matrix[ds][alg] = rank (1 = best)
    rank_matrix: Dict[str, Dict[str, int]] = {}
    for ds in datasets:
        ds_scores = {
            alg: benchmark_results[ds].get(alg, {}).get("f1", {}).get("mean", 0.0)
            for alg in algorithms
        }
        sorted_algs = sorted(ds_scores, key=lambda a: ds_scores[a], reverse=True)
        rank_matrix[ds] = {alg: sorted_algs.index(alg) + 1 for alg in algorithms}

    stability: Dict[str, Any] = {}
    for alg in algorithms:
        ranks = [rank_matrix[ds][alg] for ds in datasets]
        wins     = sum(1 for r in ranks if r == 1)
        runner   = sum(1 for r in ranks if r == 2)
        avg_rank = float(np.mean(ranks))
        var_rank = float(np.var(ranks))
        # Robustness = inverse of (avg_rank * (1 + variance)) — higher is more stable
        robustness = round(1.0 / max(0.01, avg_rank * (1.0 + var_rank)), 4)
        stability[alg] = {
            "ranks_per_dataset": {ds: rank_matrix[ds][alg] for ds in datasets},
            "average_rank": round(avg_rank, 3),
            "rank_variance": round(var_rank, 3),
            "number_of_wins": wins,
            "number_of_runner_up": runner,
            "robustness_score": robustness,
        }
    return stability


# ── Ablation Study ────────────────────────────────────────────────────────────

def ablation_study_from_benchmark(benchmark_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares 'Adaptive Model Selection' strategy against each fixed single model
    using the committed benchmark results.

    Adaptive strategy: for each dataset, select the model with highest mean F1.
    Fixed strategy: always use the same model regardless of dataset.
    """
    algorithms = ["Random Forest", "XGBoost", "LightGBM", "CatBoost"]
    datasets   = list(benchmark_results.keys())

    def get_f1(ds, alg):
        return benchmark_results[ds].get(alg, {}).get("f1", {}).get("mean", 0.0)
    def get_fpr(ds, alg):
        return benchmark_results[ds].get(alg, {}).get("fpr", {}).get("mean", 0.0)
    def get_recall(ds, alg):
        return benchmark_results[ds].get(alg, {}).get("recall", {}).get("mean", 0.0)
    def get_lat(ds, alg):
        return benchmark_results[ds].get(alg, {}).get("latency_us", {}).get("mean", 5.0)

    # Adaptive: best per dataset
    adaptive_f1s   = [max(get_f1(ds, a) for a in algorithms) for ds in datasets]
    adaptive_fprs  = []
    adaptive_lats  = []
    for ds in datasets:
        best_alg = max(algorithms, key=lambda a: get_f1(ds, a))
        adaptive_fprs.append(get_fpr(ds, best_alg))
        adaptive_lats.append(get_lat(ds, best_alg))

    strategies: Dict[str, Any] = {
        "Adaptive Model Selection": {
            "mean_f1":     round(float(np.mean(adaptive_f1s)), 5),
            "mean_fpr":    round(float(np.mean(adaptive_fprs)), 5),
            "mean_recall": round(float(np.mean([max(get_recall(ds, a) for a in algorithms) for ds in datasets])), 5),
            "mean_latency_us": round(float(np.mean(adaptive_lats)), 3),
            "per_dataset_winner": {ds: max(algorithms, key=lambda a: get_f1(ds, a)) for ds in datasets},
        }
    }

    for fixed_alg in algorithms:
        f1s   = [get_f1(ds, fixed_alg) for ds in datasets]
        fprs  = [get_fpr(ds, fixed_alg) for ds in datasets]
        recs  = [get_recall(ds, fixed_alg) for ds in datasets]
        lats  = [get_lat(ds, fixed_alg) for ds in datasets]
        strategies[f"Fixed_{fixed_alg}"] = {
            "mean_f1":         round(float(np.mean(f1s)), 5),
            "mean_fpr":        round(float(np.mean(fprs)), 5),
            "mean_recall":     round(float(np.mean(recs)), 5),
            "mean_latency_us": round(float(np.mean(lats)), 3),
        }

    # Delta vs adaptive
    adaptive_mean_f1 = strategies["Adaptive Model Selection"]["mean_f1"]
    for strat_name, vals in strategies.items():
        if strat_name != "Adaptive Model Selection":
            vals["delta_f1_vs_adaptive"] = round(vals["mean_f1"] - adaptive_mean_f1, 5)
    return strategies


# ── Distribution-Shift Analysis ───────────────────────────────────────────────

def distribution_shift_analysis(benchmark_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quantifies performance degradation under temporal and protocol shift by
    comparing benchmark F1 scores across dataset/family types.

    Uses committed benchmark evidence — does NOT rerun training.
    """
    algorithms = ["Random Forest", "XGBoost", "LightGBM", "CatBoost"]

    # Proxy for shift severity per dataset
    SHIFT_LABELS = {
        "cicids2017":   "Temporal day-based shift (Mon–Fri attack-family variation)",
        "cicids2018":   "Temporal multi-day shift (week-over-week enterprise attacks)",
        "cicddos2019":  "Protocol-disjoint shift (trained reflection vs volumetric)",
        "unsw":         "Official partition (moderate distribution change)",
        "malwarebazaar":"Temporal polymorphic concept drift (Sep–Oct signature mutation)",
    }

    SHIFT_SEVERITY = {
        "cicids2017":   "MODERATE",
        "cicids2018":   "MODERATE",
        "cicddos2019":  "HIGH (Protocol-Disjoint)",
        "unsw":         "LOW",
        "malwarebazaar":"VERY HIGH (Concept Drift)",
    }

    shift_results: Dict[str, Any] = {}
    for ds in benchmark_results:
        ds_data = benchmark_results[ds]
        alg_f1s = {a: ds_data.get(a, {}).get("f1", {}).get("mean", 0.0) for a in algorithms}
        alg_fprs= {a: ds_data.get(a, {}).get("fpr", {}).get("mean", 0.0) for a in algorithms}

        # Adaptive = best algorithm for this dataset
        adaptive_alg = max(alg_f1s, key=alg_f1s.get)
        fixed_xgb_f1 = alg_f1s.get("XGBoost", 0.0)

        shift_results[ds] = {
            "shift_label": SHIFT_LABELS.get(ds, "Unknown"),
            "shift_severity": SHIFT_SEVERITY.get(ds, "UNKNOWN"),
            "adaptive_selected_model": adaptive_alg,
            "adaptive_f1": round(alg_f1s[adaptive_alg], 5),
            "fixed_xgboost_f1": round(fixed_xgb_f1, 5),
            "delta_f1_adaptive_vs_fixed_xgb": round(alg_f1s[adaptive_alg] - fixed_xgb_f1, 5),
            "algorithm_f1_ranking": sorted(alg_f1s.items(), key=lambda x: x[1], reverse=True),
            "algorithm_fpr": alg_fprs,
        }
    return shift_results


# ── Threshold Optimisation ────────────────────────────────────────────────────

def threshold_optimisation(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    fpr_constraints: List[float] = (0.01, 0.001, 0.0001),
) -> Dict[str, Any]:
    """
    Sweeps probability thresholds to find:
    - Threshold maximising F1
    - Best threshold under each FPR constraint
    """
    if y_proba.ndim > 1:
        y_proba = y_proba[:, 1]

    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    fprs_roc, tprs_roc, roc_thresholds = roc_curve(y_true, y_proba)

    # F1 at each threshold
    f1s = 2 * (precisions[:-1] * recalls[:-1]) / np.maximum(1e-9, precisions[:-1] + recalls[:-1])
    best_f1_idx = int(np.argmax(f1s))

    results: Dict[str, Any] = {
        "best_f1_threshold": {
            "threshold": round(float(thresholds[best_f1_idx]), 5),
            "f1": round(float(f1s[best_f1_idx]), 5),
            "precision": round(float(precisions[best_f1_idx]), 5),
            "recall": round(float(recalls[best_f1_idx]), 5),
        },
        "fpr_constrained_thresholds": {},
    }

    # FPR-constrained optimal thresholds
    for fpr_limit in fpr_constraints:
        valid_mask = fprs_roc <= fpr_limit
        if valid_mask.any():
            best_idx = int(np.argmax(tprs_roc[valid_mask]))
            best_thresh = roc_thresholds[valid_mask][best_idx]
            preds = (y_proba >= best_thresh).astype(int)
            actual_fpr = float(fprs_roc[valid_mask][best_idx])
            actual_recall = float(tprs_roc[valid_mask][best_idx])
            f1_val = float(f1_score(y_true, preds, zero_division=0))
            results["fpr_constrained_thresholds"][f"FPR<={fpr_limit*100:.1f}%"] = {
                "threshold": round(float(best_thresh), 5),
                "actual_fpr": round(actual_fpr, 6),
                "recall": round(actual_recall, 5),
                "f1": round(f1_val, 5),
                "note": f"Best recall while maintaining FPR <= {fpr_limit*100:.1f}%",
            }
        else:
            results["fpr_constrained_thresholds"][f"FPR<={fpr_limit*100:.1f}%"] = {
                "note": f"No threshold achieves FPR <= {fpr_limit*100:.1f}% on this dataset."
            }

    return results
