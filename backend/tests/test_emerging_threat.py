"""Comprehensive test suite for Phase 13 Emerging Threat & Early-Warning Intelligence Engine.

Covers all 36 specified requirements:
1. snapshot validation
2. temporal ordering
3. duplicate timestamp handling
4. missing timestamp handling
5. node growth
6. edge growth
7. node churn
8. edge churn
9. degree change
10. centrality change
11. bridge emergence
12. community evolution
13. temporal burst
14. risk escalation
15. risk spike
16. stable trajectory
17. DT-GNN consumption
18. Threat Fusion consumption
19. missing DT-GNN data
20. missing fusion data
21. multi-signal warning
22. contradiction handling
23. confidence separation
24. severity mapping
25. evidence generation
26. provenance
27. deterministic fingerprint
28. event deduplication
29. malformed input
30. oversized input
31. API health
32. API analyze
33. API event retrieval
34. disclaimer
35. version tracking
36. protected subsystem isolation
"""
import copy
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app
from ml.emerging_threat import (
    DETECTOR_VERSION,
    EVENT_SCHEMA_VERSION,
    SNAPSHOT_SCHEMA_VERSION,
    CentralityEvolutionDetector,
    CommunityEvolutionDetector,
    EarlyWarningScorer,
    EmergingSubgraphDetector,
    EmergingThreatConfig,
    EmergingThreatEvent,
    EmergingThreatService,
    EntitySnapshot,
    EventSeverity,
    GraphSnapshot,
    RelationshipSnapshot,
    RiskTrajectoryAnalyzer,
    TemporalBurstDetector,
    TemporalSnapshotSequence,
    TopologyEvolutionDetector,
    TrajectoryType,
    compute_event_fingerprint,
    emerging_threat_service,
    map_warning_severity,
)
from ml.registry.model_registry import ModelRegistry


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_snapshots():
    """Builds a verified chronological sequence of 3 graph snapshots."""
    # Snapshot 0: Baseline 3 nodes, 2 edges
    s0 = GraphSnapshot(
        snapshot_id="SNP-0",
        timestamp=1000.0,
        nodes={
            "N1": EntitySnapshot(id="N1", risk_score=0.20, timestamp=1000.0),
            "N2": EntitySnapshot(id="N2", risk_score=0.25, timestamp=1000.0),
            "N3": EntitySnapshot(id="N3", risk_score=0.15, timestamp=1000.0),
        },
        edges=[
            RelationshipSnapshot(source_id="N1", target_id="N2", timestamp=1000.0),
            RelationshipSnapshot(source_id="N2", target_id="N3", timestamp=1000.0),
        ],
        fusion_risk_score=0.20,
    )

    # Snapshot 1: Growth to 5 nodes, 4 edges, slight risk increase
    s1 = GraphSnapshot(
        snapshot_id="SNP-1",
        timestamp=2000.0,
        nodes={
            "N1": EntitySnapshot(id="N1", risk_score=0.35, timestamp=2000.0),
            "N2": EntitySnapshot(id="N2", risk_score=0.45, timestamp=2000.0),
            "N3": EntitySnapshot(id="N3", risk_score=0.30, timestamp=2000.0),
            "N4": EntitySnapshot(id="N4", risk_score=0.50, timestamp=2000.0),
            "N5": EntitySnapshot(id="N5", risk_score=0.55, timestamp=2000.0),
        },
        edges=[
            RelationshipSnapshot(source_id="N1", target_id="N2", timestamp=1500.0),
            RelationshipSnapshot(source_id="N2", target_id="N3", timestamp=1600.0),
            RelationshipSnapshot(source_id="N3", target_id="N4", timestamp=1700.0),
            RelationshipSnapshot(source_id="N4", target_id="N5", timestamp=1800.0),
        ],
        fusion_risk_score=0.40,
    )

    # Snapshot 2: Escalation to 8 nodes, 9 edges, high risk
    s2 = GraphSnapshot(
        snapshot_id="SNP-2",
        timestamp=3000.0,
        nodes={
            "N1": EntitySnapshot(id="N1", risk_score=0.60, timestamp=3000.0),
            "N2": EntitySnapshot(id="N2", risk_score=0.75, timestamp=3000.0),
            "N3": EntitySnapshot(id="N3", risk_score=0.70, timestamp=3000.0),
            "N4": EntitySnapshot(id="N4", risk_score=0.85, timestamp=3000.0),
            "N5": EntitySnapshot(id="N5", risk_score=0.80, timestamp=3000.0),
            "N6": EntitySnapshot(id="N6", risk_score=0.65, timestamp=3000.0),
            "N7": EntitySnapshot(id="N7", risk_score=0.70, timestamp=3000.0),
            "N8": EntitySnapshot(id="N8", risk_score=0.75, timestamp=3000.0),
        },
        edges=[
            RelationshipSnapshot(source_id="N1", target_id="N2", timestamp=2100.0),
            RelationshipSnapshot(source_id="N2", target_id="N3", timestamp=2200.0),
            RelationshipSnapshot(source_id="N3", target_id="N4", timestamp=2300.0),
            RelationshipSnapshot(source_id="N4", target_id="N5", timestamp=2400.0),
            RelationshipSnapshot(source_id="N2", target_id="N6", timestamp=2500.0),
            RelationshipSnapshot(source_id="N6", target_id="N7", timestamp=2600.0),
            RelationshipSnapshot(source_id="N7", target_id="N8", timestamp=2700.0),
            RelationshipSnapshot(source_id="N3", target_id="N7", timestamp=2800.0),
            RelationshipSnapshot(source_id="N5", target_id="N8", timestamp=2900.0),
        ],
        dt_gnn_anomaly_score=0.82,
        fusion_risk_score=0.72,
    )

    return [s0, s1, s2]


