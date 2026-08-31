"""Schema Sanitization, Multi-File Alignment, Leakage Audit, and Preprocessing for CSE-CIC-IDS2018."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
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
    DEFAULT_DATA_DIR,
    LEAKAGE_COLUMNS,
    MULTICLASS_ATTACK_CATEGORIES,
    PRIMARY_TARGET,
    SchemaAuditReport,
    TrainingConfig,
)
from utils import get_memory_usage, load_parquet_cache, save_parquet_cache


def sanitize_column_name(col: str) -> str:
    """Normalizes column names by stripping leading/trailing whitespace and spaces."""
    return str(col).strip()


def normalize_dataframe_schema(df: pd.DataFrame, source_name: str = "") -> Tuple[pd.DataFrame, List[str]]:
    """Normalizes raw CIC-IDS2018 DataFrame by resolving 80 vs 84 columns and purging leakage headers."""
    # 1. Clean column headers
    df.columns = [sanitize_column_name(c) for c in df.columns]

    # 2. Filter out repeating header rows (common artifact in CIC daily dumps)
    if "Label" in df.columns:
        df = df[df["Label"] != "Label"].copy()
    elif "label" in df.columns:
        df = df[df["label"] != "label"].copy()

    # 3. Identify and drop leakage & identifier columns
    dropped_cols = []
    cols_to_drop = []
    for col in df.columns:
        clean_lower = col.lower().strip()
        if clean_lower in LEAKAGE_COLUMNS:
            cols_to_drop.append(col)
            dropped_cols.append(col)

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # 4. Standardize Target Column Name to 'Label'
    for c in df.columns:
        if c.lower() == "label" and c != "Label":
            df = df.rename(columns={c: "Label"})

    return df, dropped_cols


def sanitize_numeric_values(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Replaces +/- Infinity and converts numeric fields safely."""
    for col in feature_cols:
        if col in df.columns:
            # Force numeric conversion
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Replace infinities with NaN for median imputation
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    return df


def load_and_merge_cicids2018_files(
    data_dir: str | Path,
    subsample_ratio: Optional[float] = None,
    use_cache: bool = True,
) -> Tuple[pd.DataFrame, SchemaAuditReport]:
    """Scans all 10 CSVs, harmonizes 80 vs 84 columns, and compiles a single consolidated dataset."""
    path = Path(data_dir)
    cache_path = path / "cicids2018_harmonized_cache.parquet"

    # Try loading cached Parquet if enabled
    if use_cache:
        cached_df = load_parquet_cache(cache_path)
        if cached_df is not None:
            if subsample_ratio and 0.0 < subsample_ratio < 1.0:
                cached_df = cached_df.sample(frac=subsample_ratio, random_state=42).reset_index(drop=True)
            report = audit_dataset_integrity(cached_df)
            return cached_df, report

    csv_files = sorted(list(set(path.rglob("*.csv"))))
    if not csv_files:
        raise FileNotFoundError(f"No CSV dataset files found under {data_dir}")

    print(f"\n[Data Loader] Discovered {len(csv_files)} CSV files in {data_dir}:")
    for f in csv_files:
        print(f"  - {f.name} ({f.stat().st_size / (1024**2):.1f} MB)")

    dfs: List[pd.DataFrame] = []
    file_col_counts: Dict[str, int] = {}
    all_dropped_cols: List[str] = []

    for f in csv_files:
        print(f"[Schema Normalizer] Ingesting {f.name}...")
        raw_df = pd.read_csv(f, low_memory=False)
        file_col_counts[f.name] = len(raw_df.columns)

        # Normalize schema (handles 80 vs 84 columns)
        clean_df, dropped = normalize_dataframe_schema(raw_df, source_name=f.name)
        all_dropped_cols.extend(dropped)

        if subsample_ratio and 0.0 < subsample_ratio < 1.0:
            clean_df = clean_df.sample(frac=subsample_ratio, random_state=42).reset_index(drop=True)

        dfs.append(clean_df)

    print("\n[Schema Normalizer] Concatenating harmonized partitions...")
    merged_df = pd.concat(dfs, ignore_index=True)

    # Re-normalize merged columns to ensure clean alignment
    merged_df, _ = normalize_dataframe_schema(merged_df)

    # Sanitize numeric columns
    feature_cols = [c for c in merged_df.columns if c != "Label"]
    merged_df = sanitize_numeric_values(merged_df, feature_cols)

    # Save to Parquet cache for subsequent rapid execution
    if use_cache:
        try:
            save_parquet_cache(merged_df, cache_path)
        except Exception as e:
            print(f"  [WARN] Parquet cache save skipped: {e}")

    report = audit_dataset_integrity(merged_df, file_col_counts, list(set(all_dropped_cols)))
    return merged_df, report


