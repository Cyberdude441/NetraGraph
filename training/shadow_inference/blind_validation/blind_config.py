"""
Configuration and Immutability Audit for NetraGraph Blind Holdout & Adversarial Validation.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
MODEL_SEL_ROOT = PROJECT_ROOT / "training" / "model_selection"
SHADOW_ROOT = PROJECT_ROOT / "training" / "shadow_inference"

RESULTS_DIR = MODULE_DIR / "results"
PLOTS_DIR = MODULE_DIR / "plots"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# 5 Multi-Seed Evaluation List
EVALUATION_SEEDS: List[int] = [42, 101, 2024, 777, 9999]

# Dataset and Model Mappings
BENCHMARK_DATASETS: List[str] = [
    "cicids2017",
    "cicids2018",
    "cicddos2019",
    "unsw",
    "malwarebazaar",
]

DATASET_TO_PROD_MODEL: Dict[str, str] = {
    "cicids2017": "network-intrusion",
    "cicids2018": "intrusion",
    "cicddos2019": "webpage-phishing",
    "unsw": "phishing-url",
    "malwarebazaar": "phishing-email",
}

THRESHOLD_SWEEP_LIST: List[float] = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]


def audit_frozen_system_hashes() -> Dict[str, Any]:
    """Calculate and return immutable SHA-256 hashes of all frozen model artifacts."""
    registry_dir = BACKEND_ROOT / "models" / "registry"
    hashes = {}
    
    models = ["intrusion", "network-intrusion", "phishing-url", "webpage-phishing", "phishing-email"]
    for m in models:
        model_file = registry_dir / m / "v1" / "model.joblib"
        if model_file.exists():
            h = hashlib.sha256(model_file.read_bytes()).hexdigest()
            hashes[f"production_{m}_v1_sha256"] = h

    # Hash adaptive selector configuration
    scoring_file = MODEL_SEL_ROOT / "scoring.py"
    if scoring_file.exists():
        hashes["adaptive_scoring_engine_sha256"] = hashlib.sha256(scoring_file.read_bytes()).hexdigest()

    selector_file = MODEL_SEL_ROOT / "model_selector.py"
    if selector_file.exists():
        hashes["adaptive_selector_engine_sha256"] = hashlib.sha256(selector_file.read_bytes()).hexdigest()

    return hashes
