"""
Explainability Engine for NetraGraph Model Selection V2.
Generates structured, evidence-grounded decision audits for domain-aware model selection.
"""
from __future__ import annotations

from typing import Any, Dict, List
try:
    from training.model_selection_v2.confidence import ConfidenceReport
    from training.model_selection_v2.config import SecurityDomain
    from training.model_selection_v2.domain_profiler import DomainProfileResult
    from training.model_selection_v2.domain_selector import DomainSelectionDecision
except ImportError:
    from confidence import ConfidenceReport
    from config import SecurityDomain
    from domain_profiler import DomainProfileResult
    from domain_selector import DomainSelectionDecision


class ExplainabilityEngine:
    """Generates human and machine-readable explanations for V2 routing decisions."""

    def explain_routing_decision(
        self,
        domain_profile: DomainProfileResult,
        selection_decision: DomainSelectionDecision,
        confidence_report: ConfidenceReport,
        representation_used: str,
        is_fallback_active: bool,
    ) -> Dict[str, Any]:
        """
        Produce comprehensive structured explanation dictionary.
        """
        explanation = {
            "summary": (
                f"Routed to [{domain_profile.domain.value.upper()}] using representation [{representation_used}] "
                f"with selected model [{selection_decision.selected_model}] (Confidence: {confidence_report.composite_confidence:.2%})"
            ),
            "domain_profiling": {
                "detected_domain": domain_profile.domain.value,
                "confidence": domain_profile.confidence,
                "evidence_signals": domain_profile.evidence,
                "matched_signatures": domain_profile.matched_signatures,
                "domain_probabilities": domain_profile.domain_probabilities,
            },
            "representation_selection": {
                "representation_name": representation_used,
                "is_structural_v2": (representation_used == "MALWARE_STRUCTURAL_V2"),
                "rationale": (
                    "Engineered structural fuzzy hashes, VT risk tiers, and executable grouping to prevent temporal drift"
                    if representation_used == "MALWARE_STRUCTURAL_V2"
                    else "Standardized numerical/flow preprocessing matrix"
                ),
            },
            "model_selection": {
                "selected_model": selection_decision.selected_model,
                "fallback_model": selection_decision.fallback_model,
                "selection_confidence": selection_decision.selection_confidence,
                "rationale": selection_decision.rationale,
                "candidate_scores": [
                    {
                        "model": b.model_name,
                        "overall_score": b.overall_score,
                        "performance_f1": b.performance_score,
                        "latency_score": b.latency_score,
                        "fpr_score": b.fpr_score,
                        "minority_recall_score": b.minority_recall_score,
                    }
                    for b in selection_decision.score_breakdown
                ],
            },
            "uncertainty_and_safety": {
                "confidence_tier": confidence_report.confidence_tier.value,
                "requires_fallback": confidence_report.requires_fallback,
                "is_fallback_active": is_fallback_active,
                "prediction_margin": confidence_report.prediction_margin,
                "prediction_entropy": confidence_report.prediction_entropy,
                "safety_reason": confidence_report.reason,
            },
        }
        return explanation
