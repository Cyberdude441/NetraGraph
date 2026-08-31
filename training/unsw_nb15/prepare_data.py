"""Data Discovery, Validation, Leakage Audit, and Preprocessing for UNSW-NB15."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Add training folder and backend to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import (
    CATEGORICAL_FEATURES,
    DEFAULT_DATA_DIR,
    LEAKAGE_COLUMNS,
    OFFICIAL_TEST_FILE,
    OFFICIAL_TRAIN_FILE,
    PRIMARY_TARGET,
    RAW_PART_FILES,
    DataValidationReport,
    TrainingConfig,
)
from utils import get_memory_usage, inspect_and_extract_zip


def discover_unsw_files(data_dir: str | Path) -> Dict[str, Optional[Path]]:
    """Recursively locates UNSW-NB15 files, extracting CSVs from ZIPs if present."""
    path = Path(data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Data directory does not exist: {path}")

    # If ZIP files are present, extract CSVs safely
    zip_files = list(path.rglob("*.zip"))
    if zip_files:
        for z in zip_files:
            inspect_and_extract_zip(z, target_extract_dir=path)

    csv_files = list(path.rglob("*.csv"))
    csv_map: Dict[str, Optional[Path]] = {
        "train": None,
        "test": None,
        "raw_parts": [],
        "all_csvs": csv_files,
    }

    for f in csv_files:
        fname = f.name.lower()
        if "training" in fname or "train" in fname:
            csv_map["train"] = f
        elif "testing" in fname or "test" in fname:
            csv_map["test"] = f
        elif any(part.lower() in fname for part in ["unsw-nb15_1", "unsw-nb15_2", "unsw-nb15_3", "unsw-nb15_4"]):
            csv_map["raw_parts"].append(f)

    return csv_map


def load_dataset_frames(
    data_dir: str | Path,
    subsample_ratio: Optional[float] = None,
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """Loads train and test DataFrames from discovered files."""
    files = discover_unsw_files(data_dir)
    train_df: Optional[pd.DataFrame] = None
    test_df: Optional[pd.DataFrame] = None

    if files["train"] and files["test"]:
        print(f"[Data Loader] Loading official training file: {files['train'].name}")
        train_df = pd.read_csv(files["train"])
        print(f"[Data Loader] Loading official testing file: {files['test'].name}")
        test_df = pd.read_csv(files["test"])
    elif files["raw_parts"]:
        print(f"[Data Loader] Loading {len(files['raw_parts'])} raw multi-part CSV files...")
        dfs = [pd.read_csv(f) for f in sorted(files["raw_parts"])]
        combined = pd.concat(dfs, ignore_index=True)
        train_df = combined
        test_df = None
    elif files["all_csvs"]:
        print(f"[Data Loader] Loading primary CSV file: {files['all_csvs'][0].name}")
        train_df = pd.read_csv(files["all_csvs"][0])
        test_df = None
    else:
        raise FileNotFoundError(f"No CSV dataset files found under {data_dir}")

    # Strip whitespace from column names
    train_df.columns = [str(c).strip() for c in train_df.columns]
    if test_df is not None:
        test_df.columns = [str(c).strip() for c in test_df.columns]

    if subsample_ratio and 0.0 < subsample_ratio < 1.0:
        print(f"[Data Loader] Applying subsample ratio {subsample_ratio:.2f} for rapid testing...")
        train_df = train_df.sample(frac=subsample_ratio, random_state=42).reset_index(drop=True)
        if test_df is not None:
            test_df = test_df.sample(frac=subsample_ratio, random_state=42).reset_index(drop=True)

    return train_df, test_df


def audit_and_validate_data(
    train_df: pd.DataFrame,
    test_df: Optional[pd.DataFrame] = None,
    target_col: str = PRIMARY_TARGET,
) -> DataValidationReport:
    """Performs strict data validation and data leakage analysis."""
    report = DataValidationReport()
    report.train_rows = len(train_df)
    report.test_rows = len(test_df) if test_df is not None else 0

    print("\n" + "=" * 60)
    print("UNSW-NB15 DATA VALIDATION & INTEGRITY AUDIT")
    print("=" * 60)
    print(f"  Training Rows   : {report.train_rows:,}")
    print(f"  Testing Rows    : {report.test_rows:,}")
    print(f"  RAM Utilization : {get_memory_usage()}")

    # 1. Missing Values
    missing_dict = train_df.isnull().sum().to_dict()
    missing_nonzero = {k: int(v) for k, v in missing_dict.items() if v > 0}
    report.missing_values = missing_nonzero
    if missing_nonzero:
        print(f"  [WARN] Missing values detected in {len(missing_nonzero)} columns: {missing_nonzero}")
    else:
        print("  [PASS] No missing values in training dataset.")

    # 2. Target Column & Distribution
    if target_col not in train_df.columns:
        # Check case-insensitive
        matches = [c for c in train_df.columns if c.lower() == target_col.lower()]
        if matches:
            target_col = matches[0]
        else:
            raise ValueError(f"Target column '{target_col}' not found in dataset columns: {list(train_df.columns)}")

    target_counts = train_df[target_col].value_counts().to_dict()
    report.target_distribution = {str(k): int(v) for k, v in target_counts.items()}
    print(f"  [PASS] Target column '{target_col}' distribution: {report.target_distribution}")

    # 3. Categorical vs Numerical Columns
    all_features = [c for c in train_df.columns if c != target_col]
    numeric_cols = [c for c in all_features if train_df[c].dtype.kind in "biufc"]
    categorical_cols = [c for c in all_features if c not in numeric_cols]
    report.numerical_columns = numeric_cols
    report.categorical_columns = categorical_cols
    report.feature_count = len(all_features)
    print(f"  [INFO] Features detected: {len(all_features)} total ({len(numeric_cols)} numeric, {len(categorical_cols)} categorical)")

    # 4. Constant Columns (Zero Variance)
    constant_cols = [c for c in all_features if train_df[c].nunique(dropna=False) <= 1]
    report.constant_columns = constant_cols
    if constant_cols:
        print(f"  [WARN] Constant (zero variance) columns found: {constant_cols}")
        report.leakage_warnings.append(f"Constant columns present: {constant_cols}")

    # 5. Data Leakage Checks
    print("\n--- Data Leakage Audit ---")
    leakage_found: List[str] = []
    for leak_col in LEAKAGE_COLUMNS:
        if leak_col in train_df.columns:
            leakage_found.append(leak_col)

    if leakage_found:
        msg = f"Columns identified for leakage/identifier exclusion: {leakage_found}"
        print(f"  [LEAKAGE SHIELD] {msg}")
        report.leakage_warnings.append(msg)
    else:
        print("  [PASS] No standard identifier leakage columns detected.")

    # 6. Train/Test Overlap & Duplicate Sample Check
    if test_df is not None:
        train_features = train_df.drop(columns=[c for c in [target_col, "id", "attack_cat"] if c in train_df.columns])
        test_features = test_df.drop(columns=[c for c in [target_col, "id", "attack_cat"] if c in test_df.columns])
        common_cols = [c for c in train_features.columns if c in test_features.columns]

        train_dupes = train_features[common_cols].duplicated().sum()
        report.duplicate_rows = int(train_dupes)

        # Hash overlap check
        train_hashes = set(pd.util.hash_pandas_object(train_features[common_cols]))
        test_hashes = set(pd.util.hash_pandas_object(test_features[common_cols]))
        overlap = len(train_hashes.intersection(test_hashes))
        report.train_test_overlap_rows = overlap
        print(f"  [INFO] Duplicate rows in training set: {train_dupes:,}")
        print(f"  [INFO] Exact feature vector overlap between train and test: {overlap:,} rows")
        if overlap > 0:
            report.leakage_warnings.append(f"Train/Test feature vector overlap: {overlap} records")

    print("=" * 60 + "\n")
    return report


def prepare_features(
    train_df: pd.DataFrame,
    test_df: Optional[pd.DataFrame] = None,
    config: Optional[TrainingConfig] = None,
) -> Tuple[pd.DataFrame, pd.Series, Optional[pd.DataFrame], Optional[pd.Series], ColumnTransformer, List[str], List[int]]:
    """Prepares and cleans feature matrices and fits the preprocessor pipeline."""
    cfg = config or TrainingConfig()
    target_col = PRIMARY_TARGET

    # 1. Audit Data
    report = audit_and_validate_data(train_df, test_df, target_col)

    # 2. Determine features to drop
    drop_cols: List[str] = []
    if cfg.drop_leakage_cols:
        for c in LEAKAGE_COLUMNS:
            if c in train_df.columns and c != target_col:
                drop_cols.append(c)

    print(f"[Feature Prep] Explicitly dropping non-feature/leakage columns: {drop_cols}")
    clean_train_df = train_df.drop(columns=drop_cols)

    feature_names = [c for c in clean_train_df.columns if c != target_col]
    X_train = clean_train_df[feature_names]
    y_train = clean_train_df[target_col].astype(int)

    X_test: Optional[pd.DataFrame] = None
    y_test: Optional[pd.Series] = None

    if test_df is not None:
        clean_test_df = test_df.drop(columns=[c for c in drop_cols if c in test_df.columns])
        # Ensure exact column alignment
        X_test = clean_test_df[[c for c in feature_names if c in clean_test_df.columns]]
        y_test = clean_test_df[target_col].astype(int)

    # 3. Categorical indices for CatBoost
    numeric_features = [c for c in feature_names if X_train[c].dtype.kind in "biufc"]
    categorical_features = [c for c in feature_names if c not in numeric_features]
    cat_indices = [feature_names.index(c) for c in categorical_features]

    print(f"[Feature Prep] Prepared {len(feature_names)} features ({len(categorical_features)} categorical: {categorical_features})")

    # 4. Build standard preprocessing ColumnTransformer for artifact compatibility
    transformers = []
    if numeric_features:
        transformers.append((
            "numeric",
            Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
            numeric_features,
        ))
    if categorical_features:
        transformers.append((
            "categorical",
            Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]),
            categorical_features,
        ))

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    preprocessor.fit(X_train)

    return X_train, y_train, X_test, y_test, preprocessor, feature_names, cat_indices


def main():
    parser = argparse.ArgumentParser(description="UNSW-NB15 Dataset Preparation and Validation Tool")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Path to UNSW-NB15 dataset directory")
    parser.add_argument("--subsample", type=float, default=None, help="Subsample ratio for testing (0.0 to 1.0)")
    args = parser.parse_args()

    print(f"Starting UNSW-NB15 Data Preparation on: {args.data_dir}")
    train_df, test_df = load_dataset_frames(args.data_dir, subsample_ratio=args.subsample)
    cfg = TrainingConfig(data_dir=args.data_dir, subsample_ratio=args.subsample)
    X_train, y_train, X_test, y_test, preprocessor, feature_names, cat_indices = prepare_features(train_df, test_df, cfg)
    print(f"\nPreparation Complete! Training Shape: {X_train.shape}, Test Shape: {X_test.shape if X_test is not None else 'N/A'}")


if __name__ == "__main__":
    main()
