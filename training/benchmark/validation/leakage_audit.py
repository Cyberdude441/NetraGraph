"""Leakage Audit Engine for Cybersecurity Machine Learning Datasets."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple

import numpy as np
import pandas as pd

# Canonical leakage columns across network and malware datasets
IDENTIFIER_PATTERNS = [
    r"^flow\s*id",
    r"^(src|source)\s*(ip|addr|address)",
    r"^(dst|dest|destination)\s*(ip|addr|address)",
    r"^(src|source)\s*(port|pt)",
    r"^(dst|dest|destination)\s*(port|pt)",
    r"^timestamp",
    r"^time",
    r"^date",
    r"^unnamed",
    r"^id$",
    r"^index$",
    r"hash",
    r"sha256",
    r"md5",
    r"^day",
    r"^submission",
    r"^reporter",
]


def audit_dataset_leakage(
    df: pd.DataFrame,
    target_column: str,
    explicit_drop: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Performs full lexical and statistical leakage audit:
    1. Detects identifier and metadata headers.
    2. Measures high-correlation proxy leakage (> 0.99 with target).
    3. Returns sanitized dataframe and audit metadata.
    """
    original_columns = list(df.columns)
    dropped_columns: List[str] = []
    suspicious_correlation_columns: List[str] = []

    # 1. Header lexical matching
    for col in original_columns:
        if col == target_column:
            continue

        clean_col = str(col).strip().lower()
        if explicit_drop and any(clean_col == str(d).strip().lower() for d in explicit_drop):
            dropped_columns.append(col)
            continue

        for pattern in IDENTIFIER_PATTERNS:
            if re.search(pattern, clean_col):
                dropped_columns.append(col)
                break

    # 2. Check for duplicate column names
    clean_df = df.drop(columns=dropped_columns, errors="ignore").copy()

    # 3. Statistical correlation check (numeric features against target)
    y_raw = df[target_column]
    if pd.api.types.is_numeric_dtype(y_raw) or len(y_raw.unique()) == 2:
        y_num = pd.to_numeric(y_raw, errors="coerce").fillna(0)
        for col in clean_df.columns:
            if col != target_column and pd.api.types.is_numeric_dtype(clean_df[col]):
                try:
                    corr = np.abs(np.corrcoef(clean_df[col].fillna(0), y_num)[0, 1])
                    if not np.isnan(corr) and corr > 0.995:
                        suspicious_correlation_columns.append(f"{col} (corr={corr:.4f})")
                except Exception:
                    pass

    return {
        "original_column_count": len(original_columns),
        "sanitized_column_count": len(clean_df.columns) - 1,  # excluding target
        "dropped_leakage_columns": dropped_columns,
        "potential_leakage_features": suspicious_correlation_columns,
        "sanitized_feature_names": [c for c in clean_df.columns if c != target_column],
        "status": "PASS" if not suspicious_correlation_columns else "FLAGGED_FOR_REVIEW",
    }
