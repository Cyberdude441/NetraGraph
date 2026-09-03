"""NetraGraph Phase 12: Neuro-Symbolic Threat Fusion & Explainable Intelligence Module."""
from __future__ import annotations

from .assessment import ThreatAssessment
from .config import (
    ASSESSMENT_SCHEMA_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    FUSION_VERSION,
    RULE_SET_VERSION,
    DisagreementConfig,
    SafetyLimitsConfig,
    SourceWeightsConfig,
    TemporalDecayConfig,
    TemporalDecayType,
    ThreatFusionConfig,
)
from .evidence import EvidenceChain, EvidenceItem, EvidenceOrientation
from .explainability import GOVERNANCE_DISCLAIMER, ExplainabilityEngine
from .fusion import ThreatFusionEngine
from .provenance import ProvenanceRecord, ProvenanceTracker
from .rules import (
    DiscordantIntelligenceRule,
    InfrastructureReuseRule,
    MultiSourceConvergenceRule,
    RapidConnectivitySurgeRule,
    RuleEvaluationResult,
    SymbolicRule,
    SymbolicRuleEngine,
    TemporalBurstRule,
)
from .service import ThreatFusionService, threat_fusion_service
from .signals import (
    SignalSeverity,
    SignalSource,
    ThreatSignal,
    calculate_severity,
    normalize_score,
)

__all__ = [
    "FUSION_VERSION",
    "RULE_SET_VERSION",
    "EVIDENCE_SCHEMA_VERSION",
    "ASSESSMENT_SCHEMA_VERSION",
    "GOVERNANCE_DISCLAIMER",
    "TemporalDecayType",
    "SourceWeightsConfig",
    "TemporalDecayConfig",
    "DisagreementConfig",
    "SafetyLimitsConfig",
    "ThreatFusionConfig",
    "SignalSource",
    "SignalSeverity",
    "ThreatSignal",
    "normalize_score",
    "calculate_severity",
    "ProvenanceRecord",
    "ProvenanceTracker",
    "EvidenceOrientation",
    "EvidenceItem",
    "EvidenceChain",
    "SymbolicRule",
    "RuleEvaluationResult",
    "RapidConnectivitySurgeRule",
    "TemporalBurstRule",
    "MultiSourceConvergenceRule",
    "InfrastructureReuseRule",
    "DiscordantIntelligenceRule",
    "SymbolicRuleEngine",
    "ThreatFusionEngine",
    "ExplainabilityEngine",
    "ThreatAssessment",
    "ThreatFusionService",
    "threat_fusion_service",
]
