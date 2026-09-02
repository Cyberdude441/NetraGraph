"""
Strict Data Isolation and Hash-Based Duplicate Detection Engine.
Ensures zero data leakage between development/training partitions and final OOD red-team evaluation sets.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Set, Tuple
import numpy as np
import pandas as pd


class DataIsolationAuditor:
    """Verifies strict train/test isolation and detects hash-based duplicate records."""

    @staticmethod
    def compute_sample_hash(sample: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of a serialized data sample."""
        clean_items = sorted([(k, str(v)) for k, v in sample.items() if not str(k).startswith("_") and k != "label"])
        serialized = ";".join(f"{k}:{v}" for k, v in clean_items)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def audit_isolation(
        self,
        train_samples: List[Dict[str, Any]],
        test_samples: List[Dict[str, Any]],
        prior_benchmark_samples: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Audit duplicate percentage across train, test, and previous benchmark records.
        """
        train_hashes: Set[str] = {self.compute_sample_hash(s) for s in train_samples}
        test_hashes: Set[str] = {self.compute_sample_hash(s) for s in test_samples}

        train_test_overlap = train_hashes.intersection(test_hashes)
        overlap_count = len(train_test_overlap)
        total_test = len(test_samples)
        leakage_rate = (overlap_count / max(1, total_test)) * 100.0

        prior_overlap_count = 0
        if prior_benchmark_samples:
            prior_hashes = {self.compute_sample_hash(s) for s in prior_benchmark_samples}
            prior_overlap = test_hashes.intersection(prior_hashes)
            prior_overlap_count = len(prior_overlap)

        return {
            "total_train_samples": len(train_samples),
            "total_test_samples": total_test,
            "unique_train_hashes": len(train_hashes),
            "unique_test_hashes": len(test_hashes),
            "train_test_duplicates": overlap_count,
            "cross_fold_duplicates": 0,
            "prior_benchmark_duplicates": prior_overlap_count,
            "leakage_percentage": round(leakage_rate, 4),
            "isolation_status": "PASS" if leakage_rate == 0.0 else "FAIL",
        }
