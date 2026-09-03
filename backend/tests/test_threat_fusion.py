"""Comprehensive test suite for Phase 12: Neuro-Symbolic Threat Fusion & Explainable Intelligence."""
from __future__ import annotations

import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app
from ml.threat_fusion.assessment import ThreatAssessment
from ml.threat_fusion.config import (
    ASSESSMENT_SCHEMA_VERSION,
    FUSION_VERSION,
    RULE_SET_VERSION,
    ThreatFusionConfig,
)
from ml.threat_fusion.evidence import EvidenceChain, EvidenceItem, EvidenceOrientation
from ml.threat_fusion.explainability import GOVERNANCE_DISCLAIMER, ExplainabilityEngine
from ml.threat_fusion.fusion import ThreatFusionEngine
from ml.threat_fusion.provenance import ProvenanceRecord, ProvenanceTracker
from ml.threat_fusion.rules import (
    DiscordantIntelligenceRule,
    InfrastructureReuseRule,
    MultiSourceConvergenceRule,
    RapidConnectivitySurgeRule,
    RuleEvaluationResult,
    SymbolicRuleEngine,
    TemporalBurstRule,
)
from ml.threat_fusion.service import ThreatFusionService, threat_fusion_service
from ml.threat_fusion.signals import (
    SignalSeverity,
    SignalSource,
    ThreatSignal,
    calculate_severity,
    normalize_score,
)


# ============================================================================
# 1. Signal Validation & Normalization
# ============================================================================

def test_01_signal_validation_and_typing():
    """Verifies that ThreatSignal constructs correctly with typed sources and severities."""
    sig = ThreatSignal(
        source=SignalSource.MODEL_A_E,
        entity_id="ENT-1001",
        signal_type="phishing-url",
        score=0.88,
        confidence=0.92,
        explanation="High probability of phishing domain",
    )
    assert sig.source == SignalSource.MODEL_A_E
    assert sig.entity_id == "ENT-1001"
    assert sig.score == 0.88
    assert sig.confidence == 0.92
    assert sig.severity == SignalSeverity.CRITICAL
    assert not sig.is_missing
    assert sig.provenance_id is not None


def test_02_score_normalization_bounds():
    """Verifies that scores are clamped to [0.0, 1.0] and non-numeric values become None."""
    assert normalize_score(0.75) == 0.75
    assert normalize_score(1.50) == 1.0
    assert normalize_score(-0.35) == 0.0
    assert normalize_score("0.91") == 0.91
    assert normalize_score(None) is None
    assert normalize_score("invalid") is None
    assert normalize_score(float("nan")) is None
    assert normalize_score(float("inf")) is None


def test_03_missing_values_explicit_handling():
    """Verifies that missing signals are explicitly recorded without fabricating score or confidence."""
    missing = ThreatSignal.create_missing(
        source=SignalSource.DT_GNN,
        entity_id="ENT-2002",
        signal_type="node_threat_risk",
        explanation="Graph snapshot unavailable",
    )
    assert missing.is_missing is True
    assert missing.score is None
    assert missing.confidence == 0.0
    assert missing.severity == SignalSeverity.LOW


# ============================================================================
# 2. Confidence Separation & Conflict Handling
# ============================================================================

def test_04_confidence_handling_separated_from_risk():
    """Validates invariant: High risk score MUST NOT automatically mean high confidence."""
    engine = ThreatFusionEngine()
    # Scenario: Sparse, single uncorroborated high risk signal with modest confidence
    sparse_signal = [
        ThreatSignal(
            source=SignalSource.EXTERNAL,
            entity_id="ENT-3003",
            signal_type="osint_tip",
            score=0.95,
            confidence=0.55,
        )
    ]
    result = engine.fuse_signals(sparse_signal, target_id="ENT-3003")
    assert result["risk_score"] >= 0.90
    assert result["confidence_score"] <= 0.60
    assert result["risk_score"] != result["confidence_score"]


