"""Cryptographic provenance and deterministic identity generation for Drift Observatory.

CRITICAL ARCHITECTURAL INVARIANT:
Analytical observation IDs MUST NOT depend on computation timestamp.
Identical analytical inputs (domain, target, baseline ID, comparison data digest,
metric name, algorithm version, and threshold policy version) MUST ALWAYS produce
the exact same observation ID regardless of execution time.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional, Union
import numpy as np


def compute_data_digest(data: Any) -> str:
    """
    Computes a deterministic SHA-256 hex digest for arbitrary analytical datasets or data structures.
    Uses canonical JSON serialization with sorted keys and normalized float representation.
    """
    if data is None:
        return hashlib.sha256(b"null").hexdigest()

    if isinstance(data, (list, tuple, set)):
        # Normalize items
        serialized_items = []
        for item in data:
            if isinstance(item, (int, float, str, bool)):
                serialized_items.append(str(item))
            elif isinstance(item, dict):
                serialized_items.append(json.dumps(item, sort_keys=True))
            else:
                serialized_items.append(str(item))
        serialized_items.sort()
        payload = "|".join(serialized_items).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    if isinstance(data, dict):
        payload = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    if isinstance(data, np.ndarray):
        payload = data.tobytes()
        return hashlib.sha256(payload).hexdigest()

    return hashlib.sha256(str(data).encode("utf-8")).hexdigest()


def compute_analytical_observation_id(
    domain: str,
    target: str,
    reference_baseline_id: str,
    comparison_data_digest: str,
    metric_name: str,
    algorithm_version: str = "1.0.0",
    threshold_policy_version: str = "1.0.0",
) -> str:
    """
    Generates a deterministic, timestamp-free analytical identity hash.
    
    Formula:
        drf:{domain}:{target}:{ref_id[:8]}:{sha256(canonical_inputs)[:16]}
    """
    canonical_dict = {
        "domain": str(domain).upper(),
        "target": str(target).lower(),
        "ref_id": str(reference_baseline_id),
        "cmp_digest": str(comparison_data_digest),
        "metric": str(metric_name),
        "alg_ver": str(algorithm_version),
        "policy_ver": str(threshold_policy_version),
    }
    canonical_payload = json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
    content_hash = hashlib.sha256(canonical_payload).hexdigest()[:16]
    
    clean_domain = str(domain).lower().replace("_", "")
    clean_target = str(target).lower().replace(" ", "-")[:16]
    clean_ref = str(reference_baseline_id).replace("base:", "")[:8]
    
    return f"drf:{clean_domain}:{clean_target}:{clean_ref}:{content_hash}"


def generate_run_id() -> str:
    """Generates an execution-level run identifier for operational trace disambiguation."""
    return f"run-{uuid.uuid4().hex[:12]}"
