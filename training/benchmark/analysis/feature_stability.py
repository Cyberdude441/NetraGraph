"""Feature Importance and Cross-Fold Stability Analysis Engine."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def compute_feature_stability_across_folds(
    fold_feature_importances: Dict[str, List[Dict[str, float]]],
    feature_names: List[str],
) -> Dict[str, Any]:
    """
    Computes feature importance mean, standard deviation, and rank stability:
    - Per-algorithm feature rankings
    - Consolidated ensemble importance
    - Rank stability across multiple validation folds
    """
    algorithms = list(fold_feature_importances.keys())
    results: Dict[str, Any] = {"algorithms": {}, "consolidated_top_features": []}

    all_alg_feature_scores: Dict[str, List[float]] = {f: [] for f in feature_names}

    for alg in algorithms:
        fold_dicts = fold_feature_importances[alg]
        if not fold_dicts:
            continue

        feature_records = []
        for feat in feature_names:
            vals = [fd.get(feat, 0.0) for fd in fold_dicts]
            mean_imp = float(np.mean(vals))
            std_imp = float(np.std(vals)) if len(vals) > 1 else 0.0

            # Collect for consolidated ensemble
            all_alg_feature_scores[feat].append(mean_imp)

            feature_records.append({
                "feature": feat,
                "mean_importance": round(mean_imp, 5),
                "std_importance": round(std_imp, 5),
            })

        # Sort descending
        feature_records.sort(key=lambda x: x["mean_importance"], reverse=True)
        # Assign ranks and calculate stability
        for rank, rec in enumerate(feature_records, 1):
            rec["rank"] = rank
            # Rank stability index (lower std relative to mean indicates stable signal)
            rec["stability_score"] = round(1.0 / (1.0 + rec["std_importance"] / max(1e-4, rec["mean_importance"])), 4)

        results["algorithms"][alg] = {
            "top_10_features": feature_records[:10],
            "all_features_ranked": feature_records,
        }

    # Consolidated multi-algorithm rankings
    consolidated = []
    for feat, scores in all_alg_feature_scores.items():
        if scores:
            mean_score = float(np.mean(scores))
            std_score = float(np.std(scores)) if len(scores) > 1 else 0.0
            consolidated.append({
                "feature": feat,
                "ensemble_mean_importance": round(mean_score, 5),
                "ensemble_std_importance": round(std_score, 5),
                "stability_index": round(1.0 / (1.0 + std_score / max(1e-4, mean_score)), 4),
            })

    consolidated.sort(key=lambda x: x["ensemble_mean_importance"], reverse=True)
    for rank, item in enumerate(consolidated, 1):
        item["consolidated_rank"] = rank

    results["consolidated_top_features"] = consolidated[:15]
    return results
