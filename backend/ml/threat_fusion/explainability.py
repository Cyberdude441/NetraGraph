"""Structured explainability generation and governance attributions."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .evidence import EvidenceChain
from .rules import RuleEvaluationResult
from .signals import ThreatSignal

GOVERNANCE_DISCLAIMER = (
    "Model-derived statistical correlation; not a determination of legal culpability, "
    "guilt, or causality. Provided as an analytical investigative lead requiring human verification."
)


class ExplainabilityEngine:
    """Produces structured, reproducible explanations from verified evidence and symbolic rules."""

    def generate_explanation(
        self,
        target_id: str,
        risk_score: float,
        confidence_score: float,
        severity: str,
        disagreement_score: float,
        supporting_signals: List[ThreatSignal],
        contradicting_signals: List[ThreatSignal],
        triggered_rules: List[RuleEvaluationResult],
        evidence_chain: EvidenceChain,
        weights_used: Dict[str, float],
    ) -> Dict[str, Any]:
        """Synthesizes structured factors and facts into an auditable explanation artifact."""
        # 1. Top Contributing (Supporting) Signals
        top_contributing = []
        for s in sorted(supporting_signals, key=lambda sig: (weights_used.get(sig.signal_id, 1.0) * (sig.score or 0.0)), reverse=True)[:5]:
            top_contributing.append({
                "signal_id": s.signal_id,
                "source": s.source.value,
                "signal_type": s.signal_type,
                "score": s.score,
                "confidence": s.confidence,
                "effective_weight": weights_used.get(s.signal_id, 1.0),
                "narrative": s.explanation,
                "provenance_id": s.provenance_id,
            })

        # 2. Top Contradicting Signals
        top_contradicting = []
        for s in sorted(contradicting_signals, key=lambda sig: (weights_used.get(sig.signal_id, 1.0) * (1.0 - (sig.score or 0.0))), reverse=True)[:5]:
            top_contradicting.append({
                "signal_id": s.signal_id,
                "source": s.source.value,
                "signal_type": s.signal_type,
                "score": s.score,
                "confidence": s.confidence,
                "effective_weight": weights_used.get(s.signal_id, 1.0),
                "narrative": s.explanation,
                "provenance_id": s.provenance_id,
            })

        # 3. Model vs Graph vs Rule contributions summary
        source_breakdown: Dict[str, float] = {}
        for s in supporting_signals + contradicting_signals:
            src = s.source.value
            source_breakdown[src] = round(source_breakdown.get(src, 0.0) + (s.score or 0.0) * weights_used.get(s.signal_id, 1.0), 3)

        # 4. Synthesize analytical summary narrative
        rule_names = [r.rule_id for r in triggered_rules if r.triggered]
        narrative_parts = [
            f"Threat assessment for target '{target_id}' indicates {severity} risk ({risk_score:.2f}) "
            f"with confidence {confidence_score:.2f} based on {evidence_chain.total_evidence_count} evidence records."
        ]

        if disagreement_score >= 0.25:
            narrative_parts.append(
                f"Significant analytical divergence detected across signals (disagreement index {disagreement_score:.2f}), "
                f"resulting in a confidence penalty."
            )

        if rule_names:
            narrative_parts.append(
                f"Evaluation triggered {len(rule_names)} symbolic heuristic rule(s): {', '.join(rule_names)}."
            )

        if top_contributing:
            top_fact = top_contributing[0]
            narrative_parts.append(
                f"Primary supporting signal from {top_fact['source']} ({top_fact['signal_type']}) with score {top_fact['score']}."
            )

        if top_contradicting:
            top_contra = top_contradicting[0]
            narrative_parts.append(
                f"Notable counter-indicator from {top_contra['source']} with low threat score {top_contra['score']}."
            )

        summary_narrative = " ".join(narrative_parts)

        return {
            "overall_risk": risk_score,
            "confidence": confidence_score,
            "severity": severity,
            "disagreement_index": disagreement_score,
            "top_contributing_signals": top_contributing,
            "top_contradicting_signals": top_contradicting,
            "triggered_rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_version": r.rule_version,
                    "severity": r.severity.value,
                    "explanation": r.explanation,
                }
                for r in triggered_rules
                if r.triggered
            ],
            "source_contributions": source_breakdown,
            "evidence_count": {
                "total": evidence_chain.total_evidence_count,
                "supporting": evidence_chain.supporting_count,
                "contradicting": evidence_chain.contradicting_count,
            },
            "summary_narrative": summary_narrative,
            "disclaimer": GOVERNANCE_DISCLAIMER,
        }
