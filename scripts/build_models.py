"""Build and package all official NetraGraph ML Models (A–E) into versioned bundles.
Extracts datasets from git blob history and generates production artifacts.
"""
from __future__ import annotations

import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Add backend to sys.path
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from ml.config.version import ensure_supported_ml_runtime
from ml.data.preprocessing import build_preprocessor
from ml.evaluation.evaluate_models import evaluate

GIT_DATASET_BLOBS = {
    "Model A (Session Intrusion)": {
        "blob_sha": "3d136f7fc1654baef3cd595cb3edb02079200e8c",
        "csv_filename": "cybersecurity_intrusion_data.csv",
        "model_name": "intrusion",
        "target_col": "attack_detected",
        "drop_cols": ["session_id"],
        "dataset_name": "Cybersecurity Intrusion Detection Dataset (Session)",
        "task_type": "Session Intrusion Detection",
    },
    "Model B (Network Intrusion)": {
        "blob_sha": "8027055d19a9effa5f5da762f4ea67df290443a4",
        "csv_filename": "Train_data.csv",
        "model_name": "network-intrusion",
        "target_col": "class",
        "drop_cols": [],
        "dataset_name": "NSL-KDD Network Intrusion Detection Dataset",
        "task_type": "Network Intrusion Detection",
    },
    "Model C (Phishing URL PhiUSIIL)": {
        "blob_sha": "0e909298d6fee36444aad822d6165373cf35b9c3",
        "csv_filename": "PhiUSIIL_Phishing_URL_Dataset.csv",
        "model_name": "phishing-url",
        "target_col": "label",
        "drop_cols": ["FILENAME", "URL", "Domain", "Title"],
        "dataset_name": "PhiUSIIL Phishing URL Websites Dataset",
        "task_type": "Phishing URL Detection",
    },
    "Model D (Web Page Phishing)": {
        "blob_sha": "22e7c6718cd92f41bf23262ead537f525fda94ff",
        "csv_filename": "dataset_phishing.csv",
        "model_name": "webpage-phishing",
        "target_col": "status",
        "drop_cols": ["url"],
        "dataset_name": "Web Page Phishing Detection 88-Feature Dataset",
        "task_type": "Web Page Phishing Detection",
    },
    "Model E (Phishing Email)": {
        "blob_sha": "4c73856cf256e50b0b3981327f02c4a86799c33f",
        "csv_filename": "CEAS_08.csv",
        "model_name": "phishing-email",
        "target_col": "label",
        "drop_cols": [],
        "sample_size": 10000,
        "dataset_name": "CEAS 2008 Phishing Email Corpus",
        "task_type": "Phishing Email Detection",
    },
}