# 1. Snapshot Validation
def test_01_snapshot_validation():
    snap = GraphSnapshot(
        snapshot_id="SNP-VAL",
        timestamp=100.0,
        nodes={"A": EntitySnapshot(id="A", risk_score=0.5)},
        edges=[RelationshipSnapshot(source_id="A", target_id="B")],
    )
    assert snap.node_count == 1
    assert snap.edge_count == 1
    assert "A" in snap.node_ids()


# 2. Temporal Ordering
def test_02_temporal_ordering(sample_snapshots):
    # Pass snapshots out of order
    unordered = [sample_snapshots[2], sample_snapshots[0], sample_snapshots[1]]
    seq = TemporalSnapshotSequence(unordered)
    assert seq.count == 3
    assert seq.snapshots[0].timestamp < seq.snapshots[1].timestamp < seq.snapshots[2].timestamp


# 3. Duplicate Timestamp Handling
def test_03_duplicate_timestamp_handling():
    s1 = GraphSnapshot(snapshot_id="S1", timestamp=100.0)
    s2 = GraphSnapshot(snapshot_id="S2", timestamp=100.0)
    seq = TemporalSnapshotSequence([s1, s2])
    assert seq.count == 2
    # Ensure second timestamp is micro-offset to maintain strict inequality
    assert seq.snapshots[0].timestamp < seq.snapshots[1].timestamp


# 4. Missing Timestamp Handling
def test_04_missing_timestamp_handling():
    s = GraphSnapshot(snapshot_id="S_NONE", timestamp=None)
    seq = TemporalSnapshotSequence([s])
    assert seq.snapshots[0].timestamp == 0.0


# 5. Node Growth
def test_05_node_growth(sample_snapshots):
    detector = TopologyEvolutionDetector()
    metrics = detector.compare_snapshots(sample_snapshots[0], sample_snapshots[1], delta_seconds=1000.0)
    # 3 nodes -> 5 nodes: growth = 2/3 = 0.6667
    assert metrics.curr_nodes == 5
    assert metrics.prior_nodes == 3
    assert metrics.node_growth_rate > 0.60