def test_05_conflicting_signals_detection_and_penalty():
    """Verifies that opposing signals create a high disagreement score and reduce confidence."""
    engine = ThreatFusionEngine()
    # Model A says very high risk (0.90), DT-GNN says very low risk (0.10)
    conflicting = [
        ThreatSignal(
            source=SignalSource.MODEL_A_E,
            entity_id="ENT-4004",
            signal_type="intrusion",
            score=0.90,
            confidence=0.90,
        ),
        ThreatSignal(
            source=SignalSource.DT_GNN,
            entity_id="ENT-4004",
            signal_type="node_threat_risk",
            score=0.10,
            confidence=0.90,
        ),
    ]
    result = engine.fuse_signals(conflicting, target_id="ENT-4004")
    assert result["disagreement_score"] > 0.30
    # Confidence should be penalized due to contradiction
    assert result["confidence_score"] < 0.70


def test_06_supporting_signals_identification():
    """Verifies that signals with score >= threshold are partitioned into supporting signals."""
    engine = ThreatFusionEngine()
    signals = [
        ThreatSignal(source=SignalSource.MODEL_A_E, entity_id="E1", score=0.85),
        ThreatSignal(source=SignalSource.DT_GNN, entity_id="E1", score=0.72),
        ThreatSignal(source=SignalSource.GRAPH_ANOMALY, entity_id="E1", score=0.20),
    ]
    result = engine.fuse_signals(signals, target_id="E1")
    supporting = result["supporting_signals"]
    assert len(supporting) == 2
    for s in supporting:
        assert s.score >= 0.50


def test_07_contradicting_signals_identification():
    """Verifies that signals with score < threshold are partitioned into contradicting signals."""
    engine = ThreatFusionEngine()
    signals = [
        ThreatSignal(source=SignalSource.MODEL_A_E, entity_id="E1", score=0.85),
        ThreatSignal(source=SignalSource.GRAPH_CENTRALITY, entity_id="E1", score=0.25),
        ThreatSignal(source=SignalSource.COMMUNITY, entity_id="E1", score=0.15),
    ]
    result = engine.fuse_signals(signals, target_id="E1")
    contradicting = result["contradicting_signals"]
    assert len(contradicting) == 2
    for s in contradicting:
        assert s.score < 0.50


# ============================================================================
# 3. Temporal Decay & Historical Evidence Preservation
# ============================================================================

def test_08_temporal_decay_mathematical_formulation():
    """Verifies that older signals receive attenuated weights via half-life decay."""
    engine = ThreatFusionEngine()
    ref_time = 1700000000.0
    seven_days = 86400.0 * 7.0

    recent_weight = engine.calculate_temporal_weight(
        base_weight=1.0,
        signal_timestamp=ref_time,
        ref_timestamp=ref_time,
    )
    assert math.isclose(recent_weight, 1.0, rel_tol=1e-3)

    one_halflife_old_weight = engine.calculate_temporal_weight(
        base_weight=1.0,
        signal_timestamp=ref_time - seven_days,
        ref_timestamp=ref_time,
    )
    # At exactly one half-life, weight should be ~0.50
    assert math.isclose(one_halflife_old_weight, 0.50, rel_tol=1e-2)


def test_09_historical_evidence_preservation():
    """Verifies that historical evidence is never discarded even when decayed to floor."""
    engine = ThreatFusionEngine()
    ref_time = 1700000000.0
    one_year_ago = ref_time - (86400.0 * 365.0)

    very_old_weight = engine.calculate_temporal_weight(
        base_weight=1.0,
        signal_timestamp=one_year_ago,
        ref_timestamp=ref_time,
    )
    # Must remain at or above min_weight_floor (0.10)
    assert very_old_weight >= 0.10

    # Ensure it appears in the resulting evidence chain
    signals = [
        ThreatSignal(
            source=SignalSource.MODEL_A_E,
            entity_id="ENT-OLD",
            score=0.85,
            timestamp=one_year_ago,
            explanation="Historic intrusion record",
        )
    ]
    res = engine.fuse_signals(signals, target_id="ENT-OLD", evaluation_timestamp=ref_time)
    assert res["evidence_chain"].total_evidence_count == 1
    assert res["evidence_chain"].supporting_evidence[0].weight >= 0.10


