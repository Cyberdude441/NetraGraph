"""
Scoring engine that converts empirical benchmark metrics into a
ranked operational score per algorithm for a given dataset profile.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from config import (
    CONFIDENCE_MARGIN_HIGH,
    CONFIDENCE_MARGIN_MED,
    FAMILY_DDOS_VOLUMETRIC,
    FAMILY_MALWARE_STATIC,
    TASK_MULTICLASS_MALWARE,
)


def compute_operational_score(
    empirical: Dict[str, Any],
    family: str,
    task: str,
    norm_max_latency_us: float = 6.0,
) -> float:
    """
    Compute a composite operational score from empirical benchmark metrics.

    Task-specific logic applies domain-weighted scoring to reflect real
    cybersecurity operational priorities.
    """
    f1     = empirical.get("mean_f1", 0.0)
    recall = empirical.get("mean_recall", 0.0)
    fpr    = empirical.get("mean_fpr", 0.0)
    lat    = empirical.get("mean_latency_us", norm_max_latency_us)
    lat_norm = min(1.0, lat / norm_max_latency_us)

    if task == TASK_MULTICLASS_MALWARE:
        # Malware: macro F1 is the primary and decisive metric for concept-drift robustness.
        # The four models are tightly clustered in recall (~0.198–0.201, delta < 0.0015),
        # so recall CANNOT act as a tie-breaker without producing arbitrary rankings.
        # Latency penalty is limited to at most 1% of score (0.01 * lat_norm).
        score = (
            0.98 * f1
            + 0.01 * recall
            - 0.01 * lat_norm
        )

    elif family == FAMILY_DDOS_VOLUMETRIC:
        # DDoS: FPR is operationally critical (false-positive blocks of legitimate traffic).
        # CatBoost achieves 0.0000 FPR; XGBoost 0.0015; RF 0.0066; LGB 0.0635.
        # Apply a large FPR penalty so that 0-FPR clearly beats 0.15%-FPR.
        # F1 equal → FPR determines winner; latency is a very distant tie-breaker.
        score = (
            0.40 * f1
            + 0.20 * recall
            - 0.35 * (fpr * 20.0)     # amplified: 0.01 FPR → -0.07 penalty
            - 0.05 * lat_norm
        )

    else:
        # Standard binary network intrusion: F1 + recall primary; latency secondary
        score = (
            0.40 * f1
            + 0.20 * recall
            - 0.25 * fpr
            - 0.15 * lat_norm
        )

    return round(float(score), 6)


def rank_algorithms(
    ds_registry: Dict[str, Any],
    family: str,
    task: str,
) -> List[Tuple[str, float]]:
    """
    Returns algorithms sorted by operational score descending.
    ds_registry: {algorithm_name: registry_entry}
    """
    scored = []
    for alg, entry in ds_registry.items():
        emp = entry.get("empirical_metrics", {})
        score = compute_operational_score(emp, family, task)
        scored.append((alg, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def compute_selection_confidence(ranked: List[Tuple[str, float]]) -> float:
    """
    Computes a selection confidence score in [0, 1].

    This represents confidence in the MODEL SELECTION decision —
    NOT the probability that the model's prediction is correct.

    High confidence: the top model clearly outscores the next best.
    Low confidence : two or more models are operationally equivalent.
    """
    if not ranked:
        return 0.0
    if len(ranked) == 1:
        return 1.0

    top_score  = ranked[0][1]
    next_score = ranked[1][1]
    margin = top_score - next_score

    if margin > CONFIDENCE_MARGIN_HIGH:
        # Clear winner
        base = 0.88
        confidence = min(0.99, base + margin * 2.0)
    elif margin > CONFIDENCE_MARGIN_MED:
        # Moderate advantage
        confidence = 0.70 + margin * 4.0
    else:
        # Near tie — explicitly flag
        confidence = max(0.50, 0.55 + margin * 10.0)

    return round(float(confidence), 4)
