"""Central configuration for the NetraGraph Adaptive Model Selection research layer."""
from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List

# ─── Directory Layout ────────────────────────────────────────────────────────
MODULE_DIR = Path(__file__).resolve().parent
BENCHMARK_RESULTS_DIR = MODULE_DIR.parent / "benchmark" / "results"
RESULTS_DIR = MODULE_DIR / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Reproducibility ─────────────────────────────────────────────────────────
RANDOM_SEED: int = 42

# ─── Task Types ──────────────────────────────────────────────────────────────
TASK_BINARY_INTRUSION = "binary_network_intrusion"
TASK_BINARY_DDOS = "binary_ddos_detection"
TASK_MULTICLASS_MALWARE = "multiclass_malware_attribution"

# ─── Dataset Family Tags ─────────────────────────────────────────────────────
FAMILY_NETWORK_FLOW = "network_flow_telemetry"
FAMILY_DDOS_VOLUMETRIC = "ddos_volumetric_reflection"
FAMILY_MALWARE_STATIC = "malware_static_metadata"

# ─── Ranking Weights ─────────────────────────────────────────────────────────
# Used by the scoring engine to combine metrics into a single operational score.
# Weights reflect cybersecurity priorities: detection quality > false alarms > speed.
RANKING_WEIGHTS: Dict[str, float] = {
    "f1":              0.40,
    "recall":          0.20,
    "fpr_penalty":     0.25,   # Subtracted: lower FPR = higher score
    "latency_penalty": 0.05,   # Subtracted: lower latency = higher score (normalised)
    "stability":       0.10,   # Cross-dataset rank stability bonus
}

# ─── FPR Operational Thresholds ──────────────────────────────────────────────
FPR_THRESHOLDS: List[float] = [0.01, 0.001, 0.0001]

# ─── Confidence Calibration Constants ────────────────────────────────────────
# Confidence here represents SELECTION CONFIDENCE, not prediction probability.
CONFIDENCE_MARGIN_HIGH  = 0.04  # If best model leads next by >4% in score → high
CONFIDENCE_MARGIN_MED   = 0.01  # >1% → medium; else low

# ─── Benchmark Source ────────────────────────────────────────────────────────
BENCHMARK_RESULTS_FILE = BENCHMARK_RESULTS_DIR / "repeated_validation_results.json"

def load_benchmark_results() -> Dict[str, Any]:
    """Load the committed repeated-validation benchmark results."""
    if not BENCHMARK_RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Benchmark results not found at {BENCHMARK_RESULTS_FILE}. "
            "Run research_runner.py first."
        )
    with open(BENCHMARK_RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_environment_info() -> Dict[str, Any]:
    """Return reproducibility metadata."""
    env: Dict[str, Any] = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "random_seed": RANDOM_SEED,
        "benchmark_source": str(BENCHMARK_RESULTS_FILE),
    }
    for pkg in ["numpy", "sklearn", "xgboost", "lightgbm", "catboost", "scipy"]:
        try:
            mod = __import__(pkg)
            env[f"{pkg}_version"] = getattr(mod, "__version__", "unknown")
        except ImportError:
            env[f"{pkg}_version"] = "not_installed"
    return env
