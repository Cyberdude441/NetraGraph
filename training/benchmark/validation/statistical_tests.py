"""Statistical Significance Testing & Confidence Interval Computation Engine."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats


def compute_mean_std_ci95(values: List[float]) -> Dict[str, Any]:
    """
    Computes sample mean, standard deviation, and true 95% Student-t confidence interval:
    CI_95 = mean ± t_{n-1, 0.975} * (std / sqrt(n))
    """
    clean_vals = [float(v) for v in values if isinstance(v, (int, float)) and not np.isnan(v)]
    n = len(clean_vals)
    if n == 0:
        return {"mean": 0.0, "std": 0.0, "ci_95": "N/A", "ci_low": 0.0, "ci_high": 0.0}

    mean_val = float(np.mean(clean_vals))
    if n == 1:
        return {
            "mean": round(mean_val, 5),
            "std": 0.0,
            "ci_95": f"[{mean_val:.4f}, {mean_val:.4f}]",
            "ci_low": round(mean_val, 5),
            "ci_high": round(mean_val, 5),
        }

    std_val = float(np.std(clean_vals, ddof=1))
    # Student's t distribution critical value
    t_crit = stats.t.ppf(0.975, df=n - 1)
    margin = t_crit * (std_val / math.sqrt(n))

    ci_low = max(0.0, mean_val - margin)
    ci_high = min(1.0, mean_val + margin)

    return {
        "mean": round(mean_val, 5),
        "std": round(std_val, 5),
        "ci_95": f"[{ci_low:.4f}, {ci_high:.4f}]",
        "ci_low": round(ci_low, 5),
        "ci_high": round(ci_high, 5),
    }


def perform_pairwise_statistical_tests(
    algorithm_fold_scores: Dict[str, List[float]],
    metric_name: str = "f1",
) -> List[Dict[str, Any]]:
    """
    Performs paired Wilcoxon signed-rank and Paired t-tests across all algorithm pairs:
    - CatBoost vs XGBoost
    - CatBoost vs LightGBM
    - CatBoost vs Random Forest
    - XGBoost vs LightGBM
    - XGBoost vs Random Forest
    - LightGBM vs Random Forest
    """
    algorithms = list(algorithm_fold_scores.keys())
    comparisons = []

    for i in range(len(algorithms)):
        for j in range(i + 1, len(algorithms)):
            alg_a = algorithms[i]
            alg_b = algorithms[j]
            scores_a = np.array(algorithm_fold_scores[alg_a], dtype=np.float64)
            scores_b = np.array(algorithm_fold_scores[alg_b], dtype=np.float64)

            mean_a = float(np.mean(scores_a))
            mean_b = float(np.mean(scores_b))
            diff = scores_a - scores_b

            # If all differences are identical (e.g. both 1.0 or identical scores)
            if np.all(diff == 0):
                comparisons.append({
                    "comparison": f"{alg_a} vs {alg_b}",
                    "metric": metric_name,
                    "mean_a": round(mean_a, 5),
                    "mean_b": round(mean_b, 5),
                    "test_type": "Paired Exact Difference",
                    "statistic": 0.0,
                    "p_value": 1.0,
                    "statistically_significant": False,
                    "winner": "TIE (Identical Performance)",
                    "note": "Zero variance between paired fold scores",
                })
                continue

            # Paired t-test
            try:
                t_stat, p_val = stats.ttest_rel(scores_a, scores_b)
                test_type = "Paired Student t-test"
                stat_val = float(t_stat)
                p_val_clean = float(p_val)
            except Exception:
                test_type = "Mean Difference"
                stat_val = float(mean_a - mean_b)
                p_val_clean = 1.0

            # Wilcoxon signed rank test if sample size allows and diff != 0
            nonzero_diffs = diff[diff != 0]
            if len(nonzero_diffs) >= 3:
                try:
                    w_res = stats.wilcoxon(scores_a, scores_b, zero_method="wilcox")
                    test_type = "Wilcoxon Signed-Rank"
                    stat_val = float(w_res.statistic)
                    p_val_clean = float(w_res.pvalue)
                except Exception:
                    pass

            is_sig = p_val_clean < 0.05
            if is_sig:
                winner = alg_a if mean_a > mean_b else alg_b
            else:
                winner = "NO_STATISTICAL_DIFFERENCE (p >= 0.05)"

            comparisons.append({
                "comparison": f"{alg_a} vs {alg_b}",
                "metric": metric_name,
                "mean_a": round(mean_a, 5),
                "mean_b": round(mean_b, 5),
                "test_type": test_type,
                "statistic": round(stat_val, 4) if not np.isnan(stat_val) else 0.0,
                "p_value": round(p_val_clean, 5) if not np.isnan(p_val_clean) else 1.0,
                "statistically_significant": is_sig,
                "winner": winner,
            })

    return comparisons