# 6. Edge Growth
def test_06_edge_growth(sample_snapshots):
    detector = TopologyEvolutionDetector()
    metrics = detector.compare_snapshots(sample_snapshots[0], sample_snapshots[1], delta_seconds=1000.0)
    # 2 edges -> 4 edges: growth = 2/2 = 1.0
    assert metrics.edge_growth_rate == 1.0


# 7. Node Churn
def test_07_node_churn():
    s_p = GraphSnapshot(snapshot_id="SP", timestamp=10.0, nodes={"A": EntitySnapshot(id="A"), "B": EntitySnapshot(id="B")})
    s_c = GraphSnapshot(snapshot_id="SC", timestamp=20.0, nodes={"B": EntitySnapshot(id="B"), "C": EntitySnapshot(id="C")})
    detector = TopologyEvolutionDetector()
    metrics = detector.compare_snapshots(s_p, s_c, 10.0)
    # Total unique: A, B, C = 3. Added: C, Removed: A. Churn = 2/3 = 0.6667
    assert metrics.node_churn == pytest.approx(0.6667, abs=0.01)


# 8. Edge Churn
def test_08_edge_churn():
    s_p = GraphSnapshot(snapshot_id="SP", timestamp=10.0, edges=[RelationshipSnapshot(source_id="A", target_id="B")])
    s_c = GraphSnapshot(snapshot_id="SC", timestamp=20.0, edges=[RelationshipSnapshot(source_id="B", target_id="C")])
    detector = TopologyEvolutionDetector()
    metrics = detector.compare_snapshots(s_p, s_c, 10.0)
    # Total unique: (A,B), (B,C) = 2. Added: 1, Removed: 1. Churn = 1.0
    assert metrics.edge_churn == 1.0


# 9. Degree Change
def test_09_degree_change(sample_snapshots):
    cent_det = CentralityEvolutionDetector()
    shifts = cent_det.compare_centralities(sample_snapshots[1], sample_snapshots[2])
    assert "N2" in shifts
    # N2 degree changed as more connections formed (raw degree 2 -> 3)
    assert shifts["N2"].curr_raw_degree >= shifts["N2"].prior_raw_degree
    assert shifts["N2"].raw_degree_shift >= 1


# 10. Centrality Change
def test_10_centrality_change(sample_snapshots):
    cent_det = CentralityEvolutionDetector()
    shifts = cent_det.compare_centralities(sample_snapshots[1], sample_snapshots[2])
    # Betweenness and pagerank calculated
    assert shifts["N2"].curr_betweenness >= 0.0
    assert shifts["N2"].curr_pagerank > 0.0


# 11. Bridge Emergence
def test_11_bridge_emergence():
    # Construct a bottleneck bridge scenario: Cluster 1 (A, B) -- BRIDGE (X) -- Cluster 2 (C, D)
    s_prior = GraphSnapshot(
        snapshot_id="S0",
        timestamp=10.0,
        nodes={n: EntitySnapshot(id=n) for n in ["A", "B", "C", "D", "X"]},
        edges=[
            RelationshipSnapshot(source_id="A", target_id="B"),
            RelationshipSnapshot(source_id="C", target_id="D"),
            RelationshipSnapshot(source_id="A", target_id="X"),
        ],
    )
    s_curr = GraphSnapshot(
        snapshot_id="S1",
        timestamp=20.0,
        nodes={n: EntitySnapshot(id=n) for n in ["A", "B", "C", "D", "X"]},
        edges=[
            RelationshipSnapshot(source_id="A", target_id="B"),
            RelationshipSnapshot(source_id="C", target_id="D"),
            RelationshipSnapshot(source_id="A", target_id="X"),
            RelationshipSnapshot(source_id="X", target_id="C"), # Bridge completed!
        ],
    )
    detector = CentralityEvolutionDetector()
    shifts = detector.compare_centralities(s_prior, s_curr)
    assert shifts["X"].betweenness_shift > 0.20
    assert shifts["X"].is_emerging_bridge is True


