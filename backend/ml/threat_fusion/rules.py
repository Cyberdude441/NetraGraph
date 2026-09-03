"""Transparent, deterministic symbolic reasoning rules for threat intelligence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import RULE_SET_VERSION
from .signals import SignalSeverity, SignalSource, ThreatSignal


@dataclass
class RuleEvaluationResult:
    """Outcome of evaluating an explicit symbolic heuristic rule."""
    rule_id: str
    rule_version: str = RULE_SET_VERSION
    triggered: bool = False
    severity: SignalSeverity = SignalSeverity.LOW
    confidence: float = 0.85
    risk_indicator: float = 0.0      # Suggested risk score contribution in [0, 1]
    input_signal_ids: List[str] = field(default_factory=list)
    explanation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class SymbolicRule(ABC):
    """Abstract base class for all deterministic symbolic heuristic rules."""
    rule_id: str
    rule_version: str = RULE_SET_VERSION
    category: str
    description: str

    @abstractmethod
    def evaluate(
        self,
        signals: List[ThreatSignal],
        context: Optional[Dict[str, Any]] = None,
    ) -> RuleEvaluationResult:
        pass


class RapidConnectivitySurgeRule(SymbolicRule):
    """RULE-01: Flags rapid increase in network connectivity or degree within short time frames."""
    rule_id = "RULE_RAPID_CONNECTIVITY_SURGE_V1"
    category = "topological_dynamics"
    description = "Detects accelerated expansion of direct connections over brief observation intervals."

    def evaluate(
        self,
        signals: List[ThreatSignal],
        context: Optional[Dict[str, Any]] = None,
    ) -> RuleEvaluationResult:
        ctx = context or {}
        degree_delta = ctx.get("degree_delta", 0)
        time_delta_hours = ctx.get("time_delta_hours", 24.0)

        # Trigger if >= 5 new connections established in < 6 hours
        triggered = bool(degree_delta >= 5 and time_delta_hours <= 6.0)

        if triggered:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                triggered=True,
                severity=SignalSeverity.HIGH,
                confidence=0.88,
                risk_indicator=0.75,
                explanation=(
                    f"Entity established {degree_delta} direct connections within {time_delta_hours:.1f} hours, "
                    "exhibiting sudden topological velocity."
                ),
                metadata={"degree_delta": degree_delta, "time_delta_hours": time_delta_hours},
            )
        return RuleEvaluationResult(rule_id=self.rule_id, triggered=False)


class TemporalBurstRule(SymbolicRule):
    """RULE-02: Flags anomalous temporal bursts of interactions in compact time windows."""
    rule_id = "RULE_TEMPORAL_BURST_V1"
    category = "temporal_pattern"
    description = "Identifies high-frequency interaction bursts occurring within a narrow temporal window."

    def evaluate(
        self,
        signals: List[ThreatSignal],
        context: Optional[Dict[str, Any]] = None,
    ) -> RuleEvaluationResult:
        temporal_signals = [s for s in signals if s.source in [SignalSource.TEMPORAL_BEHAVIOR, SignalSource.DT_GNN] and not s.is_missing]
        ctx = context or {}
        burst_count = ctx.get("burst_event_count", 0)
        burst_window_seconds = ctx.get("burst_window_seconds", 300.0)

        triggered = bool(burst_count >= 10 and burst_window_seconds <= 300.0)

        if triggered:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                triggered=True,
                severity=SignalSeverity.HIGH,
                confidence=0.90,
                risk_indicator=0.80,
                input_signal_ids=[s.signal_id for s in temporal_signals],
                explanation=(
                    f"Observed anomalous cluster of {burst_count} events within {burst_window_seconds:.0f} seconds, "
                    "indicating automated or coordinated operational burst."
                ),
                metadata={"burst_count": burst_count, "window_seconds": burst_window_seconds},
            )
        return RuleEvaluationResult(rule_id=self.rule_id, triggered=False)


class MultiSourceConvergenceRule(SymbolicRule):
    """RULE-03: Flags when multiple independent subsystems simultaneously indicate high threat."""
    rule_id = "RULE_MULTI_SOURCE_CONVERGENCE_V1"
    category = "cross_domain_consensus"
    description = "Triggers when two or more distinct analytical sources independently report elevated risk."

    def evaluate(
        self,
        signals: List[ThreatSignal],
        context: Optional[Dict[str, Any]] = None,
    ) -> RuleEvaluationResult:
        # Group valid signals by source
        high_sources: Dict[SignalSource, ThreatSignal] = {}
        for s in signals:
            if not s.is_missing and s.score is not None and s.score >= 0.70:
                high_sources[s.source] = s

        # Distinct sources reporting >= 0.70
        distinct_count = len(high_sources)
        triggered = distinct_count >= 2

        if triggered:
            src_names = [src.value for src in high_sources.keys()]
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                triggered=True,
                severity=SignalSeverity.CRITICAL,
                confidence=0.92,
                risk_indicator=0.88,
                input_signal_ids=[s.signal_id for s in high_sources.values()],
                explanation=(
                    f"Multi-source convergence: {distinct_count} independent analytical sources "
                    f"({', '.join(src_names)}) independently report elevated risk >= 0.70."
                ),
                metadata={"convergent_sources": src_names, "source_count": distinct_count},
            )
        return RuleEvaluationResult(rule_id=self.rule_id, triggered=False)


class InfrastructureReuseRule(SymbolicRule):
    """RULE-04: Flags infrastructure reuse across distinct cases or high betweenness bridge hubs."""
    rule_id = "RULE_INFRASTRUCTURE_REUSE_V1"
    category = "infrastructure_sharing"
    description = "Triggers when network artifacts are shared across multiple disparate evidence contexts."

    def evaluate(
        self,
        signals: List[ThreatSignal],
        context: Optional[Dict[str, Any]] = None,
    ) -> RuleEvaluationResult:
        ctx = context or {}
        shared_cases_count = ctx.get("shared_cases_count", 0)
        betweenness = ctx.get("betweenness_centrality", 0.0)

        triggered = bool(shared_cases_count >= 2 or betweenness >= 0.35)

        if triggered:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                triggered=True,
                severity=SignalSeverity.HIGH,
                confidence=0.85,
                risk_indicator=0.72,
                explanation=(
                    f"Infrastructure element is shared across {shared_cases_count} cases with betweenness {betweenness:.3f}, "
                    "suggesting pooled or proxy infrastructure."
                ),
                metadata={"shared_cases_count": shared_cases_count, "betweenness": betweenness},
            )
        return RuleEvaluationResult(rule_id=self.rule_id, triggered=False)


class DiscordantIntelligenceRule(SymbolicRule):
    """RULE-05: Flags significant contradiction between endpoint ML and graph/network representations."""
    rule_id = "RULE_DISCORDANT_INTELLIGENCE_V1"
    category = "analytical_conflict"
    description = "Highlights marked divergence between tabular endpoint models and topological GNN signals."

    def evaluate(
        self,
        signals: List[ThreatSignal],
        context: Optional[Dict[str, Any]] = None,
    ) -> RuleEvaluationResult:
        ml_signals = [s for s in signals if s.source == SignalSource.MODEL_A_E and not s.is_missing and s.score is not None]
        gnn_signals = [s for s in signals if s.source == SignalSource.DT_GNN and not s.is_missing and s.score is not None]

        if ml_signals and gnn_signals:
            ml_max = max(s.score for s in ml_signals)
            gnn_max = max(s.score for s in gnn_signals)
            diff = abs(ml_max - gnn_max)

            if diff >= 0.45:
                return RuleEvaluationResult(
                    rule_id=self.rule_id,
                    triggered=True,
                    severity=SignalSeverity.MEDIUM,
                    confidence=0.70,
                    risk_indicator=0.50,
                    input_signal_ids=[ml_signals[0].signal_id, gnn_signals[0].signal_id],
                    explanation=(
                        f"Discordant analytical signals: endpoint ML score ({ml_max:.2f}) diverges significantly "
                        f"from topological GNN score ({gnn_max:.2f}) by {diff:.2f}. Analyst review recommended."
                    ),
                    metadata={"ml_max": ml_max, "gnn_max": gnn_max, "divergence": diff},
                )
        return RuleEvaluationResult(rule_id=self.rule_id, triggered=False)


class SymbolicRuleEngine:
    """Evaluates a registry of deterministic symbolic heuristic rules against signals and context."""

    def __init__(self, rules: Optional[List[SymbolicRule]] = None):
        self.rules: List[SymbolicRule] = rules or [
            RapidConnectivitySurgeRule(),
            TemporalBurstRule(),
            MultiSourceConvergenceRule(),
            InfrastructureReuseRule(),
            DiscordantIntelligenceRule(),
        ]

    def evaluate_all(
        self,
        signals: List[ThreatSignal],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[RuleEvaluationResult]:
        """Evaluates all registered rules and returns their results deterministically."""
        results: List[RuleEvaluationResult] = []
        for rule in self.rules:
            res = rule.evaluate(signals, context=context)
            results.append(res)
        return results
