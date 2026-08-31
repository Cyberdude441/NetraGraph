"""Cross-Dataset Validation Bridge: Evaluate Existing Model B on UNSW-NB15."""
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

DEFAULT_MODEL_B_DIR = PROJECT_ROOT / "backend" / "models" / "registry" / "network-intrusion" / "v1"

# Explicit Semantic Feature Mapping between NSL-KDD (Model B) and UNSW-NB15
FEATURE_MAPPINGS: Dict[str, Optional[str]] = {
    # NSL-KDD Column -> UNSW-NB15 Column
    "duration": "dur",
    "protocol_type": "proto",
    "service": "service",
    "src_bytes": "sbytes",
    "dst_bytes": "dbytes",
    "count": "ct_srv_src",
    "srv_count": "ct_srv_dst",
    "same_srv_rate": "rate",
    "is_guest_login": "is_ftp_login",
}


def load_model_b(model_b_dir: Path) -> Tuple[Any, Any, Dict[str, Any]]:
    """Loads existing production Model B estimator and schema."""
    if not model_b_dir.exists():
        raise FileNotFoundError(f"Model B artifact directory not found: {model_b_dir}")

    schema = json.loads((model_b_dir / "feature_schema.json").read_text(encoding="utf-8"))
    model = joblib.load(model_b_dir / "model.joblib")
    preprocessor = joblib.load(model_b_dir / "preprocessor.joblib")
    return model, preprocessor, schema


def align_unsw_to_model_b_schema(
    unsw_df: pd.DataFrame,
    model_b_schema: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Explicitly translates UNSW-NB15 features to Model B (NSL-KDD) schema."""
    model_b_features = model_b_schema["feature_names"]
    aligned_rows = {}
    mapping_report: Dict[str, Any] = {
        "mapped_features": {},
        "unmapped_features": [],
        "synthesized_defaults": {},
    }

    for target_feat in model_b_features:
        unsw_source = FEATURE_MAPPINGS.get(target_feat)
        if unsw_source and unsw_source in unsw_df.columns:
            aligned_rows[target_feat] = unsw_df[unsw_source]
            mapping_report["mapped_features"][target_feat] = unsw_source
        else:
            # Provide safe neutral baseline for NSL-KDD host features absent in UNSW flow data
            default_val = "SF" if target_feat == "flag" else 0
            aligned_rows[target_feat] = [default_val] * len(unsw_df)
            mapping_report["unmapped_features"].append(target_feat)
            mapping_report["synthesized_defaults"][target_feat] = default_val

    aligned_df = pd.DataFrame(aligned_rows)
    return aligned_df, mapping_report


def cross_validate_model_b_on_unsw(
    unsw_data_path: str | Path,
    model_b_dir: Optional[str | Path] = None,
    subsample_limit: int = 10000,
) -> Dict[str, Any]:
    """Runs cross-dataset evaluation of existing Model B on UNSW-NB15 test flows."""
    model_dir = Path(model_b_dir) if model_b_dir else DEFAULT_MODEL_B_DIR
    model, preprocessor, schema = load_model_b(model_dir)

    print("\n" + "=" * 70)
    print("  CROSS-DATASET TRANSFERABILITY VALIDATION")
    print(f"  Source Model : Model B (NSL-KDD Network Intrusion)")
    print(f"  Target Data  : UNSW-NB15 ({unsw_data_path})")
    print("=" * 70)

    unsw_df = pd.read_csv(unsw_data_path)
    if len(unsw_df) > subsample_limit:
        print(f"[Cross-Validator] Subsampling to {subsample_limit:,} rows for rapid transferability assessment...")
        unsw_df = unsw_df.sample(n=subsample_limit, random_state=42).reset_index(drop=True)

    aligned_df, map_report = align_unsw_to_model_b_schema(unsw_df, schema)

    print(f"\n[Schema Bridge] Mapped {len(map_report['mapped_features'])} compatible flow features:")
    for k, v in map_report["mapped_features"].items():
        print(f"  - Model B '{k}' <--- UNSW '{v}'")
    print(f"[Schema Bridge] Unmapped NSL-KDD Host Features ({len(map_report['unmapped_features'])}): {map_report['unmapped_features'][:8]}...")

    # Transform through Model B preprocessor
    X_trans = preprocessor.transform(aligned_df)
    raw_preds = model.predict(X_trans)

    # Convert predictions to binary: Model B uses 'anomaly' vs 'normal' or 1 vs 0
    # Map 'anomaly' / 1 -> 1 (Attack), 'normal' / 0 -> 0 (Normal)
    y_pred = np.array([1 if str(p).lower() in ["anomaly", "1"] else 0 for p in raw_preds])

    # Ground truth from UNSW
    y_true = unsw_df["label"].astype(int).values if "label" in unsw_df.columns else None

    if y_true is not None:
        metrics = compute_cybersecurity_metrics(y_true, y_pred)
        print_evaluation_summary(metrics, title="CROSS-DATASET TRANSFERABILITY METRICS (MODEL B -> UNSW-NB15)")
        return {
            "metrics": metrics,
            "mapping_report": map_report,
            "sample_count": len(unsw_df),
        }
    else:
        print("  [WARN] UNSW data does not contain 'label' column. Outputting prediction distribution only.")
        return {
            "prediction_distribution": pd.Series(y_pred).value_counts().to_dict(),
            "mapping_report": map_report,
        }


def main():
    parser = argparse.ArgumentParser(description="Cross-Dataset Validation Bridge for Model B")
    parser.add_argument("--unsw-data", required=True, help="Path to UNSW-NB15 CSV file")
    parser.add_argument("--model-b-dir", default=str(DEFAULT_MODEL_B_DIR), help="Path to Model B artifact directory")
    parser.add_argument("--subsample", type=int, default=10000, help="Maximum sample size")
    args = parser.parse_args()

    cross_validate_model_b_on_unsw(args.unsw_data, args.model_b_dir, args.subsample)


if __name__ == "__main__":
    main()
