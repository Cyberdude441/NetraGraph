"""NetraGraph Rigorous Multi-Algorithm ML Benchmark Runner (Temporal & Cross-Partition Validation)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ["LOKY_MAX_CPU_COUNT"] = "4"

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler

# Add benchmark directory and models directory to sys.path
BENCHMARK_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BENCHMARK_DIR.parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))
if str(BENCHMARK_DIR / "models") not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR / "models"))

from config import (
    DATASET_LOADERS,
    LEAKAGE_HEADERS,
    RANDOM_SEED,
    RESULTS_DIR,
    detect_system_environment,
    print_environment_banner,
)
from models.catboost_model import train_and_evaluate_catboost
from models.lightgbm_model import train_and_evaluate_lgb
from models.random_forest import train_and_evaluate_rf
from models.xgboost_model import train_and_evaluate_xgb


def preprocess_temporal_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_column: str,
    is_multiclass: bool,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str], LabelEncoder, StandardScaler]:
    """
    Applies strict leakage prevention across temporal / cross-partition boundaries.
    - All transformers (Imputer, Encoders, Scaler) are FIT STRICTLY ON TRAIN SPLIT.
    - Test split is purely transformed with zero forward leakage.
    """
    train_df = train_df.copy()
    test_df = test_df.copy()

    # 1. Clean Column Names
    train_df.columns = [str(c).strip() for c in train_df.columns]
    test_df.columns = [str(c).strip() for c in test_df.columns]

    # 2. Identify and Purge Leakage Columns
    drop_cols_train = [c for c in train_df.columns if c != target_column and c.lower() in LEAKAGE_HEADERS]
    drop_cols_test = [c for c in test_df.columns if c != target_column and c.lower() in LEAKAGE_HEADERS]

    if drop_cols_train:
        train_df = train_df.drop(columns=drop_cols_train)
    if drop_cols_test:
        test_df = test_df.drop(columns=drop_cols_test)

    # 3. Separate features and target
    X_train_df = train_df.drop(columns=[target_column]).copy()
    y_train_raw = train_df[target_column].copy()

    X_test_df = test_df.drop(columns=[target_column]).copy()
    y_test_raw = test_df[target_column].copy()

    # 4. Handle Categoricals vs Numerics
    numeric_cols = [c for c in X_train_df.columns if X_train_df[c].dtype.kind in "biufc"]
    categorical_cols = [c for c in X_train_df.columns if c not in numeric_cols]

    # Impute numeric features based STRICTLY ON TRAIN MEDIAN
    for c in numeric_cols:
        X_train_df[c] = pd.to_numeric(X_train_df[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
        median_val = X_train_df[c].median()
        if pd.isna(median_val):
            median_val = 0.0
        X_train_df[c] = X_train_df[c].fillna(median_val)

        # Apply same train median to test
        if c in X_test_df.columns:
            X_test_df[c] = pd.to_numeric(X_test_df[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
            X_test_df[c] = X_test_df[c].fillna(median_val)

    # Encode categoricals with dummy variables and align test columns
    if categorical_cols:
        X_train_df = pd.get_dummies(X_train_df, columns=categorical_cols, drop_first=True)
        X_test_df = pd.get_dummies(X_test_df, columns=[c for c in categorical_cols if c in X_test_df.columns], drop_first=True)
        # Align test columns to train columns exactly
        X_test_df = X_test_df.reindex(columns=X_train_df.columns, fill_value=0)

    feature_names = list(X_train_df.columns)
    X_train = X_train_df.values.astype(np.float32)
    X_test = X_test_df.values.astype(np.float32)

    # 5. Encode Target (Fit strictly on Train)
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train_raw.astype(str))

    # Map test labels safely
    train_classes = set(label_encoder.classes_)
    y_test_clean = []
    for val in y_test_raw.astype(str):
        if val in train_classes:
            y_test_clean.append(label_encoder.transform([val])[0])
        else:
            y_test_clean.append(0)  # Default fallback for unseen out-of-distribution label
    y_test = np.array(y_test_clean, dtype=np.int64)

    # 6. Feature Scaling (Fit strictly on Train)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    return X_train, y_train, X_test, y_test, feature_names, label_encoder, scaler


def run_benchmark_for_dataset(
    dataset_name: str,
    env_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Runs Random Forest, XGBoost, LightGBM, and CatBoost on the rigorous temporal/cross-partition split."""
    if dataset_name not in DATASET_LOADERS:
        raise ValueError(f"Unknown dataset: '{dataset_name}'. Available: {list(DATASET_LOADERS.keys())}")

    print("\n" + "=" * 82)
    print(f"RIGOROUS BENCHMARK RUN: {dataset_name.upper()}")
    print("=" * 82)

    loader_fn = DATASET_LOADERS[dataset_name]
    train_df, test_df, target_col, is_multiclass, partition_desc = loader_fn()

    print(f"Validation Strategy: {partition_desc}")
    print(f"Target Column      : '{target_col}' (Multiclass: {is_multiclass})")
    print(f"Train Raw Partition: {train_df.shape[0]:,} rows, {train_df.shape[1]} columns")
    print(f"Test Raw Partition : {test_df.shape[0]:,} rows, {test_df.shape[1]} columns")

    # Strict Leakage-Free Preprocessing across Partitions
    X_train, y_train, X_test, y_test, feature_names, label_encoder, _ = preprocess_temporal_split(
        train_df=train_df,
        test_df=test_df,
        target_column=target_col,
        is_multiclass=is_multiclass,
    )

    print(f"Sanitized Features : {len(feature_names)} features (All identifiers & timestamps purged)")
    print(f"Train Matrix Shape : {X_train.shape[0]:,} samples x {X_train.shape[1]} features")
    print(f"Test Matrix Shape  : {X_test.shape[0]:,} samples x {X_test.shape[1]} features")
    print(f"Train Class Balance: {dict(pd.Series(y_train).value_counts().sort_index())}")
    print(f"Test Class Balance : {dict(pd.Series(y_test).value_counts().sort_index())}")
    print("-" * 82)

    algorithm_results = []

    # 1. Random Forest
    print("\n[1/4] Training Random Forest (100 trees, balanced bagging)...")
    rf_res = train_and_evaluate_rf(X_train, y_train, X_test, y_test, is_multiclass, env_info)
    algorithm_results.append(rf_res)
    print(f"      -> F1: {rf_res['f1']:.4f} | Recall: {rf_res['recall']:.4f} | ROC-AUC: {rf_res['roc_auc']} | Train Time: {rf_res['training_time_sec']:.2f}s | Device: {rf_res['device_used']}")

    # 2. XGBoost
    print("\n[2/4] Training XGBoost (100 estimators, depth=6, eta=0.1)...")
    xgb_res = train_and_evaluate_xgb(X_train, y_train, X_test, y_test, is_multiclass, env_info)
    algorithm_results.append(xgb_res)
    print(f"      -> F1: {xgb_res['f1']:.4f} | Recall: {xgb_res['recall']:.4f} | ROC-AUC: {xgb_res['roc_auc']} | Train Time: {xgb_res['training_time_sec']:.2f}s | Device: {xgb_res['device_used']}")

    # 3. LightGBM
    print("\n[3/4] Training LightGBM (100 estimators, GOSS histogram, depth=6)...")
    lgb_res = train_and_evaluate_lgb(X_train, y_train, X_test, y_test, is_multiclass, env_info)
    algorithm_results.append(lgb_res)
    print(f"      -> F1: {lgb_res['f1']:.4f} | Recall: {lgb_res['recall']:.4f} | ROC-AUC: {lgb_res['roc_auc']} | Train Time: {lgb_res['training_time_sec']:.2f}s | Device: {lgb_res['device_used']}")

    # 4. CatBoost
    print("\n[4/4] Training CatBoost (100 iterations, oblivious decision trees, depth=6)...")
    cb_res = train_and_evaluate_catboost(X_train, y_train, X_test, y_test, is_multiclass, env_info)
    algorithm_results.append(cb_res)
    print(f"      -> F1: {cb_res['f1']:.4f} | Recall: {cb_res['recall']:.4f} | ROC-AUC: {cb_res['roc_auc']} | Train Time: {cb_res['training_time_sec']:.2f}s | Device: {cb_res['device_used']}")

    # -------------------------------------------------------------------------
    # Comparison Table & Model Selection
    # -------------------------------------------------------------------------
    print("\n" + "=" * 82)
    print(f"STANDARDIZED COMPARISON TABLE — {dataset_name.upper()}")
    print("=" * 82)
    header = f"{'MODEL':<16} {'ACCURACY':<10} {'PRECISION':<11} {'RECALL':<9} {'F1':<9} {'ROC-AUC':<9} {'FPR':<9} {'TRAIN TIME':<11}"
    print(header)
    print("-" * 82)

    for r in algorithm_results:
        roc_str = f"{r['roc_auc']:.4f}" if isinstance(r['roc_auc'], (int, float)) else str(r['roc_auc'])
        row = (
            f"{r['algorithm']:<16} "
            f"{r['accuracy']:<10.4f} "
            f"{r['precision']:<11.4f} "
            f"{r['recall']:<9.4f} "
            f"{r['f1']:<9.4f} "
            f"{roc_str:<9} "
            f"{r['fpr']:<9.4f} "
            f"{r['training_time_sec']:<9.2f}s"
        )
        print(row)

    print("-" * 82)

    # Primary Ranking: 1. F1, 2. Recall, 3. ROC-AUC
    def sort_key(res: Dict[str, Any]):
        roc_val = res['roc_auc'] if isinstance(res['roc_auc'], (int, float)) else 0.0
        return (res['f1'], res['recall'], roc_val)

    sorted_results = sorted(algorithm_results, key=sort_key, reverse=True)
    best_overall = sorted_results[0]['algorithm']

    # Operational Bound Winners (Binary datasets only)
    if not is_multiclass:
        best_fpr_1pct = max(
            algorithm_results,
            key=lambda r: (r.get("fpr_1pct_metrics", {}).get("f1_at_fpr_1pct", 0), r.get("fpr_1pct_metrics", {}).get("recall_at_fpr_1pct", 0))
        )["algorithm"]

        best_fpr_01pct = max(
            algorithm_results,
            key=lambda r: (r.get("fpr_01pct_metrics", {}).get("f1_at_fpr_01pct", 0), r.get("fpr_01pct_metrics", {}).get("recall_at_fpr_01pct", 0))
        )["algorithm"]
    else:
        best_fpr_1pct = best_overall
        best_fpr_01pct = best_overall

    try:
        print(f"\n🏆 BEST OVERALL MODEL            : {best_overall}")
        if not is_multiclass:
            print(f"🏆 BEST MODEL UNDER FPR <= 1%     : {best_fpr_1pct}")
            print(f"🏆 BEST MODEL UNDER FPR <= 0.1%   : {best_fpr_01pct}")
    except Exception:
        print(f"\n[WINNER] BEST OVERALL MODEL      : {best_overall}")
        if not is_multiclass:
            print(f"[WINNER] BEST UNDER FPR <= 1%    : {best_fpr_1pct}")
            print(f"[WINNER] BEST UNDER FPR <= 0.1%  : {best_fpr_01pct}")
    print("=" * 82)

    benchmark_payload = {
        "dataset_name": dataset_name,
        "validation_strategy": partition_desc,
        "is_multiclass": is_multiclass,
        "target_column": target_col,
        "num_features": len(feature_names),
        "num_train_samples": X_train.shape[0],
        "num_test_samples": X_test.shape[0],
        "best_overall_model": best_overall,
        "best_model_under_fpr_1pct": best_fpr_1pct,
        "best_model_under_fpr_01pct": best_fpr_01pct,
        "algorithm_results": algorithm_results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    json_path = RESULTS_DIR / f"{dataset_name}_benchmark.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_payload, f, indent=2)
    print(f"[Artifact Saved] {json_path}")

    return benchmark_payload


def generate_all_datasets_comparison_csv(all_results: List[Dict[str, Any]]) -> Path:
    """Combines benchmark records across all datasets into all_datasets_comparison.csv."""
    rows = []
    for res in all_results:
        ds = res["dataset_name"]
        strat = res.get("validation_strategy", "Standard")
        for alg in res["algorithm_results"]:
            rows.append({
                "Dataset": ds,
                "Validation_Strategy": strat,
                "Algorithm": alg["algorithm"],
                "Device": alg["device_used"],
                "Accuracy": alg["accuracy"],
                "Precision": alg["precision"],
                "Recall": alg["recall"],
                "F1_Score": alg["f1"],
                "ROC_AUC": alg["roc_auc"],
                "PR_AUC": alg["pr_auc"],
                "FPR": alg["fpr"],
                "FNR": alg["fnr"],
                "Train_Time_Sec": alg["training_time_sec"],
                "Inference_Time_Sec": alg["inference_time_sec"],
                "Inference_Per_Sample_us": alg["inference_per_sample_us"],
                "Num_Features": alg["num_features"],
                "Num_Train_Samples": alg["num_train_samples"],
                "Num_Test_Samples": alg["num_test_samples"],
            })

    df_comp = pd.DataFrame(rows)
    csv_path = RESULTS_DIR / "all_datasets_comparison.csv"
    df_comp.to_csv(csv_path, index=False)
    print(f"\n[Combined Comparison CSV Generated] {csv_path}")
    return csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="NetraGraph Rigorous Multi-Algorithm ML Benchmark")
    parser.add_argument(
        "--dataset",
        choices=["cicids2018", "cicids2017", "cicddos2019", "unsw", "malwarebazaar", "all"],
        default="all",
        help="Specify dataset to benchmark, or 'all' to run the full benchmark suite.",
    )
    args = parser.parse_args()

    env_info = detect_system_environment()
    print_environment_banner(env_info)

    datasets_to_run = (
        ["cicids2018", "cicids2017", "cicddos2019", "unsw", "malwarebazaar"]
        if args.dataset == "all"
        else [args.dataset]
    )

    all_benchmark_results = []
    for ds in datasets_to_run:
        res = run_benchmark_for_dataset(ds, env_info)
        all_benchmark_results.append(res)

    if len(all_benchmark_results) > 1 or args.dataset == "all":
        generate_all_datasets_comparison_csv(all_benchmark_results)

    print("\n" + "=" * 82)
    print("ALL RIGOROUS BENCHMARKS COMPLETED SUCCESSFULLY")
    print("=" * 82)


if __name__ == "__main__":
    main()
