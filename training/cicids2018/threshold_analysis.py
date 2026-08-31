"""Decision Threshold Optimization & FPR Constraint Sweeper for Network Intrusion Detection."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

# Add training folder and backend to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def sweep_decision_thresholds(
    y_true: np.ndarray | pd.Series,
    y_proba: np.ndarray,
    thresholds: Optional[np.ndarray] = None,
    target_fpr_limit: float = 0.001,  # 0.1% max false alarm rate
) -> Dict[str, Any]:
    """Sweeps decision thresholds from 0.01 to 0.99 to find optimal F1 and FPR-constrained operating points."""
    y_true = np.array(y_true)
    proba_pos = y_proba[:, 1] if y_proba.ndim == 2 else y_proba
    thresh_array = thresholds if thresholds is not None else np.linspace(0.01, 0.99, 99)

    records: List[Dict[str, Any]] = []
    best_f1 = -1.0
    best_f1_threshold = 0.5
    best_f1_metrics = {}

    fpr_constrained_threshold: Optional[float] = None
    fpr_constrained_metrics: Optional[Dict[str, Any]] = None

    for tau in thresh_array:
        y_pred = (proba_pos >= tau).astype(int)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        record = {
            "threshold": round(float(tau), 3),
            "f1": round(f1, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "fpr": round(fpr, 5),
            "fnr": round(fnr, 5),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
        }
        records.append(record)

        if f1 > best_f1:
            best_f1 = f1
            best_f1_threshold = float(tau)
            best_f1_metrics = record

        # Find highest recall where FPR is below operational constraint limit
        if fpr <= target_fpr_limit:
            if fpr_constrained_metrics is None or rec > fpr_constrained_metrics["recall"]:
                fpr_constrained_threshold = float(tau)
                fpr_constrained_metrics = record

    results = {
        "best_f1_threshold": round(best_f1_threshold, 3),
        "best_f1_metrics": best_f1_metrics,
        "default_0_5_metrics": [r for r in records if abs(r["threshold"] - 0.5) < 0.015][0] if records else {},
        "fpr_constrained_threshold": round(fpr_constrained_threshold, 3) if fpr_constrained_threshold else None,
        "fpr_constrained_metrics": fpr_constrained_metrics or {},
        "target_fpr_limit": target_fpr_limit,
        "sweep_samples": records,
    }

    return results


def print_threshold_summary(results: Dict[str, Any]) -> None:
    """Prints comparative table between default 0.5 threshold and optimized operational thresholds."""
    def_m = results["default_0_5_metrics"]
    opt_m = results["best_f1_metrics"]
    fpr_m = results["fpr_constrained_metrics"]

    print("\n" + "=" * 70)
    print("  DECISION THRESHOLD FORENSIC OPTIMIZATION")
    print("=" * 70)
    best_t_str = f"Best F1 (t={results['best_f1_threshold']})"
    fpr_t_str = f"FPR<={results['target_fpr_limit']*100:.1f}% (t={results.get('fpr_constrained_threshold', 'N/A')})"
    print(f"{'Metric':<24} | {'Default (t=0.50)':<16} | {best_t_str:<18} | {fpr_t_str}")
    print("-" * 70)
    print(f"{'F1 Score':<24} | {def_m.get('f1', 0)*100:6.2f}%          | {opt_m.get('f1', 0)*100:6.2f}%            | {fpr_m.get('f1', 0)*100:6.2f}%")
    print(f"{'Precision':<24} | {def_m.get('precision', 0)*100:6.2f}%          | {opt_m.get('precision', 0)*100:6.2f}%            | {fpr_m.get('precision', 0)*100:6.2f}%")
    print(f"{'Recall':<24} | {def_m.get('recall', 0)*100:6.2f}%          | {opt_m.get('recall', 0)*100:6.2f}%            | {fpr_m.get('recall', 0)*100:6.2f}%")
    print(f"{'False Positive Rate':<24} | {def_m.get('fpr', 0)*100:6.3f}%          | {opt_m.get('fpr', 0)*100:6.3f}%            | {fpr_m.get('fpr', 0)*100:6.3f}%")
    print(f"{'False Negative Rate':<24} | {def_m.get('fnr', 0)*100:6.3f}%          | {opt_m.get('fnr', 0)*100:6.3f}%            | {fpr_m.get('fnr', 0)*100:6.3f}%")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Threshold Analysis Tool for CIC-IDS2018")
    parser.add_argument("--artifact", required=True, help="Path to versioned artifact directory")
    args = parser.parse_args()

    import joblib
    loc = Path(args.artifact)
    metrics_path = loc / "metrics.json"
    if metrics_path.exists():
        print(f"[Threshold Analyzer] Threshold audit metadata available in {metrics_path}")


if __name__ == "__main__":
    main()