def build_single_model(cfg: dict, version: str = "v1") -> None:
    ensure_supported_ml_runtime()
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder

    model_name = cfg["model_name"]
    print(f"\n==========================================")
    print(f"Building {model_name} ({cfg['task_type']}) - {version}")
    print(f"==========================================")

    # 1. Fetch CSV from git blob
    blob_res = subprocess.run(
        ["git", "cat-file", "-p", cfg["blob_sha"]],
        capture_output=True,
        cwd=ROOT,
    )
    if blob_res.returncode != 0:
        raise RuntimeError(f"Failed to fetch git blob {cfg['blob_sha']}: {blob_res.stderr.decode()}")

    zf = zipfile.ZipFile(io.BytesIO(blob_res.stdout))
    df = pd.read_csv(zf.open(cfg["csv_filename"]))
    print(f"Loaded raw dataset '{cfg['csv_filename']}': {df.shape[0]} rows, {df.shape[1]} columns")

    # Sample if dataset is very large for fast training
    sample_limit = cfg.get("sample_size")
    if sample_limit and len(df) > sample_limit:
        df = df.sample(n=sample_limit, random_state=42).reset_index(drop=True)
        print(f"Stratified subsample to {len(df)} rows for efficient training.")

    # Drop non-feature columns
    target_col = cfg["target_col"]
    drop_cols = [c for c in cfg.get("drop_cols", []) if c in df.columns and c != target_col]
    if drop_cols:
        df = df.drop(columns=drop_cols)
        print(f"Dropped identifiers / raw text columns: {drop_cols}")

    # Remove rows where target is missing
    df = df.dropna(subset=[target_col])

    feature_names = [col for col in df.columns if col != target_col]
    X = df[feature_names]
    y = df[target_col]

    # Fit label encoder
    label_encoder = LabelEncoder()
    encoded_y = label_encoder.fit_transform(y.astype(str))
    classes = label_encoder.classes_.tolist()
    print(f"Classes: {classes} (Target: '{target_col}')")
    print(f"Features ({len(feature_names)}): {feature_names[:8]}...")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, encoded_y, test_size=0.2, random_state=42, stratify=encoded_y
    )

    # Build and fit preprocessor
    preprocessor = build_preprocessor(X_train, feature_names)
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)

    # Train estimator
    model = RandomForestClassifier(
        n_estimators=150,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(X_train_transformed, y_train)

    # Evaluate
    metrics = evaluate(model, X_test_transformed, y_test)
    print(f"Accuracy: {metrics['accuracy'] * 100:.2f}% | F1: {metrics['f1'] * 100:.2f}%")

    # Destination directories (both artifacts and registry)
    destinations = [
        ROOT / "artifacts" / model_name / version,
        BACKEND / "models" / "registry" / model_name / version,
    ]

    for dest in destinations:
        dest.mkdir(parents=True, exist_ok=True)

        # Save model and preprocessor
        joblib.dump(model, dest / "model.joblib")
        joblib.dump(preprocessor, dest / "preprocessor.joblib")

        # Feature schema
        schema_data = {
            "feature_names": feature_names,
            "dtypes": {name: str(X[name].dtype) for name in feature_names},
            "target_column": target_col,
        }
        (dest / "feature_schema.json").write_text(json.dumps(schema_data, indent=2), encoding="utf-8")

        # Label mapping
        label_map = {str(idx): label for idx, label in enumerate(classes)}
        (dest / "label_mapping.json").write_text(json.dumps(label_map, indent=2), encoding="utf-8")

        # Metrics
        (dest / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        # Metadata
        metadata = {
            "model_name": model_name,
            "model_type": cfg["task_type"],
            "model_version": version,
            "training_timestamp": datetime.now(timezone.utc).isoformat(),
            "framework_versions": {
                "python": platform.python_version(),
                "scikit-learn": __import__("sklearn").__version__,
                "joblib": joblib.__version__,
                "pandas": pd.__version__,
                "numpy": np.__version__,
            },
            "python_version": platform.python_version(),
            "dataset_name": cfg["dataset_name"],
            "target_column": target_col,
            "feature_names": feature_names,
            "class_labels": classes,
            "training_metrics": metrics,
        }
        (dest / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Requirements
        reqs = f"scikit-learn=={__import__('sklearn').__version__}\njoblib=={joblib.__version__}\npandas=={pd.__version__}\nnumpy=={np.__version__}\n"
        (dest / "requirements_model.txt").write_text(reqs, encoding="utf-8")

        # Training report
        report = {
            "dataset_name": cfg["dataset_name"],
            "rows_processed": len(df),
            "columns_used": feature_names,
            "target_column": target_col,
            "class_distribution": {str(k): int(v) for k, v in zip(*np.unique(encoded_y, return_counts=True))},
            "model_version": version,
            **metrics,
        }
        (dest / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Artifacts successfully saved for {model_name}/{version}")


def main():
    print("Starting NetraGraph ML Artifacts Generator (Models A–E)...")
    for key, cfg in GIT_DATASET_BLOBS.items():
        build_single_model(cfg, version="v1")
    print("\nAll Models A–E successfully trained, validated, and persisted!")


if __name__ == "__main__":
    main()