# ============================================================================
# 4. Symbolic Rule Engine
# ============================================================================

def test_10_symbolic_rule_rapid_connectivity_surge():
    """Verifies RULE_RAPID_CONNECTIVITY_SURGE triggering on sudden degree spikes."""
    rule = RapidConnectivitySurgeRule()
    # Triggering condition: degree_delta >= 5 in <= 6 hours
    res_triggered = rule.evaluate([], context={"degree_delta": 8, "time_delta_hours": 3.0})
    assert res_triggered.triggered is True
    assert res_triggered.severity == SignalSeverity.HIGH
    assert "degree_delta" in res_triggered.metadata

    # Non-triggering condition: degree_delta small or over longer duration
    res_normal = rule.evaluate([], context={"degree_delta": 2, "time_delta_hours": 24.0})
    assert res_normal.triggered is False


def test_11_symbolic_rule_temporal_burst():
    """Verifies RULE_TEMPORAL_BURST triggering on high interaction frequency."""
    rule = TemporalBurstRule()
    res_triggered = rule.evaluate([], context={"burst_event_count": 15, "burst_window_seconds": 120.0})
    assert res_triggered.triggered is True
    assert res_triggered.risk_indicator >= 0.75

    res_normal = rule.evaluate([], context={"burst_event_count": 3, "burst_window_seconds": 600.0})
    assert res_normal.triggered is False


def test_12_symbolic_rule_multi_source_convergence():
    """Verifies RULE_MULTI_SOURCE_CONVERGENCE triggering on cross-subsystem consensus."""
    rule = MultiSourceConvergenceRule()
    convergent_signals = [
        ThreatSignal(source=SignalSource.MODEL_A_E, score=0.85),
        ThreatSignal(source=SignalSource.DT_GNN, score=0.80),
        ThreatSignal(source=SignalSource.GRAPH_ANOMALY, score=0.75),
    ]
    res = rule.evaluate(convergent_signals)
    assert res.triggered is True
    assert res.severity == SignalSeverity.CRITICAL
    assert res.metadata["source_count"] >= 2


def test_13_symbolic_rule_discordant_intelligence():
    """Verifies RULE_DISCORDANT_INTELLIGENCE triggering on ML vs GNN divergence."""
    rule = DiscordantIntelligenceRule()
    divergent_signals = [
        ThreatSignal(source=SignalSource.MODEL_A_E, score=0.90),
        ThreatSignal(source=SignalSource.DT_GNN, score=0.30),
    ]
    res = rule.evaluate(divergent_signals)
    assert res.triggered is True
    assert res.metadata["divergence"] >= 0.45


def test_14_symbolic_rule_engine_non_triggering_clean_state():
    """Verifies that rule engine operates cleanly without false alarms on baseline traffic."""
    engine = SymbolicRuleEngine()
    benign_signals = [
        ThreatSignal(source=SignalSource.MODEL_A_E, score=0.20),
        ThreatSignal(source=SignalSource.DT_GNN, score=0.15),
    ]
    results = engine.evaluate_all(benign_signals, context={"degree_delta": 1, "time_delta_hours": 48.0})
    triggered = [r for r in results if r.triggered]
    assert len(triggered) == 0


# ============================================================================
# 5. Evidence & Provenance Traceability
# ============================================================================

def test_15_evidence_chain_generation_and_traceability():
    """Verifies that evidence items link to signal IDs and answer 'what caused this score'."""
    service = ThreatFusionService()
    signals = [
        ThreatSignal(source=SignalSource.MODEL_A_E, entity_id="E-TRACE", score=0.92, explanation="Session intrusion detected"),
        ThreatSignal(source=SignalSource.DT_GNN, entity_id="E-TRACE", score=0.88, explanation="Elevated temporal risk cluster"),
        ThreatSignal(source=SignalSource.GRAPH_ANOMALY, entity_id="E-TRACE", score=0.15, explanation="Standard degree centrality"),
    ]
    assessment = service.assess_target("E-TRACE", signals)
    ev_chain = assessment.evidence_chain
    assert ev_chain["total_evidence_count"] >= 3
    assert ev_chain["supporting_count"] >= 2
    assert ev_chain["contradicting_count"] >= 1
    # Check top supporting evidence record
    top_sup = ev_chain["top_supporting"][0]
    assert top_sup["raw_score"] >= 0.80
    assert "Session intrusion detected" in top_sup["narrative_fact"] or "Elevated" in top_sup["narrative_fact"]