# 12. Community Evolution
def test_12_community_evolution():
    import itertools
    # Two distinct clusters in prior snapshot merge into a single complete clique in current
    nodes = {n: EntitySnapshot(id=n) for n in ["A", "B", "C", "D", "E", "F"]}
    edges_prior = [
        RelationshipSnapshot(source_id="A", target_id="B"),
        RelationshipSnapshot(source_id="B", target_id="C"),
        RelationshipSnapshot(source_id="A", target_id="C"),
        RelationshipSnapshot(source_id="D", target_id="E"),
        RelationshipSnapshot(source_id="E", target_id="F"),
        RelationshipSnapshot(source_id="D", target_id="F"),
    ]
    edges_curr = [RelationshipSnapshot(source_id=u, target_id=v) for u, v in itertools.combinations(nodes.keys(), 2)]

    s_prior = GraphSnapshot(snapshot_id="SP", timestamp=10.0, nodes=nodes, edges=edges_prior)
    s_curr = GraphSnapshot(snapshot_id="SC", timestamp=20.0, nodes=nodes, edges=edges_curr)

    det = CommunityEvolutionDetector()
    metrics = det.compare_communities(s_prior, s_curr)
    assert metrics.communities_merged >= 1 or metrics.community_evolution_score > 0.0


# 13. Temporal Burst
def test_13_temporal_burst():
    # 10 interactions within 100 seconds
    edges = [
        RelationshipSnapshot(source_id=f"S{i}", target_id="T1", timestamp=1000.0 + i * 5)
        for i in range(10)
    ]
    s = GraphSnapshot(snapshot_id="SB", timestamp=1050.0, edges=edges)
    burst_det = TemporalBurstDetector()
    res = burst_det.analyze_bursts("NET-BURST", [s])
    assert res.burst_detected is True
    assert res.burst_score > 0.50
    assert res.max_event_count_in_window == 10


# 14. Risk Escalation Trajectory
def test_14_risk_escalation():
    analyzer = RiskTrajectoryAnalyzer()
    obs = [(100.0, 0.20), (200.0, 0.40), (300.0, 0.65), (400.0, 0.85)]
    res = analyzer.analyze_trajectory("E1", obs)
    assert res.trajectory_type == TrajectoryType.RAPID_ESCALATION
    assert res.velocity >= 0.15
    assert res.trajectory_score >= 0.70


# 15. Sudden Risk Spike Trajectory
def test_15_risk_spike():
    analyzer = RiskTrajectoryAnalyzer()
    obs = [(100.0, 0.20), (200.0, 0.22), (300.0, 0.75)] # +0.53 jump
    res = analyzer.analyze_trajectory("E2", obs)
    assert res.trajectory_type == TrajectoryType.SUDDEN_SPIKE
    assert res.trajectory_score >= 0.75


# 16. Stable Trajectory
def test_16_stable_trajectory():
    analyzer = RiskTrajectoryAnalyzer()
    obs = [(100.0, 0.20), (200.0, 0.21), (300.0, 0.22), (400.0, 0.21)]
    res = analyzer.analyze_trajectory("E3", obs)
    assert res.trajectory_type == TrajectoryType.STABLE
    assert res.trajectory_score < 0.30


# 17. DT-GNN Consumption
def test_17_dt_gnn_consumption(sample_snapshots):
    seq = TemporalSnapshotSequence(sample_snapshots)
    event = emerging_threat_service.analyze_network_sequence(
        "NET-GNN", seq, external_dt_gnn_score=0.88
    )
    assert event.dt_gnn_signals.get("score") == 0.88
    assert event.early_warning_score > 0.50


# 18. Threat Fusion Consumption
def test_18_threat_fusion_consumption(sample_snapshots):
    seq = TemporalSnapshotSequence(sample_snapshots)
    event = emerging_threat_service.analyze_network_sequence(
        "NET-FUSION", seq, external_fusion_score=0.92
    )
    assert event.fusion_signals.get("score") == 0.92


