"""Comprehensive Metric Evaluation and Cybersecurity Forensics for UNSW-NB15."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

# Add training folder and backend to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def compute_cybersecurity_metrics(
    y_true: np.ndarray | pd.Series | list,
    y_pred: np.ndarray | pd.Series | list,
    y_proba: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Computes standard ML and specialized cybersecurity operational metrics (FPR, FNR)."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = 0, 0, 0, 0
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    else:
        fpr, fnr = 0.0, 0.0

    acc = float(accuracy_score(y_true, y_pred))
    prec_bin = float(precision_score(y_true, y_pred, average="binary", zero_division=0))
    rec_bin = float(recall_score(y_true, y_pred, average="binary", zero_division=0))
    f1_bin = float(f1_score(y_true, y_pred, average="binary", zero_division=0))
    f1_weighted = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    metrics: Dict[str, Any] = {
        "accuracy": acc,
        "precision_binary": prec_bin,
        "recall_binary": rec_bin,
        "f1_binary": f1_bin,
        "f1_weighted": f1_weighted,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(y_true, y_pred, output_dict=True, zero_division=0),
    }

    if y_proba is not None:
        try:
            # Handle 1D or 2D probability outputs
            proba_positive = y_proba[:, 1] if y_proba.ndim == 2 else y_proba
            metrics["roc_auc"] = float(roc_auc_score(y_true, proba_positive))
            metrics["pr_auc"] = float(average_precision_score(y_true, proba_positive))
        except Exception as exc:
            metrics["roc_auc_error"] = str(exc)

    return metrics


def print_evaluation_summary(metrics: Dict[str, Any], title: str = "UNSW-NB15 MODEL EVALUATION") -> None:
    """Prints clear, analyst-ready evaluation banner emphasizing FPR & FNR."""
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)
    print(f"  Accuracy                : {metrics['accuracy'] * 100:.2f}%")
    print(f"  F1 Score (Binary)       : {metrics['f1_binary'] * 100:.2f}%")
    print(f"  Precision (Binary)      : {metrics['precision_binary'] * 100:.2f}%")
    print(f"  Recall (Binary)         : {metrics['recall_binary'] * 100:.2f}%")
    if "roc_auc" in metrics:
        print(f"  ROC-AUC Score           : {metrics['roc_auc']:.4f}")
    if "pr_auc" in metrics:
        print(f"  PR-AUC Score            : {metrics['pr_auc']:.4f}")
    print("-----------------------------------------------------------------")
    print("  CYBERSECURITY OPERATIONAL THREAT METRICS:")
    print(f"  False Positive Rate (FPR): {metrics['false_positive_rate'] * 100:.3f}% (Alert Fatigue Impact)")
    print(f"  False Negative Rate (FNR): {metrics['false_negative_rate'] * 100:.3f}% (Missed Intrusion Risk)")
    print("-----------------------------------------------------------------")
    print(f"  Confusion Matrix        : TN={metrics['true_negatives']:,} | FP={metrics['false_positives']:,}")
    print(f"                            FN={metrics['false_negatives']:,} | TP={metrics['true_positives']:,}")
    print("=" * 65 + "\n")


def evaluate_saved_artifact(artifact_dir: str | Path, test_csv_path: Optional[str | Path] = None) -> Dict[str, Any]:
    """Loads a saved NetraGraph artifact bundle and evaluates on test data."""
    import joblib
    loc = Path(artifact_dir)
    print(f"[Evaluator] Loading model artifact from: {loc}")

    schema = json.loads((loc / "feature_schema.json").read_text(encoding="utf-8"))
    model = joblib.load(loc / "model.joblib")
    preprocessor = joblib.load(loc / "preprocessor.joblib")

    if test_csv_path:
        test_df = pd.read_csv(test_csv_path)
        target_col = schema.get("target_column", "label")
        X = test_df[[c for c in schema["feature_names"] if c in test_df.columns]]
        y_true = test_df[target_col].astype(int)

        X_trans = preprocessor.transform(X)
        y_pred = model.predict(X_trans)
        y_proba = model.predict_proba(X_trans) if hasattr(model, "predict_proba") else None

        metrics = compute_cybersecurity_metrics(y_true, y_pred, y_proba)
        print_evaluation_summary(metrics, title=f"EVALUATION FOR {loc.name}")
        return metrics
    else:
        metrics = json.loads((loc / "metrics.json").read_text(encoding="utf-8"))
        print_evaluation_summary(metrics, title=f"SAVED ARTIFACT METRICS ({loc.name})")
        return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate UNSW-NB15 Model Artifact")
    parser.add_argument("--artifact", required=True, help="Path to versioned artifact directory")
    parser.add_argument("--test-data", default=None, help="Optional test CSV dataset path")
    args = parser.parse_args()

    evaluate_saved_artifact(args.artifact, args.test_data)


if __name__ == "__main__":
    main()