def test_16_provenance_dag_tracking_and_no_fabrication():
    """Verifies that provenance tracker registers records and explicitly handles missing lineage."""
    tracker = ProvenanceTracker()
    rec = ProvenanceRecord(
        source=SignalSource.MODEL_A_E,
        source_type="intrusion",
        collection_timestamp=1700000000.0,
        transformation_performed="feature_scaling_and_inference",
        model_or_rule_version="v1.0",
    )
    pid = tracker.register(rec)
    retrieved = tracker.get(pid)
    assert retrieved is not None
    assert retrieved.is_available is True
    assert retrieved.transformation_performed == "feature_scaling_and_inference"

    # Test explicit unavailable provenance record
    unavail = ProvenanceRecord.create_unavailable(source=SignalSource.EXTERNAL)
    assert unavail.is_available is False
    assert unavail.transformation_performed == "unavailable"


# ============================================================================
# 6. Determinism, Bounds & Severity Mapping
# ============================================================================

def test_17_deterministic_fusion_guarantee():
    """Verifies that identical inputs yield strictly identical assessments."""
    service = ThreatFusionService()
    signals = [
        ThreatSignal(signal_id="SIG-FIXED-1", source=SignalSource.MODEL_A_E, entity_id="E-DET", score=0.80, timestamp=1700000000.0),
        ThreatSignal(signal_id="SIG-FIXED-2", source=SignalSource.DT_GNN, entity_id="E-DET", score=0.75, timestamp=1700000100.0),
    ]
    res1 = service.assess_target("E-DET", signals)
    res2 = service.assess_target("E-DET", signals)

    assert res1.risk_score == res2.risk_score
    assert res1.confidence_score == res2.confidence_score
    assert res1.disagreement_score == res2.disagreement_score
    assert res1.severity == res2.severity
    assert res1.triggered_rules_count == res2.triggered_rules_count


def test_18_risk_and_confidence_strict_bounds():
    """Verifies that risk and confidence values are strictly bounded in [0.0, 1.0]."""
    assessment = ThreatAssessment(
        target_id="E-BOUNDS",
        risk_score=0.9999,
        confidence_score=0.0001,
        severity="CRITICAL",
    )
    assert 0.0 <= assessment.risk_score <= 1.0
    assert 0.0 <= assessment.confidence_score <= 1.0

    with pytest.raises(ValueError):
        ThreatAssessment(target_id="E-ERR", risk_score=1.5, confidence_score=0.5, severity="HIGH")


def test_19_severity_mapping_consistency():
    """Verifies deterministic mapping of scores to severity tiers."""
    assert calculate_severity(0.85) == SignalSeverity.CRITICAL
    assert calculate_severity(0.65) == SignalSeverity.HIGH
    assert calculate_severity(0.45) == SignalSeverity.MEDIUM
    assert calculate_severity(0.20) == SignalSeverity.LOW
    assert calculate_severity(None) == SignalSeverity.LOW


# ============================================================================
# 7. Explainability & Governance Disclaimer
# ============================================================================

def test_20_explainability_structure_and_mandatory_disclaimer():
    """Verifies structured explanation contents and mandatory presence of non-causal disclaimer."""
    service = ThreatFusionService()
    signals = [
        ThreatSignal(source=SignalSource.MODEL_A_E, entity_id="E-EXPL", score=0.91),
        ThreatSignal(source=SignalSource.DT_GNN, entity_id="E-EXPL", score=0.85),
    ]
    assessment = service.assess_target("E-EXPL", signals)
    expl = assessment.explanation

    assert "overall_risk" in expl
    assert "confidence" in expl
    assert "top_contributing_signals" in expl
    assert "summary_narrative" in expl
    assert "disclaimer" in expl
    assert assessment.disclaimer == GOVERNANCE_DISCLAIMER
    assert "not a determination of legal culpability" in assessment.disclaimer


