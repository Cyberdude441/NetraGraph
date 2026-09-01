"""
Dataset Profiler — extracts legitimate structural metadata from an incoming dataset
WITHOUT using class labels to inform model selection.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config import (
    FAMILY_DDOS_VOLUMETRIC,
    FAMILY_MALWARE_STATIC,
    FAMILY_NETWORK_FLOW,
    TASK_BINARY_DDOS,
    TASK_BINARY_INTRUSION,
    TASK_MULTICLASS_MALWARE,
)

# Column name hints used purely for structural classification (not label use)
_DDOS_HINTS = {"protocol", "reflection", "amplif", "ddos", "syn", "udp", "netbios", "ldap", "dns"}
_MALWARE_HINTS = {"entropy", "signature", "clamav", "file_size", "sha256", "vt_", "reporter",
                  "imported_symbols", "sections_count"}
_NETWORK_FLOW_HINTS = {"flow", "packet", "iat", "fwd", "bwd", "flag", "window", "bytes"}


def profile_dataset(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    dataset_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extracts structural and statistical metadata from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe (may include the target column).
    target_column : str, optional
        Name of the target/label column. Used ONLY to measure class balance.
        NOT used to influence model selection decisions.
    dataset_hint : str, optional
        Short string hint e.g. 'cicids2018', 'malwarebazaar'. Used to confirm
        inferred task type. If provided, overrides inference.

    Returns
    -------
    Dict with structural profile metadata.
    """
    n_rows, n_cols = df.shape
    feature_cols = [c for c in df.columns if c != target_column] if target_column else list(df.columns)

    # ── Numerical vs Categorical split ───────────────────────────────────────
    num_cols = [c for c in feature_cols if df[c].dtype.kind in "biufc"]
    cat_cols = [c for c in feature_cols if c not in num_cols]
    num_cat_ratio = len(num_cols) / max(1, len(cat_cols))

    # ── Missing value ratio ───────────────────────────────────────────────────
    total_cells = n_rows * len(feature_cols)
    missing_count = df[feature_cols].isnull().sum().sum()
    missing_ratio = float(missing_count / max(1, total_cells))

    # ── Duplicate ratio ───────────────────────────────────────────────────────
    n_dups = df[feature_cols].duplicated().sum()
    dup_ratio = float(n_dups / max(1, n_rows))

    # ── Class balance (uses labels ONLY for metadata, not selection) ──────────
    class_info: Dict[str, Any] = {"num_classes": 1, "imbalance_ratio": 1.0, "is_multiclass": False}
    if target_column and target_column in df.columns:
        vc = df[target_column].value_counts()
        n_classes = int(len(vc))
        imb = float(vc.max() / max(1, vc.min()))
        class_info = {
            "num_classes": n_classes,
            "imbalance_ratio": round(imb, 3),
            "is_multiclass": n_classes > 2,
            "class_distribution": {str(k): int(v) for k, v in vc.items()},
        }

    # ── Feature distribution statistics ──────────────────────────────────────
    if num_cols:
        num_data = df[num_cols].select_dtypes(include=[np.number])
        mean_skewness = float(num_data.skew().mean())
        mean_kurtosis = float(num_data.kurtosis().mean())
    else:
        mean_skewness = 0.0
        mean_kurtosis = 0.0

    # ── Task & Family Inference ───────────────────────────────────────────────
    inferred_family, inferred_task = _infer_task_family(df.columns.tolist(), class_info, dataset_hint)

    # ── Temporal characteristics ──────────────────────────────────────────────
    col_lower = {c.lower() for c in feature_cols}
    has_temporal_cols = any(k in " ".join(col_lower) for k in ("iat", "time", "date", "timestamp"))

    # ── Protocol characteristics ──────────────────────────────────────────────
    has_protocol_cols = any(k in " ".join(col_lower) for k in ("proto", "protocol", "port"))

    return {
        "n_samples": int(n_rows),
        "n_features": len(feature_cols),
        "n_numeric_features": len(num_cols),
        "n_categorical_features": len(cat_cols),
        "numeric_to_categorical_ratio": round(num_cat_ratio, 3),
        "missing_value_ratio": round(missing_ratio, 4),
        "duplicate_row_ratio": round(dup_ratio, 4),
        "class_info": class_info,
        "mean_feature_skewness": round(mean_skewness, 4),
        "mean_feature_kurtosis": round(mean_kurtosis, 4),
        "has_temporal_features": has_temporal_cols,
        "has_protocol_features": has_protocol_cols,
        "inferred_dataset_family": inferred_family,
        "inferred_task_type": inferred_task,
        "dataset_hint": dataset_hint,
    }


def _infer_task_family(
    columns: List[str],
    class_info: Dict[str, Any],
    hint: Optional[str],
) -> tuple:
    """Infer dataset family and task type from column names and class structure."""
    if hint:
        hint_l = hint.lower()
        if "malware" in hint_l or "bazaar" in hint_l:
            return FAMILY_MALWARE_STATIC, TASK_MULTICLASS_MALWARE
        if "ddos" in hint_l or "2019" in hint_l:
            return FAMILY_DDOS_VOLUMETRIC, TASK_BINARY_DDOS
        return FAMILY_NETWORK_FLOW, TASK_BINARY_INTRUSION

    col_set = {c.lower() for c in columns}
    col_str = " ".join(col_set)

    malware_hits = sum(1 for k in _MALWARE_HINTS if k in col_str)
    ddos_hits = sum(1 for k in _DDOS_HINTS if k in col_str)
    flow_hits = sum(1 for k in _NETWORK_FLOW_HINTS if k in col_str)

    is_multi = class_info.get("is_multiclass", False)

    if malware_hits >= 3 or is_multi:
        return FAMILY_MALWARE_STATIC, TASK_MULTICLASS_MALWARE
    if ddos_hits > flow_hits and ddos_hits >= 2:
        return FAMILY_DDOS_VOLUMETRIC, TASK_BINARY_DDOS
    return FAMILY_NETWORK_FLOW, TASK_BINARY_INTRUSION
