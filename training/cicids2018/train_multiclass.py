"""GPU-Accelerated Multi-Class Attack Taxonomy Classifier for CSE-CIC-IDS2018."""
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
    DEFAULT_DATA_DIR,
    MULTICLASS_ATTACK_CATEGORIES,
    PRIMARY_TARGET,
    TrainingConfig,
)
from evaluate import compute_cybersecurity_metrics, print_evaluation_summary
from prepare_data import load_and_merge_cicids2018_files, prepare_cicids2018_features
from utils import calculate_sha256, detect_hardware, print_hardware_status


def train_cicids2018_multiclass(config: TrainingConfig) -> Path:
    """Trains a multi-class CatBoost model to distinguish 15 distinct attack types."""
    print("\n" + "=" * 70)
    print("  NETRAGRAPH CSE-CIC-IDS2018 MULTI-CLASS GPU TRAINING PIPELINE")
    print("=" * 70)

    hw_info = detect_hardware(requested_device=config.device)
    print_hardware_status(hw_info)
    training_device = hw_info["training_device"]

    df, audit_report = load_and_merge_cicids2018_files(
        config.data_dir,
        subsample_ratio=config.subsample_ratio,
        use_cache=config.use_parquet_cache,
    )
    X_train, y_train, X_test, y_test, preprocessor, feature_names = prepare_cicids2018_features(
        df, target_mode="multiclass"
    )

    print(f"\n[Trainer] Initializing Multi-Class Classifier on {training_device}...")
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
            "loss_function": "MultiClass",
            "eval_metric": "MultiClass",
            "task_type": training_device,
            "verbose": 100,
        }
        if config.early_stopping_rounds:
            cb_params["early_stopping_rounds"] = config.early_stopping_rounds

        model = CatBoostClassifier(**cb_params)
        model_type_name = "CatBoostClassifier (MultiClass)"
    else:
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(
            n_estimators=min(config.iterations, 150),
            max_depth=config.depth * 2,
            random_state=config.random_seed,
            n_jobs=-1,
        )
        model_type_name = "RandomForestClassifier (MultiClass)"

    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)

    print(f"[Trainer] Fitting {model_type_name} across 15 attack taxonomy classes...")
    if use_catboost:
        model.fit(X_train_trans, y_train, eval_set=(X_test_trans, y_test), use_best_model=True)
    else:
        model.fit(X_train_trans, y_train)

    print("  [PASS] Multi-class model fitting completed successfully.")

    y_pred = model.predict(X_test_trans)
    y_proba = model.predict_proba(X_test_trans) if hasattr(model, "predict_proba") else None
    metrics = compute_cybersecurity_metrics(y_test, y_pred, y_proba, is_multiclass=True)
    print_evaluation_summary(metrics, title="CSE-CIC-IDS2018 MULTI-CLASS EVALUATION")

    # Invert mapping for analyst labels
    int_to_name = {str(v): k for k, v in MULTICLASS_ATTACK_CATEGORIES.items()}

    output_dir = PROJECT_ROOT / config.output_dir if config.output_dir != str(DEFAULT_DATA_DIR) else PROJECT_ROOT / "artifacts" / "network-intrusion-cicids2018-multiclass" / "v1"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Artifact Packager] Persisting multi-class bundle to: {output_dir}")

    joblib.dump(model, output_dir / "model.joblib")
    joblib.dump(preprocessor, output_dir / "preprocessor.joblib")

    schema_payload = {
        "feature_names": feature_names,
        "dtypes": {name: str(X_train[name].dtype) for name in feature_names},
        "target_column": PRIMARY_TARGET,
        "task_mode": "multiclass",
    }
    (output_dir / "feature_schema.json").write_text(json.dumps(schema_payload, indent=2), encoding="utf-8")
    (output_dir / "label_mapping.json").write_text(json.dumps(int_to_name, indent=2), encoding="utf-8")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    metadata = {
        "model_name": "network-intrusion-cicids2018-multiclass",
        "model_type": model_type_name,
        "model_version": "v1",
        "task_domain": "Multi-Class Network Threat Taxonomy (CIC-IDS2018)",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "training_device": training_device,
        "gpu_hardware": hw_info["gpu_name"],
        "dataset_name": "CSE-CIC-IDS2018 Multi-Class Attack Dataset",
        "training_rows": len(X_train),
        "testing_rows": len(X_test),
        "feature_count": len(feature_names),
        "class_categories": MULTICLASS_ATTACK_CATEGORIES,
        "training_metrics": metrics,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    reqs = f"scikit-learn=={__import__('sklearn').__version__}\njoblib=={joblib.__version__}\npandas=={pd.__version__}\nnumpy=={np.__version__}\n"
    if use_catboost:
        reqs += f"catboost>={__import__('catboost').__version__}\n"
    (output_dir / "requirements_model.txt").write_text(reqs, encoding="utf-8")

    sha256_hash = calculate_sha256(output_dir / "model.joblib")
    print(f"\n[Verification] Multi-Class Artifact SHA-256: {sha256_hash}")
    print("=" * 70 + "\n")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="CSE-CIC-IDS2018 Multi-Class Training Tool")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Path to CIC-IDS2018 dataset directory")
    parser.add_argument("--device", default="auto", choices=["auto", "gpu", "cpu"], help="Compute device")
    parser.add_argument("--iterations", type=int, default=1200, help="Training iterations")
    parser.add_argument("--subsample", type=float, default=None, help="Subsample ratio for prototyping")
    args = parser.parse_args()

    cfg = TrainingConfig(
        data_dir=args.data_dir,
        device=args.device,
        iterations=args.iterations,
        subsample_ratio=args.subsample,
    )
    train_cicids2018_multiclass(cfg)


if __name__ == "__main__":
    main()