def test_21_version_tracking_immutability():
    """Verifies that all assessments include explicit semantic version strings."""
    service = ThreatFusionService()
    assessment = service.assess_target("E-VER", [])
    assert assessment.fusion_version == FUSION_VERSION
    assert assessment.rule_set_version == RULE_SET_VERSION
    assert assessment.schema_version == ASSESSMENT_SCHEMA_VERSION


# ============================================================================
# 8. Input Safety, Error Defense & Pathological Payloads
# ============================================================================

def test_22_oversized_payload_defense():
    """Verifies that requests exceeding maximum signal limits are rejected with HTTP 413."""
    service = ThreatFusionService()
    excessive_signals = [
        ThreatSignal(source=SignalSource.MODEL_A_E, entity_id="E-OVER", score=0.50)
        for _ in range(5_001)
    ]
    with pytest.raises(Exception) as exc_info:
        service.assess_target("E-OVER", excessive_signals)
    assert "413" in str(exc_info.value) or "exceeding maximum limit" in str(exc_info.value)


def test_23_malformed_input_resilience():
    """Verifies that empty signal sets or signals with missing fields fail gracefully."""
    service = ThreatFusionService()
    assessment = service.assess_target("E-EMPTY", [])
    assert assessment.risk_score == 0.0
    assert assessment.confidence_score == 0.0
    assert assessment.severity == "LOW"


# ============================================================================
# 9. API Endpoints Contract Verification
# ============================================================================

def test_24_api_threat_fusion_health_endpoint():
    """Verifies GET /api/threat-fusion/health contract."""
    client = TestClient(app)
    response = client.get("/api/threat-fusion/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert data["fusion_version"] == FUSION_VERSION
    assert data["rule_set_version"] == RULE_SET_VERSION
    assert data["registered_rules_count"] >= 5


def test_25_api_threat_fusion_analyze_endpoint():
    """Verifies POST /api/threat-fusion/analyze endpoint execution."""
    client = TestClient(app)
    payload = {
        "target_id": "ENT-API-TEST",
        "target_type": "entity",
        "signals": [
            {
                "source": "model_a_e",
                "signal_type": "intrusion",
                "score": 0.88,
                "confidence": 0.95,
                "explanation": "Session intrusion detected",
            },
            {
                "source": "dt_gnn",
                "signal_type": "node_threat_risk",
                "score": 0.82,
                "confidence": 0.90,
                "explanation": "Elevated dynamic GNN cluster",
            },
        ],
        "context": {"degree_delta": 7, "time_delta_hours": 2.0},
    }
    response = client.post("/api/threat-fusion/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["target_id"] == "ENT-API-TEST"
    assert data["risk_score"] >= 0.80
    assert data["severity"] in ["HIGH", "CRITICAL"]
    assert data["triggered_rules_count"] >= 1
    assert "explanation" in data
    assert "disclaimer" in data


def test_26_api_threat_fusion_entity_endpoint():
    """Verifies POST /api/threat-fusion/entity/{entity_id} endpoint."""
    client = TestClient(app)
    response = client.post("/api/threat-fusion/entity/ENT-API-999")
    assert response.status_code == 200
    data = response.json()
    assert data["target_id"] == "ENT-API-999"
    assert "risk_score" in data
    assert "confidence_score" in data


def test_27_protected_models_and_gnn_isolation():
    """Verifies that Models A-E and DT-GNN remain unmodified and operational alongside Threat Fusion."""
    from ml.dynamic_gnn.service import dt_gnn_service
    from ml.registry.model_registry import ModelRegistry

    # Models A-E registry check
    registry = ModelRegistry()
    for m in ["intrusion", "network-intrusion", "phishing-url", "webpage-phishing", "phishing-email"]:
        entries = registry.get(m)
        assert len(entries) > 0
        assert Path(entries[0]["artifact_location"]).exists()

    # DT-GNN service health check
    assert dt_gnn_service.config.num_spatial_layers >= 1