# 19. Missing DT-GNN Data Handling
def test_19_missing_dt_gnn_data(sample_snapshots):
    seq = TemporalSnapshotSequence(sample_snapshots)
    event = emerging_threat_service.analyze_network_sequence(
        "NET-NO-GNN", seq, external_dt_gnn_score=None
    )
    assert event is not None
    assert 0.0 <= event.early_warning_score <= 1.0


# 20. Missing Threat Fusion Data Handling
def test_20_missing_fusion_data():
    s = GraphSnapshot(snapshot_id="S0", timestamp=10.0, nodes={"A": EntitySnapshot(id="A")})
    seq = TemporalSnapshotSequence([s])
    event = emerging_threat_service.analyze_network_sequence(
        "NET-NO-FUSION", seq, external_fusion_score=None
    )
    assert event is not None
    assert event.early_warning_score >= 0.0


# 21. Multi-Signal Early Warning Convergence
def test_21_multi_signal_warning(sample_snapshots):
    seq = TemporalSnapshotSequence(sample_snapshots)
    event = emerging_threat_service.analyze_network_sequence(
        "NET-CONVERGE", seq, external_dt_gnn_score=0.85, external_fusion_score=0.80
    )
    assert event.early_warning_score >= 0.60
    assert event.severity in ["HIGH", "CRITICAL"]


# 22. Contradiction Handling
def test_22_contradiction_handling():
    scorer = EarlyWarningScorer()
    # High trajectory (0.90) but zero topology velocity and zero bursts
    res = scorer.calculate_score(
        trajectory_score=0.90,
        topology_velocity_score=0.0,
        centrality_velocity_score=0.0,
        temporal_burst_score=0.0,
        community_evolution_score=0.0,
        snapshot_count=5,
        timespan_seconds=3600.0,
    )
    # The warning score should be attenuated by the calm structural indicators
    assert res["early_warning_score"] < 0.40


# 23. Confidence Separation
def test_23_confidence_separation():
    scorer = EarlyWarningScorer()
    # High warning score from sudden burst, but only 1 snapshot and 10 seconds span
    res = scorer.calculate_score(
        trajectory_score=0.95,
        topology_velocity_score=0.90,
        centrality_velocity_score=0.85,
        temporal_burst_score=0.85,
        community_evolution_score=0.80,
        snapshot_count=1,
        timespan_seconds=10.0,
    )
    assert res["early_warning_score"] >= 0.70
    assert res["confidence_score"] <= 0.60
    # Invariant: early_warning_score != confidence_score
    assert abs(res["early_warning_score"] - res["confidence_score"]) > 0.10


# 24. Severity Mapping Consistency
def test_24_severity_mapping():
    cfg = EmergingThreatConfig()
    assert map_warning_severity(0.85, cfg) == EventSeverity.CRITICAL
    assert map_warning_severity(0.65, cfg) == EventSeverity.HIGH
    assert map_warning_severity(0.40, cfg) == EventSeverity.MEDIUM
    assert map_warning_severity(0.10, cfg) == EventSeverity.LOW


# 25. Evidence Generation & Traceability
def test_25_evidence_generation(sample_snapshots):
    seq = TemporalSnapshotSequence(sample_snapshots)
    event = emerging_threat_service.analyze_network_sequence("NET-EVID", seq)
    exp = event.explanation
    assert "supporting_factors" in exp
    assert "summary_narrative" in exp
    assert len(exp["summary_narrative"]) > 0


# 26. Provenance Preservation
def test_26_provenance_preservation(sample_snapshots):
    seq = TemporalSnapshotSequence(sample_snapshots)
    event = emerging_threat_service.analyze_network_sequence("NET-PROV", seq)
    assert event.observation_window["start"] == 1000.0
    assert event.observation_window["end"] == 3000.0
    assert event.detector_version == DETECTOR_VERSION


