"""
Comparator Module for NetraGraph Shadow Inference.

Compares outputs from production Models A–E and the Adaptive Selection layer.
Calculates prediction agreement, risk delta, disagreement severity,
and aggregate statistics.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union
import numpy as np

from schemas import AdaptiveResult, ComparisonResult, ProductionResult


def normalize_prediction(pred: Union[str, int, float, None]) -> str:
    """
    Standardize various label encodings into canonical string categories:
    'MALICIOUS' (positive class) or 'BENIGN' (negative class).
    """
    if pred is None:
        return "UNKNOWN"
    s = str(pred).strip().lower()
    
    # Positive / Attack indications
    if s in ["1", "1.0", "anomaly", "attack", "phishing", "malicious", "dos", "probe", "r2l", "u2r", "ddos", "true"]:
        return "MALICIOUS"
    
    # Negative / Benign indications
    if s in ["0", "0.0", "normal", "legitimate", "benign", "clean", "false"]:
        return "BENIGN"
    
    return s.upper()


def compare_results(
    production: ProductionResult,
    adaptive: AdaptiveResult,
) -> ComparisonResult:
    """
    Compare a single production result with an adaptive result.
    """
    prod_norm = normalize_prediction(production.prediction)
    adapt_norm = normalize_prediction(adaptive.prediction)

    agreement = (prod_norm == adapt_norm)
    risk_delta = abs(production.risk_score - adaptive.risk_score)
    model_changed = (production.model.lower() != adaptive.model.lower())
    latency_delta_ms = adaptive.total_latency_ms - production.latency_ms

    # Determine severity of disagreement
    if agreement:
        severity = "NONE"
    elif risk_delta > 0.50:
        severity = "CRITICAL"
    elif risk_delta > 0.25:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return ComparisonResult(
        prediction_agreement=agreement,
        risk_delta=risk_delta,
        model_changed=model_changed,
        production_model=production.model,
        adaptive_model=adaptive.model,
        production_prediction=str(production.prediction),
        adaptive_prediction=str(adaptive.prediction),
        latency_delta_ms=latency_delta_ms,
        disagreement_severity=severity,
    )


def calculate_aggregate_comparison(
    comparisons: List[ComparisonResult],
) -> Dict[str, Any]:
    """
    Compute aggregate agreement, disagreement, risk delta, and latency metrics across multiple results.
    """
    if not comparisons:
        return {
            "total_samples": 0,
            "agreement_rate": 1.0,
            "disagreement_rate": 0.0,
            "mean_risk_delta": 0.0,
            "median_risk_delta": 0.0,
            "max_risk_delta": 0.0,
            "model_changed_rate": 0.0,
            "severity_breakdown": {"NONE": 0, "LOW": 0, "MEDIUM": 0, "CRITICAL": 0},
        }

    total = len(comparisons)
    agreed_count = sum(1 for c in comparisons if c.prediction_agreement)
    disagreed_count = total - agreed_count
    model_changed_count = sum(1 for c in comparisons if c.model_changed)

    risk_deltas = [c.risk_delta for c in comparisons]
    latency_deltas = [c.latency_delta_ms for c in comparisons]

    severity_counts = {"NONE": 0, "LOW": 0, "MEDIUM": 0, "CRITICAL": 0}
    for c in comparisons:
        severity_counts[c.disagreement_severity] = severity_counts.get(c.disagreement_severity, 0) + 1

    return {
        "total_samples": total,
        "agreement_count": agreed_count,
        "disagreement_count": disagreed_count,
        "agreement_rate": round(agreed_count / total, 5),
        "disagreement_rate": round(disagreed_count / total, 5),
        "model_changed_rate": round(model_changed_count / total, 5),
        "mean_risk_delta": round(float(np.mean(risk_deltas)), 5),
        "median_risk_delta": round(float(np.median(risk_deltas)), 5),
        "max_risk_delta": round(float(np.max(risk_deltas)), 5),
        "mean_latency_delta_ms": round(float(np.mean(latency_deltas)), 5),
        "severity_breakdown": severity_counts,
    }
