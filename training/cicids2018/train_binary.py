"""GPU-Accelerated Binary Training Pipeline for CSE-CIC-IDS2018."""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

# Add training folder and backend to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import (
    BINARY_LABEL_MAPPING,
    DEFAULT_DATA_DIR,
    DEFAULT_OUTPUT_DIR,
    LEAKAGE_COLUMNS,
    LOCAL_ARTIFACT_DIR,
    PRIMARY_TARGET,
    TrainingConfig,
)
from evaluate import compute_cybersecurity_metrics, print_evaluation_summary
from prepare_data import load_and_merge_cicids2018_files, prepare_cicids2018_features
from threshold_analysis import print_threshold_summary, sweep_decision_thresholds
from utils import calculate_sha256, detect_hardware, print_hardware_status


def train_cicids2018_binary(config: TrainingConfig) -> Path:
    """Executes end-to-end binary training, threshold optimization, and artifact bundling."""
    print("\n" + "=" * 70)
    print("  NETRAGRAPH CSE-CIC-IDS2018 BINARY GPU TRAINING PIPELINE")
    print("=" * 70)

    # 1. Hardware Inspection
    hw_info = detect_hardware(requested_device=config.device)
    print_hardware_status(hw_info)
    training_device = hw_info["training_device"]

    # 2. Data Loading, Schema Harmonization (80 vs 84 cols), and Sanitization
    df, audit_report = load_and_merge_cicids2018_files(
        config.data_dir,
        subsample_ratio=config.subsample_ratio,
        use_cache=config.use_parquet_cache,
    )
    X_train, y_train, X_test, y_test, preprocessor, feature_names = prepare_cicids2018_features(
        df, target_mode="binary"
    )

    # 3. Model Selection & Instantiation
    print(f"\n[Trainer] Initializing Binary Classifier on {training_device}...")
    use_catboost = False
    try:
        from catboost import CatBoostClassifier
        use_catboost = True
    except ImportError:
        print("  [INFO] CatBoost not found. Falling back to Scikit-Learn RandomForestClassifier.")

    if use_catboost:
        cb_params = {
            "iterations": config.iterations,
            "depth": config.depth,
            "learning_rate": config.learning_rate,
            "random_seed": config.random_seed,
            "loss_function": "Logloss",
            "eval_metric": "Logloss",
            "task_type": training_device,
            "verbose": 100,
        }
        if config.early_stopping_rounds:
            cb_params["early_stopping_rounds"] = config.early_stopping_rounds
        if config.auto_class_weights:
            cb_params["auto_class_weights"] = config.auto_class_weights

        model = CatBoostClassifier(**cb_params)
        model_type_name = "CatBoostClassifier"
    else:
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(
            n_estimators=min(config.iterations, 150),
            max_depth=config.depth * 2,
            random_state=config.random_seed,
            class_weight="balanced",
            n_jobs=-1,
        )
        model_type_name = "RandomForestClassifier"

    # 4. Transform Feature Matrices
    print(f"[Trainer] Preprocessing feature matrix ({X_train.shape[0]:,} train samples, {X_test.shape[0]:,} test samples)...")
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)

    # 5. Fit Estimator
    print(f"[Trainer] Fitting {model_type_name}...")
    if use_catboost:
        model.fit(X_train_trans, y_train, eval_set=(X_test_trans, y_test), use_best_model=True)
    else:
        model.fit(X_train_trans, y_train)

    print("  [PASS] Model fitting completed successfully.")

    # 6. Metric Evaluation & Threshold Optimization Sweep
    y_pred = model.predict(X_test_trans)
    y_proba = model.predict_proba(X_test_trans) if hasattr(model, "predict_proba") else None
    metrics = compute_cybersecurity_metrics(y_test, y_pred, y_proba)
    print_evaluation_summary(metrics, title="CSE-CIC-IDS2018 BINARY EVALUATION (TEST SET)")

    if y_proba is not None:
        threshold_results = sweep_decision_thresholds(y_test, y_proba)
        print_threshold_summary(threshold_results)
        metrics["threshold_analysis"] = {
            "best_f1_threshold": threshold_results["best_f1_threshold"],
            "best_f1_metrics": threshold_results["best_f1_metrics"],
            "fpr_constrained_threshold": threshold_results["fpr_constrained_threshold"],
            "fpr_constrained_metrics": threshold_results["fpr_constrained_metrics"],
        }

    # 7. Package NetraGraph-Compliant Versioned Artifact Bundles
    destinations = [
        PROJECT_ROOT / config.output_dir,
    ]
    if config.save_local_artifact:
        destinations.append(LOCAL_ARTIFACT_DIR)

    for dest in destinations:
        dest.mkdir(parents=True, exist_ok=True)
        print(f"[Artifact Packager] Persisting bundle to: {dest}")

        joblib.dump(model, dest / "model.joblib")
        joblib.dump(preprocessor, dest / "preprocessor.joblib")

        # Feature schema
        schema_payload = {
            "feature_names": feature_names,
            "dtypes": {name: str(X_train[name].dtype) for name in feature_names},
            "target_column": PRIMARY_TARGET,
            "task_mode": "binary",
        }
        (dest / "feature_schema.json").write_text(json.dumps(schema_payload, indent=2), encoding="utf-8")

        # Labels
        (dest / "label_mapping.json").write_text(json.dumps(BINARY_LABEL_MAPPING, indent=2), encoding="utf-8")

        # Metrics
        (dest / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        # Metadata
        metadata = {
            "model_name": config.model_name,
            "model_type": model_type_name,
            "model_version": config.model_version,
            "task_domain": "Network Anomaly & Intrusion Detection (CIC-IDS2018)",
            "training_timestamp": datetime.now(timezone.utc).isoformat(),
            "training_device": training_device,
            "gpu_hardware": hw_info["gpu_name"],
            "dataset_name": "CSE-CIC-IDS2018 Network Intrusion Dataset",
            "training_rows": len(X_train),
            "testing_rows": len(X_test),
            "feature_count": len(feature_names),
            "hyperparameters": {
                "iterations": config.iterations,
                "depth": config.depth,
                "learning_rate": config.learning_rate,
                "random_seed": config.random_seed,
            },
            "framework_versions": {
                "python": platform.python_version(),
                "scikit-learn": __import__("sklearn").__version__,
                "pandas": pd.__version__,
                "numpy": np.__version__,
                "joblib": joblib.__version__,
            },
            "training_metrics": metrics,
        }
        (dest / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Requirements
        reqs = f"scikit-learn=={__import__('sklearn').__version__}\njoblib=={joblib.__version__}\npandas=={pd.__version__}\nnumpy=={np.__version__}\n"
        if use_catboost:
            reqs += f"catboost>={__import__('catboost').__version__}\n"
        (dest / "requirements_model.txt").write_text(reqs, encoding="utf-8")

        # Forensic Report
        training_report = {
            "model_name": config.model_name,
            "model_version": config.model_version,
            "dataset_source": str(config.data_dir),
            "training_device": training_device,
            "gpu_name": hw_info["gpu_name"],
            "features_used": feature_names,
            "dropped_leakage_columns": audit_report.dropped_leakage_columns,
            "evaluation_metrics": metrics,
        }
        (dest / "training_report.json").write_text(json.dumps(training_report, indent=2), encoding="utf-8")

    primary_dir = destinations[0]
    sha256_hash = calculate_sha256(primary_dir / "model.joblib")
    print(f"\n[Verification] Model Artifact SHA-256: {sha256_hash}")
    print(f"[Verification] Primary Artifact Bundle: {primary_dir}")
    print("=" * 70 + "\n")

    return primary_dir


def main():
    parser = argparse.ArgumentParser(description="CSE-CIC-IDS2018 Binary Model Training Tool")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Path to CIC-IDS2018 dataset directory")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output artifact directory")
    parser.add_argument("--device", default="auto", choices=["auto", "gpu", "cpu"], help="Compute device")
    parser.add_argument("--iterations", type=int, default=1200, help="Training iterations")
    parser.add_argument("--depth", type=int, default=6, help="Tree depth")
    parser.add_argument("--lr", type=float, default=0.05, help="Learning rate")
    parser.add_argument("--subsample", type=float, default=None, help="Subsample ratio for prototyping")
    args = parser.parse_args()

    cfg = TrainingConfig(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        device=args.device,
        iterations=args.iterations,
        depth=args.depth,
        learning_rate=args.lr,
        subsample_ratio=args.subsample,
    )
    train_cicids2018_binary(cfg)


if __name__ == "__main__":
    main()
