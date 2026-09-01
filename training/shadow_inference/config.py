"""Central configuration for the NetraGraph Shadow-Mode Adaptive ML Inference Gateway."""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List

# ─── Directory Layout ────────────────────────────────────────────────────────
MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
BENCHMARK_RESULTS_DIR = PROJECT_ROOT / "training" / "benchmark" / "results"
MODEL_SELECTION_DIR = PROJECT_ROOT / "training" / "model_selection"
MODEL_SELECTION_RESULTS_DIR = MODEL_SELECTION_DIR / "results"
RESULTS_DIR = MODULE_DIR / "results"
PLOTS_DIR = RESULTS_DIR / "plots"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Reproducibility & Safety ────────────────────────────────────────────────
RANDOM_SEED: int = 42
IS_SHADOW_MODE: bool = True  # Strict safeguard: Never active for production traffic

# ─── Task Types & Families (Exported for Cross-Module Compatibility) ─────────
TASK_BINARY_INTRUSION = "binary_network_intrusion"
TASK_BINARY_DDOS = "binary_ddos_detection"
TASK_MULTICLASS_MALWARE = "multiclass_malware_attribution"

FAMILY_NETWORK_FLOW = "network_flow_telemetry"
FAMILY_DDOS_VOLUMETRIC = "ddos_volumetric_reflection"
FAMILY_MALWARE_STATIC = "malware_static_metadata"

CONFIDENCE_MARGIN_HIGH = 0.04
CONFIDENCE_MARGIN_MED = 0.01

def load_benchmark_results(path: Optional[Path] = None) -> Dict[str, Any]:
    import json
    target = path or (BENCHMARK_RESULTS_DIR / "statistical_comparison.json")
    if not target.exists():
        target = PROJECT_ROOT / "training" / "benchmark" / "results" / "statistical_comparison.json"
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)

# ─── Production Models A-E Mapping ───────────────────────────────────────────
PRODUCTION_MODELS: Dict[str, Dict[str, Any]] = {
    "intrusion": {
        "model_id": "Model A",
        "name": "intrusion",
        "version": "v1",
        "title": "Session Intrusion Detection",
        "task_type": "binary_classification",
        "category": "session_intrusion",
        "dataset_equivalent": "cicids2018",
    },
    "network-intrusion": {
        "model_id": "Model B",
        "name": "network-intrusion",
        "version": "v1",
        "title": "Network Intrusion Detection",
        "task_type": "binary_classification",
        "category": "network_intrusion",
        "dataset_equivalent": "cicids2017",
    },
    "phishing-url": {
        "model_id": "Model C",
        "name": "phishing-url",
        "version": "v1",
        "title": "Phishing URL Detection",
        "task_type": "binary_classification",
        "category": "phishing_url",
        "dataset_equivalent": "unsw",
    },
    "webpage-phishing": {
        "model_id": "Model D",
        "name": "webpage-phishing",
        "version": "v1",
        "title": "Web Page Phishing Detection",
        "task_type": "binary_classification",
        "category": "webpage_phishing",
        "dataset_equivalent": "cicddos2019",
    },
    "phishing-email": {
        "model_id": "Model E",
        "name": "phishing-email",
        "version": "v1",
        "title": "Phishing Email Detection",
        "task_type": "binary_classification",
        "category": "phishing_email",
        "dataset_equivalent": "malwarebazaar",
    },
}

# ─── Benchmark Dataset to Production Mapping ─────────────────────────────────
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

# ─── Drift Monitoring Thresholds ─────────────────────────────────────────────
# PSI (Population Stability Index) standard thresholds
PSI_LOW_THRESHOLD: float = 0.10
PSI_HIGH_THRESHOLD: float = 0.25

# KS-test significance level
KS_ALPHA: float = 0.05

# Drift Severity Labels
DRIFT_LOW = "LOW"
DRIFT_MEDIUM = "MEDIUM"
DRIFT_HIGH = "HIGH"

# ─── Latency Measurement Configuration ───────────────────────────────────────
LATENCY_PERCENTILES: List[float] = [50.0, 90.0, 95.0, 99.0]
LATENCY_WARMUP_RUNS: int = 3


def get_shadow_environment_info() -> Dict[str, Any]:
    """Return environment and safety metadata for shadow inference."""
    env: Dict[str, Any] = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "random_seed": RANDOM_SEED,
        "is_shadow_mode": IS_SHADOW_MODE,
        "production_models_count": len(PRODUCTION_MODELS),
        "benchmark_datasets": BENCHMARK_DATASETS,
        "results_directory": str(RESULTS_DIR),
    }
    return env
