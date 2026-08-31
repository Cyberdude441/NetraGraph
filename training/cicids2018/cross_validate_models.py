"""Cross-Dataset Model Bridge: Multi-Dataset Evaluation across NSL-KDD, UNSW-NB15, and CIC-IDS2018."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

from evaluate import compute_cybersecurity_metrics, print_evaluation_summary

MODEL_B_DIR = PROJECT_ROOT / "backend" / "models" / "registry" / "network-intrusion" / "v1"
MODEL_UNSW_DIR = PROJECT_ROOT / "artifacts" / "network-anomaly-unsw" / "v1"


def align_cicids_to_model_b_schema(
    cic_df: pd.DataFrame,
    schema: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Maps CIC-IDS2018 flow statistics to Model B (NSL-KDD) input schema."""
    target_features = schema["feature_names"]
    aligned = {}
    report = {"mapped": {}, "unmapped": []}

    # Semantic mapping dictionary
    mapping = {
        "duration": "Flow Duration",
        "src_bytes": "TotLen Fwd Pkts",
        "dst_bytes": "TotLen Bwd Pkts",
        "count": "Tot Fwd Pkts",
        "srv_count": "Tot Bwd Pkts",
        "protocol_type": "Protocol",
    }

    for feat in target_features:
        source_col = mapping.get(feat)
        if source_col and source_col in cic_df.columns:
            aligned[feat] = cic_df[source_col]
            report["mapped"][feat] = source_col
        else:
            default_val = "SF" if feat == "flag" else ("tcp" if feat == "protocol_type" else 0)
            aligned[feat] = [default_val] * len(cic_df)
            report["unmapped"].append(feat)

    return pd.DataFrame(aligned), report


def evaluate_cross_dataset(
    cicids_sample_path: str | Path,
    model_dir: Optional[str | Path] = None,
    subsample: int = 5000,
) -> Dict[str, Any]:
    """Runs cross-dataset evaluation of existing NetraGraph network models on CIC-IDS2018."""
    target_model_dir = Path(model_dir) if model_dir else MODEL_B_DIR
    if not target_model_dir.exists():
        print(f"[Cross-Validator] Model directory not found: {target_model_dir}")
        return {}

    print("\n" + "=" * 70)
    print("  CROSS-DATASET GENERALIZATION EVALUATION")
    print(f"  Model Under Test : {target_model_dir.name}")
    print(f"  Target Telemetry : CSE-CIC-IDS2018 ({cicids_sample_path})")
    print("=" * 70)

    schema = json.loads((target_model_dir / "feature_schema.json").read_text(encoding="utf-8"))
    model = joblib.load(target_model_dir / "model.joblib")
    preprocessor = joblib.load(target_model_dir / "preprocessor.joblib")

    cic_df = pd.read_csv(cicids_sample_path, low_memory=False)
    if len(cic_df) > subsample:
        cic_df = cic_df.sample(n=subsample, random_state=42).reset_index(drop=True)

    aligned_df, map_report = align_cicids_to_model_b_schema(cic_df, schema)
    print(f"[Schema Bridge] Successfully mapped {len(map_report['mapped'])} features:")
    for k, v in map_report["mapped"].items():
        print(f"  - {k} <--- {v}")

    X_trans = preprocessor.transform(aligned_df)
    raw_preds = model.predict(X_trans)

    # Convert predictions to binary
    y_pred = np.array([1 if str(p).lower() in ["anomaly", "1", "attack"] else 0 for p in raw_preds])

    if "Label" in cic_df.columns:
        y_true = np.where(cic_df["Label"].astype(str).str.strip().str.lower() == "benign", 0, 1)
        metrics = compute_cybersecurity_metrics(y_true, y_pred)
        print_evaluation_summary(metrics, title=f"CROSS-DATASET TRANSFERABILITY ({target_model_dir.name} -> CIC-IDS2018)")
        return metrics
    else:
        print("[Cross-Validator] Label column not found in sample.")
        return {"predictions": pd.Series(y_pred).value_counts().to_dict()}


def main():
    parser = argparse.ArgumentParser(description="Cross-Dataset Validation Tool for Network Intrusion Models")
    parser.add_argument("--data-sample", required=True, help="Path to CIC-IDS2018 CSV sample")
    parser.add_argument("--model-dir", default=None, help="Path to model artifact directory")
    parser.add_argument("--subsample", type=int, default=5000, help="Max evaluation rows")
    args = parser.parse_args()

    evaluate_cross_dataset(args.data_sample, model_dir=args.model_dir, subsample=args.subsample)


if __name__ == "__main__":
    main()
