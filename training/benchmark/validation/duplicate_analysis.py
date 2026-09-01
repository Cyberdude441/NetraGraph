"""Duplicate & Near-Duplicate Analysis across Train and Test Partitions."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def analyze_partition_duplicates(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: List[str],
) -> Dict[str, Any]:
    """
    Computes exact and cross-split duplicate rates across feature matrices:
    - Train internal duplicates
    - Test internal duplicates
    - Cross-split contamination duplicates (identical feature vectors in train and test)
    """
    n_train = X_train.shape[0]
    n_test = X_test.shape[0]

    # Convert rounded feature rows to hash representations for fast matching
    def compute_row_hashes(matrix: np.ndarray) -> List[str]:
        # Round to 4 decimal places to capture near-duplicates
        rounded = np.round(matrix, decimals=4)
        return [hashlib.md5(row.tobytes()).hexdigest() for row in rounded]

    train_hashes = compute_row_hashes(X_train)
    test_hashes = compute_row_hashes(X_test)

    train_unique_hashes = set(train_hashes)
    test_unique_hashes = set(test_hashes)

    train_duplicate_count = n_train - len(train_unique_hashes)
    test_duplicate_count = n_test - len(test_unique_hashes)

    # Cross-split overlap
    cross_split_overlap_hashes = train_unique_hashes.intersection(test_unique_hashes)
    cross_split_count = sum(1 for h in test_hashes if h in train_unique_hashes)

    return {
        "train_samples": n_train,
        "test_samples": n_test,
        "train_duplicate_count": train_duplicate_count,
        "train_duplicate_pct": round((train_duplicate_count / max(1, n_train)) * 100, 2),
        "test_duplicate_count": test_duplicate_count,
        "test_duplicate_pct": round((test_duplicate_count / max(1, n_test)) * 100, 2),
        "cross_split_leakage_duplicates": cross_split_count,
        "cross_split_leakage_pct": round((cross_split_count / max(1, n_test)) * 100, 2),
        "leakage_status": "PASS (Zero Cross-Split Duplicates)" if cross_split_count == 0 else f"WARNING ({cross_split_count} cross-split duplicates detected)",
    }