def audit_dataset_integrity(
    df: pd.DataFrame,
    file_col_counts: Optional[Dict[str, int]] = None,
    dropped_cols: Optional[List[str]] = None,
) -> SchemaAuditReport:
    """Audits missing values, infinite floats, class distribution, and feature integrity."""
    report = SchemaAuditReport()
    report.total_rows = len(df)
    report.file_column_counts = file_col_counts or {}
    report.dropped_leakage_columns = dropped_cols or []

    feature_cols = [c for c in df.columns if c != "Label"]
    report.normalized_feature_count = len(feature_cols)

    # Missing & Infinite counts
    report.missing_values_count = int(df[feature_cols].isnull().sum().sum())
    report.infinite_values_count = int(np.isinf(df[feature_cols].select_dtypes(include=[np.number])).sum().sum())

    # Target breakdown
    if "Label" in df.columns:
        counts = df["Label"].astype(str).str.strip().value_counts().to_dict()
        report.class_distribution = {str(k): int(v) for k, v in counts.items()}
        report.benign_rows = int(counts.get("Benign", counts.get("benign", 0)))
        report.attack_rows = report.total_rows - report.benign_rows

    print("\n" + "=" * 65)
    print("  CSE-CIC-IDS2018 SCHEMA & INTEGRITY AUDIT")
    print("=" * 65)
    print(f"  Total Partitions Scanned : {len(report.file_column_counts)}")
    for f, count in report.file_column_counts.items():
        print(f"    - {f:20s}: {count} raw columns")
    print(f"  Harmonized Features Count: {report.normalized_feature_count}")
    print(f"  Total Flow Records       : {report.total_rows:,}")
    print(f"  Benign vs Attack Flows   : {report.benign_rows:,} Benign ({report.benign_rows / max(1, report.total_rows) * 100:.1f}%) | {report.attack_rows:,} Attacks")
    print(f"  Purged Leakage Columns   : {report.dropped_leakage_columns}")
    print(f"  NaN Values Sanitized     : {report.missing_values_count:,}")
    print(f"  RAM Utilization          : {get_memory_usage()}")
    print("=" * 65 + "\n")

    return report


def prepare_cicids2018_features(
    df: pd.DataFrame,
    target_mode: str = "binary",  # "binary" or "multiclass"
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, ColumnTransformer, List[str]]:
    """Splits dataset, encodes targets, and fits scikit-learn preprocessing pipeline."""
    feature_names = [c for c in df.columns if c != "Label"]
    X = df[feature_names].copy()

    # Target Mapping
    raw_labels = df["Label"].astype(str).str.strip()
    if target_mode == "binary":
        y = np.where(raw_labels.str.lower() == "benign", 0, 1)
        y = pd.Series(y, name="Label")
    else:
        # Multi-class integer mapping
        y_int = raw_labels.str.lower().map(MULTICLASS_ATTACK_CATEGORIES).fillna(1).astype(int)
        y = pd.Series(y_int, name="Label")

    print(f"[Feature Prep] Splitting {len(X):,} samples ({target_mode} mode, test_size={test_size})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    numeric_features = [c for c in feature_names if X_train[c].dtype.kind in "biufc"]
    categorical_features = [c for c in feature_names if c not in numeric_features]

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
    print(f"[Feature Prep] Fitting preprocessor on training partition ({len(X_train):,} samples)...")
    preprocessor.fit(X_train)

    return X_train, y_train, X_test, y_test, preprocessor, feature_names


def main():
    parser = argparse.ArgumentParser(description="CSE-CIC-IDS2018 Dataset Preparation & Schema Normalizer")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Path to CIC-IDS2018 dataset directory")
    parser.add_argument("--subsample", type=float, default=None, help="Subsample ratio (0.0 to 1.0)")
    parser.add_argument("--mode", default="binary", choices=["binary", "multiclass"], help="Target classification mode")
    args = parser.parse_args()

    df, report = load_and_merge_cicids2018_files(args.data_dir, subsample_ratio=args.subsample)
    X_train, y_train, X_test, y_test, preprocessor, feature_names = prepare_cicids2018_features(df, target_mode=args.mode)
    print(f"Preparation Complete! Train Shape: {X_train.shape}, Test Shape: {X_test.shape}")


if __name__ == "__main__":
    main()
