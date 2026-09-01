"""
Explanation & Forensic Audit Logger for NetraGraph Shadow Inference.

Generates structured explanations for shadow comparisons, highlighting prediction
agreements, disagreements, risk deltas, and research limitations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from schemas import ComparisonResult, ShadowResult


def generate_shadow_explanation(
    shadow_result: ShadowResult,
) -> Dict[str, Any]:
    """
    Generate an evidence-grounded structured explanation of a shadow inference comparison.
    """
    prod = shadow_result.production
    adapt = shadow_result.adaptive
    comp = shadow_result.comparison

    if comp.prediction_agreement:
        agreement_desc = (
            f"Production model '{prod.model}' and adaptive model '{adapt.model}' AGREED on prediction: "
            f"'{prod.prediction}'. Risk scores: Production={prod.risk_score:.4f}, Adaptive={adapt.risk_score:.4f} "
            f"(Delta: {comp.risk_delta:.4f})."
        )
    else:
        agreement_desc = (
            f"DISAGREEMENT DETECTED (Severity: {comp.disagreement_severity}): Production '{prod.model}' "
            f"predicted '{prod.prediction}' (Risk: {prod.risk_score:.4f}), while Adaptive '{adapt.model}' "
            f"predicted '{adapt.prediction}' (Risk: {adapt.risk_score:.4f}). Risk Delta: {comp.risk_delta:.4f}."
        )

    model_choice_reason = (
        f"Adaptive layer selected '{adapt.model}' with selection confidence {adapt.selection_confidence:.4f}. "
        f"Rationale: {adapt.rationale}"
    )

    alternatives_summary = [
        f"{alt.get('algorithm')}: score {alt.get('operational_score', 0):.4f}"
        for alt in adapt.alternatives[:2]
    ]

    return {
        "request_id": shadow_result.request_id,
        "dataset_name": shadow_result.dataset_name,
        "agreement_summary": agreement_desc,
        "model_selection_rationale": model_choice_reason,
        "alternatives_considered": alternatives_summary,
        "latency_breakdown": {
            "production_latency_ms": prod.latency_ms,
            "adaptive_selection_latency_ms": adapt.selection_latency_ms,
            "adaptive_inference_latency_ms": adapt.inference_latency_ms,
            "adaptive_total_latency_ms": adapt.total_latency_ms,
            "net_latency_delta_ms": comp.latency_delta_ms,
        },
        "research_limitations": [
            "SHADOW MODE ONLY: Adaptive path is completely isolated and has NOT modified production output.",
            "Confidence score represents MODEL SELECTION evidence strength, NOT prediction probability.",
            "Agreement or benchmark advantage does not constitute proof of infallible real-world superiority.",
            "Any future production deployment requires separate formal validation and signoff.",
        ],
    }
