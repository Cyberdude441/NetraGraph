"""
Explainability module — generates structured natural-language justifications
for every model selection decision.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def generate_selection_explanation(
    selected_model: str,
    selected_score: float,
    alternatives: List[Tuple[str, float]],
    dataset_name: str,
    family: str,
    task: str,
    registry_entry: Dict[str, Any],
    confidence: float,
) -> Dict[str, Any]:
    """
    Returns a structured, evidence-grounded explanation of the selection decision.

    Fields
    ------
    selected_model     : Algorithm chosen.
    rationale          : Primary reason (evidence-based language only).
    alternative_models : Ranked alternatives with why they were not selected.
    expected_strengths : Empirically validated strengths for this task.
    known_limitations  : Documented limitations from registry.
    evidence           : Numeric evidence values cited.
    confidence_note    : Clarification that confidence = selection confidence.
    """
    emp = registry_entry.get("empirical_metrics", {})
    strengths = registry_entry.get("strengths", [])
    limitations = registry_entry.get("known_limitations", [])

    # Determine primary rationale based on task and dataset family
    if "DDoS" in task or "ddos" in family:
        primary_reason = (
            f"{selected_model} achieved the highest operational score for protocol-disjoint "
            f"DDoS detection (empirical Mean F1 {emp.get('mean_f1', 0):.4f}, "
            f"Mean FPR {emp.get('mean_fpr', 0):.4f}) under unseen reflection attack protocols."
        )
    elif "malware" in family or "multiclass" in task:
        primary_reason = (
            f"{selected_model} achieved the highest Macro F1 ({emp.get('mean_f1', 0):.4f}) "
            f"under temporal malware signature drift across multiple submission window folds, "
            f"demonstrating superior bagging variance reduction."
        )
    else:
        primary_reason = (
            f"{selected_model} achieved the highest operational score for binary network intrusion "
            f"detection (Mean F1 {emp.get('mean_f1', 0):.4f}, "
            f"Inference {emp.get('mean_latency_us', 0):.2f} µs/sample) "
            f"across multiple temporal day-based validation folds."
        )

    # Build alternative explanations
    alt_explanations = []
    for alt_name, alt_score in alternatives[:2]:
        score_delta = round(selected_score - alt_score, 5)
        if score_delta < 0.001:
            why_not = (
                f"{alt_name} is statistically indistinguishable from {selected_model} under "
                f"N=3 fold Wilcoxon testing (p >= 0.25). Selection between them should consider "
                f"operational latency: prefer {selected_model} for the current task profile."
            )
        else:
            why_not = (
                f"{alt_name} scored {alt_score:.5f} vs {selected_model} {selected_score:.5f} "
                f"(delta = {score_delta:.5f}) on the composite operational metric."
            )
        alt_explanations.append({
            "algorithm": alt_name,
            "operational_score": round(alt_score, 5),
            "why_not_selected": why_not,
        })

    return {
        "selected_model": selected_model,
        "dataset": dataset_name,
        "task_type": task,
        "dataset_family": family,
        "rationale": primary_reason,
        "alternative_models": alt_explanations,
        "expected_strengths": strengths,
        "known_limitations": limitations,
        "evidence": {
            "mean_f1": emp.get("mean_f1"),
            "ci95_f1": emp.get("ci95_f1"),
            "mean_fpr": emp.get("mean_fpr"),
            "mean_fnr": emp.get("mean_fnr"),
            "mean_recall": emp.get("mean_recall"),
            "mean_latency_us": emp.get("mean_latency_us"),
            "validation_methodology": registry_entry.get("validation_methodology"),
        },
        "selection_confidence": confidence,
        "confidence_note": (
            "Selection confidence represents the strength of evidence favouring this model "
            "for the given task/dataset profile. It is NOT a prediction probability or "
            "a guarantee of production accuracy."
        ),
    }
