"""
Core Model Selector Engine — the primary decision-making API.

Usage (research / decision-support only):

    from model_selector import select_model_for_dataset, predict_with_selected_model

These interfaces are ISOLATED from production Models A–E and
backend/models/registry/. They must NOT be called from production API routes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from training.model_selection.config import (
        FAMILY_DDOS_VOLUMETRIC,
        FAMILY_MALWARE_STATIC,
        FAMILY_NETWORK_FLOW,
        TASK_BINARY_DDOS,
        TASK_BINARY_INTRUSION,
        TASK_MULTICLASS_MALWARE,
        load_benchmark_results,
    )
    from training.model_selection.dataset_profiler import profile_dataset
    from training.model_selection.explainability import generate_selection_explanation
    from training.model_selection.model_registry import DATASET_PROFILE_DEFAULTS, build_algorithm_registry
    from training.model_selection.scoring import compute_selection_confidence, rank_algorithms
except ImportError:
    from config import (
        FAMILY_DDOS_VOLUMETRIC,
        FAMILY_MALWARE_STATIC,
        FAMILY_NETWORK_FLOW,
        TASK_BINARY_DDOS,
        TASK_BINARY_INTRUSION,
        TASK_MULTICLASS_MALWARE,
        load_benchmark_results,
    )
    from dataset_profiler import profile_dataset
    from explainability import generate_selection_explanation
    from model_registry import DATASET_PROFILE_DEFAULTS, build_algorithm_registry
    from scoring import compute_selection_confidence, rank_algorithms

import numpy as np
import pandas as pd


# ─── Pre-load registry once ──────────────────────────────────────────────────
_BENCHMARK_RESULTS = load_benchmark_results()
_REGISTRY = build_algorithm_registry(_BENCHMARK_RESULTS)


def select_model_for_dataset(
    dataset_name: str,
    df: Optional[pd.DataFrame] = None,
    target_column: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Research-only model selection API.

    Parameters
    ----------
    dataset_name : str
        One of: cicids2017, cicids2018, cicddos2019, unsw, malwarebazaar.
        Used to look up the validated benchmark registry.
    df : pd.DataFrame, optional
        If provided, the dataset profiler extracts live structural metadata.
    target_column : str, optional
        Target column name (only used for class balance metadata, never for selection).

    Returns
    -------
    {
        "selected_model": str,
        "selection_confidence": float,       ← selection evidence strength (NOT prediction probability)
        "alternatives": [ {"algorithm": ..., "operational_score": ...} ],
        "explanation": { ... },
        "profile": { ... },
    }

    IMPORTANT: This function is NOT connected to production Models A–E.
    """
    ds_key = dataset_name.lower().replace("-", "").replace("_", "")
    # Normalise dataset name
    if "2018" in ds_key or "cse" in ds_key:
        ds_key = "cicids2018"
    elif "2017" in ds_key:
        ds_key = "cicids2017"
    elif "ddos" in ds_key or "2019" in ds_key:
        ds_key = "cicddos2019"
    elif "unsw" in ds_key:
        ds_key = "unsw"
    elif "malware" in ds_key or "bazaar" in ds_key:
        ds_key = "malwarebazaar"

    if ds_key not in _REGISTRY:
        raise ValueError(
            f"Unknown dataset '{dataset_name}'. Available: {list(_REGISTRY.keys())}"
        )

    ds_registry = _REGISTRY[ds_key]
    profile_defaults = DATASET_PROFILE_DEFAULTS[ds_key]
    family = profile_defaults["family"]
    task = profile_defaults["task"]

    # Live dataset profiling (optional)
    live_profile: Dict[str, Any] = {}
    if df is not None:
        live_profile = profile_dataset(df, target_column=target_column, dataset_hint=ds_key)
        # Override family/task from live profiler if it disagrees
        family = live_profile.get("inferred_dataset_family", family)
        task   = live_profile.get("inferred_task_type", task)

    # ── Rank algorithms ───────────────────────────────────────────────────────
    ranked = rank_algorithms(ds_registry, family, task)
    confidence = compute_selection_confidence(ranked)

    best_name, best_score = ranked[0]
    alternatives = [
        {"algorithm": name, "operational_score": round(sc, 5)}
        for name, sc in ranked[1:]
    ]

    # ── Explanation ───────────────────────────────────────────────────────────
    explanation = generate_selection_explanation(
        selected_model=best_name,
        selected_score=best_score,
        alternatives=ranked[1:],
        dataset_name=ds_key,
        family=family,
        task=task,
        registry_entry=ds_registry[best_name],
        confidence=confidence,
    )

    return {
        "selected_model": best_name,
        "operational_score": round(best_score, 5),
        "selection_confidence": confidence,
        "alternatives": alternatives,
        "explanation": explanation,
        "live_profile": live_profile,
        "dataset": ds_key,
        "task": task,
        "family": family,
    }


def predict_with_selected_model(
    dataset_name: str,
    X: np.ndarray,
    y: np.ndarray,
) -> Dict[str, Any]:
    """
    Research-only inference proxy.

    Selects the best model per evidence, trains it on X/y, returns predictions.
    This is isolated from production and uses only the benchmark-validated
    algorithm implementations from training/benchmark/models/.

    IMPORTANT: Does NOT modify production Models A–E or backend/models/registry/.
    """
    import sys
    from pathlib import Path

    # Import benchmark model wrappers
    benchmark_dir = Path(__file__).resolve().parents[1] / "benchmark"
    for sub in [str(benchmark_dir), str(benchmark_dir / "models")]:
        if sub not in sys.path:
            sys.path.insert(0, sub)

    from config import detect_system_environment
    env_info = detect_system_environment()

    selection = select_model_for_dataset(dataset_name)
    model_name = selection["selected_model"]
    task = selection["task"]
    is_multiclass = task == TASK_MULTICLASS_MALWARE

    n_train = int(len(X) * 0.75)
    X_tr, X_te = X[:n_train], X[n_train:]
    y_tr, y_te = y[:n_train], y[n_train:]

    if model_name == "Random Forest":
        from random_forest import train_and_evaluate_rf as _train
        result = _train(X_tr, y_tr, X_te, y_te, is_multiclass, env_info)
    elif model_name == "XGBoost":
        from xgboost_model import train_and_evaluate_xgb as _train
        result = _train(X_tr, y_tr, X_te, y_te, is_multiclass, env_info)
    elif model_name == "LightGBM":
        from lightgbm_model import train_and_evaluate_lgb as _train
        result = _train(X_tr, y_tr, X_te, y_te, is_multiclass, env_info)
    else:
        from catboost_model import train_and_evaluate_catboost as _train
        result = _train(X_tr, y_tr, X_te, y_te, is_multiclass, env_info)

    return {
        "selected_model": model_name,
        "selection_confidence": selection["selection_confidence"],
        "evaluation": result,
        "note": (
            "Research-only inference proxy. "
            "Does NOT affect production Models A–E or backend/models/registry/."
        ),
    }