# 27. Deterministic Fingerprint Calculation
def test_27_deterministic_fingerprint():
    fp1 = compute_event_fingerprint("NET-101", ["N1", "N2", "N3"], 1000.0, 2000.0, "ESCALATION")
    fp2 = compute_event_fingerprint("NET-101", ["N3", "N1", "N2"], 1000.0, 2000.0, "ESCALATION")
    # Entity order must not change fingerprint
    assert fp1 == fp2
    assert len(fp1) == 64 # SHA-256 hex


# 28. Event Deduplication Guarantee
def test_28_event_deduplication(sample_snapshots):
    seq = TemporalSnapshotSequence(sample_snapshots)
    event1 = emerging_threat_service.analyze_network_sequence("NET-DEDUP", seq)
    event2 = emerging_threat_service.analyze_network_sequence("NET-DEDUP", seq)
    # Deduplication ensures the same event instance or ID is returned
    assert event1.event_id == event2.event_id
    assert event1.event_fingerprint == event2.event_fingerprint


# 29. Malformed Input Resilience(client):
def test_29_malformed_input_resilience(client):
    res = client.post("/api/emerging-threat/analyze", json={"bad_field": 123})
    assert res.status_code == 422


# 30. Oversized Payload Defense
def test_30_oversized_payload_defense():
    snapshots = [GraphSnapshot(snapshot_id=f"S{i}", timestamp=float(i)) for i in range(105)]
    seq = TemporalSnapshotSequence(snapshots)
    with pytest.raises(Exception) as exc_info:
        emerging_threat_service.analyze_network_sequence("NET-OVERSIZED", seq)
    assert "413" in str(exc_info.value) or "exceeding limit" in str(exc_info.value)


# 31. API Health Endpoint Contract
def test_31_api_health_endpoint(client):
    res = client.get("/api/emerging-threat/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"
    assert data["detector_version"] == DETECTOR_VERSION
    assert data["event_schema_version"] == EVENT_SCHEMA_VERSION


# 32. API Analyze Endpoint Execution
def test_32_api_analyze_endpoint(client):
    payload = {
        "network_id": "NET-API-TEST",
        "snapshots": [
            {
                "timestamp": 1000.0,
                "nodes": [{"id": "E1", "risk_score": 0.2}],
                "edges": [],
            },
            {
                "timestamp": 2000.0,
                "nodes": [
                    {"id": "E1", "risk_score": 0.6},
                    {"id": "E2", "risk_score": 0.7},
                ],
                "edges": [{"source_id": "E1", "target_id": "E2"}],
            },
        ],
    }
    res = client.post("/api/emerging-threat/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["network_id"] == "NET-API-TEST"
    assert 0.0 <= data["early_warning_score"] <= 1.0
    assert data["event_fingerprint"] is not None


# 33. API Event Retrieval Endpoint
def test_33_api_event_retrieval(client):
    # First query events list
    res = client.get("/api/emerging-threat/events")
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)
    if events:
        eid = events[0]["event_id"]
        res_single = client.get(f"/api/emerging-threat/events/{eid}")
        assert res_single.status_code == 200
        assert res_single.json()["event_id"] == eid


# 34. Mandatory Governance Disclaimer
def test_34_mandatory_governance_disclaimer(sample_snapshots):
    seq = TemporalSnapshotSequence(sample_snapshots)
    event = emerging_threat_service.analyze_network_sequence("NET-DISC", seq)
    assert "not a determination of legal culpability" in event.disclaimer
    assert "Requires human verification" in event.disclaimer


# 35. Version Tracking Immutability
def test_35_version_tracking():
    assert DETECTOR_VERSION == "1.0.0"
    assert EVENT_SCHEMA_VERSION == "1.0.0"
    assert SNAPSHOT_SCHEMA_VERSION == "1.0.0"


# 36. Protected Subsystem Isolation
def test_36_protected_subsystem_isolation():
    registry = ModelRegistry()
    protected_models = ["intrusion", "network-intrusion", "phishing-url", "webpage-phishing", "phishing-email"]
    for m in protected_models:
        meta = registry.get(m)
        assert meta is not None, f"Protected Model {m} registry entry missing!"
        assert len(meta) > 0
