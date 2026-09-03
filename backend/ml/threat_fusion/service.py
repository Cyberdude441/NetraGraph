"""Operational service orchestrating multi-source threat fusion and explainability."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from .assessment import ThreatAssessment
from .config import ThreatFusionConfig
from .evidence import EvidenceChain
from .explainability import ExplainabilityEngine, GOVERNANCE_DISCLAIMER
from .fusion import ThreatFusionEngine
from .provenance import ProvenanceRecord, ProvenanceTracker
from .rules import RuleEvaluationResult, SymbolicRuleEngine
from .signals import SignalSeverity, SignalSource, ThreatSignal

logger = logging.getLogger("ThreatFusionService")

# Safe Prometheus Metrics Registration
try:
    from prometheus_client import Counter, Histogram
    THREAT_FUSION_REQUESTS_TOTAL = Counter(
        "netragraph_threat_fusion_requests_total",
        "Total threat fusion assessments requested",
        ["status"],
    )
    THREAT_FUSION_FAILURES_TOTAL = Counter(
        "netragraph_threat_fusion_failures_total",
        "Total threat fusion assessment failures",
        ["reason"],
    )
    THREAT_FUSION_DURATION_SECONDS = Histogram(
        "netragraph_threat_fusion_duration_seconds",
        "Threat fusion evaluation latency in seconds",
        buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    )
    THREAT_FUSION_HIGH_RISK_TOTAL = Counter(
        "netragraph_threat_fusion_high_risk_total",
        "Total threat assessments resulting in high or critical severity",
    )
    METRICS_AVAILABLE = True
except Exception:
    METRICS_AVAILABLE = False


class ThreatFusionService:
    """Singleton service orchestrating multi-source threat fusion and explainable intelligence."""

    _instance: Optional[ThreatFusionService] = None

    def __init__(self, config: Optional[ThreatFusionConfig] = None):
        self.config = config or ThreatFusionConfig()
        self.fusion_engine = ThreatFusionEngine(self.config)
        self.rule_engine = SymbolicRuleEngine()
        self.explainability_engine = ExplainabilityEngine()
        self.provenance_tracker = ProvenanceTracker()

    @classmethod
    def get_instance(cls) -> ThreatFusionService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def validate_limits(self, signals: List[ThreatSignal], context: Optional[Dict[str, Any]] = None) -> None:
        """Enforces resource safety limits to reject pathological payloads."""
        limits = self.config.safety_limits
        if len(signals) > limits.max_signals_per_request:
            if METRICS_AVAILABLE:
                THREAT_FUSION_FAILURES_TOTAL.labels(reason="payload_too_large").inc()
            raise HTTPException(
                status_code=413,
                detail=f"Request contains {len(signals)} signals, exceeding maximum limit of {limits.max_signals_per_request}.",
            )

    def assess_target(
        self,
        target_id: str,
        signals: List[ThreatSignal],
        context: Optional[Dict[str, Any]] = None,
        target_type: str = "entity",
    ) -> ThreatAssessment:
        """Executes end-to-end threat assessment across input signals and symbolic rules."""
        start_time = time.time()
        self.validate_limits(signals, context)

        try:
            # 1. Register provenance for all signals
            for sig in signals:
                if not sig.provenance_id:
                    rec = ProvenanceRecord(
                        source=sig.source,
                        source_type=sig.signal_type,
                        collection_timestamp=sig.timestamp,
                    )
                    sig.provenance_id = self.provenance_tracker.register(rec)

            # 2. Evaluate symbolic rules
            rule_results: List[RuleEvaluationResult] = self.rule_engine.evaluate_all(signals, context=context)
            triggered_rules = [r for r in rule_results if r.triggered]

            # Convert triggered rules into supplementary symbolic signals
            rule_signals: List[ThreatSignal] = []
            for r in triggered_rules:
                r_sig = ThreatSignal(
                    source=SignalSource.SYMBOLIC_RULE,
                    entity_id=target_id,
                    signal_type=r.rule_id,
                    score=r.risk_indicator,
                    confidence=r.confidence,
                    timestamp=time.time(),
                    severity=r.severity,
                    explanation=r.explanation,
                    metadata=r.metadata,
                )
                rule_signals.append(r_sig)

            all_signals = signals + rule_signals

            # 3. Fuse signals deterministically
            fusion_result = self.fusion_engine.fuse_signals(
                signals=all_signals,
                target_id=target_id,
                evaluation_timestamp=time.time(),
            )

            risk_score = fusion_result["risk_score"]
            confidence_score = fusion_result["confidence_score"]
            disagreement_score = fusion_result["disagreement_score"]
            severity = fusion_result["severity"].value
            supporting = fusion_result["supporting_signals"]
            contradicting = fusion_result["contradicting_signals"]
            evidence_chain: EvidenceChain = fusion_result["evidence_chain"]
            weights_used = fusion_result["weights_used"]

            # 4. Generate structured explainability
            explanation = self.explainability_engine.generate_explanation(
                target_id=target_id,
                risk_score=risk_score,
                confidence_score=confidence_score,
                severity=severity,
                disagreement_score=disagreement_score,
                supporting_signals=supporting,
                contradicting_signals=contradicting,
                triggered_rules=rule_results,
                evidence_chain=evidence_chain,
                weights_used=weights_used,
            )

            # 5. Structure evidence chain for response
            evidence_dict = {
                "total_evidence_count": evidence_chain.total_evidence_count,
                "supporting_count": evidence_chain.supporting_count,
                "contradicting_count": evidence_chain.contradicting_count,
                "top_supporting": [
                    {
                        "evidence_id": e.evidence_id,
                        "source": e.source.value,
                        "raw_score": e.raw_score,
                        "weight": e.weight,
                        "narrative_fact": e.narrative_fact,
                        "provenance_id": e.provenance_id,
                    }
                    for e in evidence_chain.get_top_supporting(k=5)
                ],
                "top_contradicting": [
                    {
                        "evidence_id": e.evidence_id,
                        "source": e.source.value,
                        "raw_score": e.raw_score,
                        "weight": e.weight,
                        "narrative_fact": e.narrative_fact,
                        "provenance_id": e.provenance_id,
                    }
                    for e in evidence_chain.get_top_contradicting(k=5)
                ],
            }

            # 6. Build final ThreatAssessment object
            assessment = ThreatAssessment(
                target_id=target_id,
                target_type=target_type,
                risk_score=risk_score,
                confidence_score=confidence_score,
                disagreement_score=disagreement_score,
                severity=severity,
                fusion_version=self.config.fusion_version,
                rule_set_version=self.config.rule_set_version,
                supporting_signals_count=len(supporting),
                contradicting_signals_count=len(contradicting),
                triggered_rules_count=len(triggered_rules),
                signals_summary=[
                    {
                        "signal_id": s.signal_id,
                        "source": s.source.value,
                        "signal_type": s.signal_type,
                        "score": s.score,
                        "confidence": s.confidence,
                        "is_missing": s.is_missing,
                    }
                    for s in all_signals
                ],
                triggered_rules=[
                    {
                        "rule_id": r.rule_id,
                        "rule_version": r.rule_version,
                        "severity": r.severity.value,
                        "explanation": r.explanation,
                    }
                    for r in triggered_rules
                ],
                evidence_chain=evidence_dict,
                explanation=explanation,
                disclaimer=GOVERNANCE_DISCLAIMER,
            )

            duration = time.time() - start_time
            if METRICS_AVAILABLE:
                THREAT_FUSION_REQUESTS_TOTAL.labels(status="success").inc()
                THREAT_FUSION_DURATION_SECONDS.observe(duration)
                if severity in ["HIGH", "CRITICAL"]:
                    THREAT_FUSION_HIGH_RISK_TOTAL.inc()

            return assessment

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Error during threat fusion assessment for {target_id}: {exc}")
            if METRICS_AVAILABLE:
                THREAT_FUSION_REQUESTS_TOTAL.labels(status="error").inc()
                THREAT_FUSION_FAILURES_TOTAL.labels(reason="internal_error").inc()
            raise HTTPException(
                status_code=500,
                detail="Threat fusion assessment failed during processing.",
            )


# Global singleton instance
threat_fusion_service = ThreatFusionService.get_instance()
