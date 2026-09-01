"""
Model Registry for the NetraGraph Adaptive Model Selection layer.

This registry references empirical results from the committed research benchmark
(training/benchmark/results/repeated_validation_results.json).
It does NOT invent scores or override production Models A–E.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from config import (
    FAMILY_DDOS_VOLUMETRIC,
    FAMILY_MALWARE_STATIC,
    FAMILY_NETWORK_FLOW,
    TASK_BINARY_DDOS,
    TASK_BINARY_INTRUSION,
    TASK_MULTICLASS_MALWARE,
    load_benchmark_results,
)

# ---------------------------------------------------------------------------
# Static metadata per algorithm — characteristics independent of dataset
# ---------------------------------------------------------------------------
ALGORITHM_METADATA: Dict[str, Dict[str, Any]] = {
    "Random Forest": {
        "algorithm": "Random Forest",
        "paradigm": "Bagging Ensemble (Unpruned Trees)",
        "device": "CPU",
        "supported_tasks": [TASK_BINARY_INTRUSION, TASK_BINARY_DDOS, TASK_MULTICLASS_MALWARE],
        "supported_families": [FAMILY_NETWORK_FLOW, FAMILY_DDOS_VOLUMETRIC, FAMILY_MALWARE_STATIC],
        "strengths": [
            "High variance reduction under concept drift",
            "Robust under imbalanced feature spaces",
            "Best single-model malware temporal attribution",
        ],
        "known_limitations": [
            "Highest inference latency (~5 µs/sample)",
            "Highest training time (~3x vs LightGBM)",
            "Tree ensembles can overfit to stale attack signatures with deep depth",
        ],
        "typical_inference_us": 4.97,
        "typical_train_sec": 3.10,
    },
    "XGBoost": {
        "algorithm": "XGBoost",
        "paradigm": "Gradient Boosted Decision Trees (Histogram)",
        "device": "CPU (GPU when available)",
        "supported_tasks": [TASK_BINARY_INTRUSION, TASK_BINARY_DDOS, TASK_MULTICLASS_MALWARE],
        "supported_families": [FAMILY_NETWORK_FLOW, FAMILY_DDOS_VOLUMETRIC, FAMILY_MALWARE_STATIC],
        "strengths": [
            "Fastest overall training throughput",
            "Sub-microsecond inference latency (~0.5 µs/sample)",
            "Strong generalization across multiple benchmark families",
        ],
        "known_limitations": [
            "Slight FPR elevation (~0.15%) under extreme protocol distribution shift",
            "Gradient compression less effective than CatBoost on oblivious trees",
        ],
        "typical_inference_us": 0.51,
        "typical_train_sec": 0.42,
    },
    "LightGBM": {
        "algorithm": "LightGBM",
        "paradigm": "Gradient Boosted Decision Trees (GOSS Histogram)",
        "device": "CPU (OpenCL GPU when available)",
        "supported_tasks": [TASK_BINARY_INTRUSION, TASK_BINARY_DDOS, TASK_MULTICLASS_MALWARE],
        "supported_families": [FAMILY_NETWORK_FLOW, FAMILY_DDOS_VOLUMETRIC, FAMILY_MALWARE_STATIC],
        "strengths": [
            "Fastest training time of all boosting variants",
            "Excellent memory footprint for large feature spaces",
        ],
        "known_limitations": [
            "FPR boundary erosion under protocol-disjoint DDoS (~6.35%)",
            "Slightly less stable on out-of-distribution attacks vs CatBoost",
        ],
        "typical_inference_us": 2.04,
        "typical_train_sec": 0.38,
    },
    "CatBoost": {
        "algorithm": "CatBoost",
        "paradigm": "Gradient Boosted Oblivious Decision Trees",
        "device": "CPU (GPU when available)",
        "supported_tasks": [TASK_BINARY_INTRUSION, TASK_BINARY_DDOS, TASK_MULTICLASS_MALWARE],
        "supported_families": [FAMILY_NETWORK_FLOW, FAMILY_DDOS_VOLUMETRIC, FAMILY_MALWARE_STATIC],
        "strengths": [
            "Perfect boundary preservation on protocol-disjoint DDoS (FPR 0.0000)",
            "Oblivious tree structure prevents boundary over-compression on novel protocols",
        ],
        "known_limitations": [
            "Slightly higher training overhead than XGBoost/LightGBM",
            "Weakest single-model malware attribution (lowest Macro F1: 0.1358)",
        ],
        "typical_inference_us": 0.75,
        "typical_train_sec": 0.88,
    },
}

# Dataset-to-task/family mapping driven by benchmark configuration
DATASET_PROFILE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "cicids2017": {
        "task": TASK_BINARY_INTRUSION,
        "family": FAMILY_NETWORK_FLOW,
        "num_features": 59,
        "is_multiclass": False,
        "temporal": True,
        "protocol_disjoint": False,
    },
    "cicids2018": {
        "task": TASK_BINARY_INTRUSION,
        "family": FAMILY_NETWORK_FLOW,
        "num_features": 61,
        "is_multiclass": False,
        "temporal": True,
        "protocol_disjoint": False,
    },
    "cicddos2019": {
        "task": TASK_BINARY_DDOS,
        "family": FAMILY_DDOS_VOLUMETRIC,
        "num_features": 35,
        "is_multiclass": False,
        "temporal": False,
        "protocol_disjoint": True,
    },
    "unsw": {
        "task": TASK_BINARY_INTRUSION,
        "family": FAMILY_NETWORK_FLOW,
        "num_features": 51,
        "is_multiclass": False,
        "temporal": False,
        "protocol_disjoint": False,
    },
    "malwarebazaar": {
        "task": TASK_MULTICLASS_MALWARE,
        "family": FAMILY_MALWARE_STATIC,
        "num_features": 12,
        "is_multiclass": True,
        "temporal": True,
        "protocol_disjoint": False,
    },
}


def build_algorithm_registry(benchmark_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges static algorithm metadata with empirical benchmark scores.
    Returns a dataset-keyed nested registry:
    registry[dataset][algorithm] = {metadata + empirical scores}
    """
    registry: Dict[str, Any] = {}
    for ds_name, ds_scores in benchmark_results.items():
        registry[ds_name] = {}
        profile = DATASET_PROFILE_DEFAULTS.get(ds_name, {})
        for alg_name, metrics in ds_scores.items():
            meta = ALGORITHM_METADATA.get(alg_name, {}).copy()
            meta["empirical_metrics"] = {
                "mean_f1":     metrics.get("f1", {}).get("mean", 0.0),
                "std_f1":      metrics.get("f1", {}).get("std", 0.0),
                "ci95_f1":     metrics.get("f1", {}).get("ci_95", "N/A"),
                "mean_recall": metrics.get("recall", {}).get("mean", 0.0),
                "mean_fpr":    metrics.get("fpr", {}).get("mean", 0.0),
                "mean_fnr":    metrics.get("fnr", {}).get("mean", 0.0),
                "mean_roc_auc":metrics.get("roc_auc", {}).get("mean", 0.0),
                "mean_train_sec": metrics.get("train_time", {}).get("mean", 0.0),
                "mean_latency_us": metrics.get("latency_us", {}).get("mean", 0.0),
            }
            meta["dataset_profile"] = profile
            meta["dataset"] = ds_name
            meta["validation_methodology"] = (
                "Temporal multi-day split" if profile.get("temporal") and not profile.get("protocol_disjoint")
                else "Protocol-disjoint split" if profile.get("protocol_disjoint")
                else "Official partition split"
            )
            registry[ds_name][alg_name] = meta
    return registry
