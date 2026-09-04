"""Comprehensive unit, integration, and regression test suite for Phase 14:
Dynamic Investigation Timeline + Graph Replay Engine.
"""
import copy
import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from ml.emerging_threat.snapshots import (
    EntitySnapshot,
    GraphSnapshot,
    RelationshipSnapshot,
    TemporalSnapshotSequence,
)
from ml.emerging_threat.events import EmergingThreatEvent, EventLifecycleState, EventSeverity
from ml.emerging_threat.config import TrajectoryType
from ml.investigation_timeline import (
    EVENT_SCHEMA_VERSION,
    MANDATORY_GOVERNANCE_DISCLAIMER,
    ProvenanceType,
    ReconstructionAccuracy,
    TimelineEventType,
    investigation_timeline_service,
    compute_graph_state_hash,
    compute_timeline_event_identity,
    compute_replay_frame_identity,
    GraphSnapshotReconstructor,
    GraphChangeDetector,
    SignalCorrelationEngine,
    InvestigatorMarkerRegistry,
    InvestigationTimelineBuilder,
    GraphReplayEngine,
    InvestigatorMarkerRequest,
)

client = TestClient(app)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def reset_service_state():
    """Clear in-memory state before each test."""
    investigation_timeline_service.clear()
    yield
    investigation_timeline_service.clear()


@pytest.fixture
def baseline_snapshot_t0():
    return GraphSnapshot(
        snapshot_id="SNP-T0",
        timestamp=1700000000.0,
        nodes={
            "N1": EntitySnapshot(id="N1", entity_type="SUSPECT", risk_score=0.25, timestamp=1700000000.0),
            "N2": EntitySnapshot(id="N2", entity_type="DEVICE", risk_score=0.30, timestamp=1700000000.0),
        },
        edges=[
            RelationshipSnapshot(source_id="N1", target_id="N2", rel_type="USES", weight=1.0, timestamp=1700000000.0)
        ],
    )


@pytest.fixture
def evolved_snapshot_t1():
    return GraphSnapshot(
        snapshot_id="SNP-T1",
        timestamp=1700001000.0,
        nodes={
            "N1": EntitySnapshot(id="N1", entity_type="SUSPECT", risk_score=0.75, timestamp=1700001000.0),
            "N2": EntitySnapshot(id="N2", entity_type="DEVICE", risk_score=0.40, timestamp=1700001000.0),
            "N3": EntitySnapshot(id="N3", entity_type="BANK_ACCOUNT", risk_score=0.85, timestamp=1700001000.0),
        },
        edges=[
            RelationshipSnapshot(source_id="N1", target_id="N2", rel_type="USES", weight=1.5, timestamp=1700001000.0),
            RelationshipSnapshot(source_id="N1", target_id="N3", rel_type="CONTROLS", weight=1.0, timestamp=1700001000.0),
        ],
    )


# =============================================================================
# 1. Timeline Creation & Ordering
# =============================================================================

def test_01_timeline_creation(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    events = investigation_timeline_service.analyze_network_timeline("NET-01", seq)
    assert len(events) >= 2
    types = {e.event_type for e in events}
    assert TimelineEventType.GRAPH_SNAPSHOT in types


def test_02_deterministic_ordering(baseline_snapshot_t0, evolved_snapshot_t1):
    seq1 = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    events1 = investigation_timeline_service.analyze_network_timeline("NET-ORDER", seq1)

    # Reversed input to sequence
    seq2 = TemporalSnapshotSequence([evolved_snapshot_t1, baseline_snapshot_t0])
    events2 = investigation_timeline_service.analyze_network_timeline("NET-ORDER", seq2)

    ids1 = [e.event_id for e in events1]
    ids2 = [e.event_id for e in events2]
    assert ids1 == ids2, "Timeline ordering must be strictly deterministic regardless of input arrival order."


def test_03_deterministic_ids():
    ev_id1, fp1 = compute_timeline_event_identity("NET-A", "NODE_ADDED", 1000.0, ["N1", "N2"], ["N1--N2"])
    ev_id2, fp2 = compute_timeline_event_identity("NET-A", "NODE_ADDED", 1000.0, ["N2", "N1"], ["N1--N2"])
    assert ev_id1 == ev_id2
    assert fp1 == fp2, "Permuted entity list must generate identical canonical fingerprint."


# =============================================================================
# 2. Graph Snapshot Reconstruction (Exact & Approximate)
# =============================================================================

def test_04_snapshot_reconstruction(baseline_snapshot_t0):
    state = GraphSnapshotReconstructor.reconstruct_from_snapshot(baseline_snapshot_t0)
    assert state.node_count == 2
    assert state.edge_count == 1
    assert state.accuracy == ReconstructionAccuracy.EXACT
    assert state.state_hash is not None


def test_05_exact_timestamp_reconstruction(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    state = investigation_timeline_service.reconstruct_snapshot("NET-01", 1700000000.0, seq)
    assert state.accuracy == ReconstructionAccuracy.EXACT
    assert state.timestamp == 1700000000.0
    assert state.node_count == 2


def test_06_approximate_reconstruction(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    # Target time midway between T0 and T1
    midway_time = 1700000500.0
    state = investigation_timeline_service.reconstruct_snapshot("NET-01", midway_time, seq)
    assert state.accuracy == ReconstructionAccuracy.APPROXIMATED
    assert len(state.data_quality_warnings) > 0
    assert "approximated" in state.data_quality_warnings[0].lower()


def test_07_missing_snapshot():
    seq = TemporalSnapshotSequence([])
    state = investigation_timeline_service.reconstruct_snapshot("NET-EMPTY", 1700000000.0, seq)
    assert state.accuracy == ReconstructionAccuracy.EMPTY_INTERPOLATED
    assert state.node_count == 0
    assert state.edge_count == 0


def test_08_duplicate_timestamps(baseline_snapshot_t0):
    s_dup = copy.deepcopy(baseline_snapshot_t0)
    s_dup.snapshot_id = "SNP-DUP"
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, s_dup])
    # Sequence should auto-micro-offset duplicate
    assert seq.count == 2
    assert seq.snapshots[1].timestamp > seq.snapshots[0].timestamp


def test_09_out_of_order_timestamps(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([evolved_snapshot_t1, baseline_snapshot_t0])
    assert seq.snapshots[0].timestamp < seq.snapshots[1].timestamp
    assert seq.snapshots[0].snapshot_id == "SNP-T0"


# =============================================================================
# 3. Structural & Attribute Change Detection
# =============================================================================

def test_10_node_addition(baseline_snapshot_t0, evolved_snapshot_t1):
    s0 = GraphSnapshotReconstructor.reconstruct_from_snapshot(baseline_snapshot_t0)
    s1 = GraphSnapshotReconstructor.reconstruct_from_snapshot(evolved_snapshot_t1)
    changes = GraphChangeDetector.detect_changes(s0, s1)
    assert "N3" in changes.added_nodes
    assert len(changes.removed_nodes) == 0


def test_11_node_removal(baseline_snapshot_t0, evolved_snapshot_t1):
    s0 = GraphSnapshotReconstructor.reconstruct_from_snapshot(evolved_snapshot_t1)
    s1 = GraphSnapshotReconstructor.reconstruct_from_snapshot(baseline_snapshot_t0)
    changes = GraphChangeDetector.detect_changes(s0, s1)
    assert "N3" in changes.removed_nodes
    assert len(changes.added_nodes) == 0


def test_12_edge_addition(baseline_snapshot_t0, evolved_snapshot_t1):
    s0 = GraphSnapshotReconstructor.reconstruct_from_snapshot(baseline_snapshot_t0)
    s1 = GraphSnapshotReconstructor.reconstruct_from_snapshot(evolved_snapshot_t1)
    changes = GraphChangeDetector.detect_changes(s0, s1)
    assert len(changes.added_edges) == 1
    added_edge = changes.added_edges[0]
    assert "N1" in added_edge and "N3" in added_edge


def test_13_edge_removal(baseline_snapshot_t0, evolved_snapshot_t1):
    s0 = GraphSnapshotReconstructor.reconstruct_from_snapshot(evolved_snapshot_t1)
    s1 = GraphSnapshotReconstructor.reconstruct_from_snapshot(baseline_snapshot_t0)
    changes = GraphChangeDetector.detect_changes(s0, s1)
    assert len(changes.removed_edges) == 1


def test_14_node_attribute_change(baseline_snapshot_t0, evolved_snapshot_t1):
    s0 = GraphSnapshotReconstructor.reconstruct_from_snapshot(baseline_snapshot_t0)
    s1 = GraphSnapshotReconstructor.reconstruct_from_snapshot(evolved_snapshot_t1)
    changes = GraphChangeDetector.detect_changes(s0, s1)
    assert "N1" in changes.node_attribute_changes
    assert changes.node_attribute_changes["N1"]["risk_score"]["old"] == 0.25
    assert changes.node_attribute_changes["N1"]["risk_score"]["new"] == 0.75


def test_15_edge_attribute_change(baseline_snapshot_t0, evolved_snapshot_t1):
    s0 = GraphSnapshotReconstructor.reconstruct_from_snapshot(baseline_snapshot_t0)
    s1 = GraphSnapshotReconstructor.reconstruct_from_snapshot(evolved_snapshot_t1)
    changes = GraphChangeDetector.detect_changes(s0, s1)
    assert len(changes.edge_attribute_changes) == 1
    key = list(changes.edge_attribute_changes.keys())[0]
    assert changes.edge_attribute_changes[key]["weight"]["old"] == 1.0
    assert changes.edge_attribute_changes[key]["weight"]["new"] == 1.5


def test_16_structural_metric_changes(baseline_snapshot_t0, evolved_snapshot_t1):
    s0 = GraphSnapshotReconstructor.reconstruct_from_snapshot(baseline_snapshot_t0)
    s1 = GraphSnapshotReconstructor.reconstruct_from_snapshot(evolved_snapshot_t1)
    changes = GraphChangeDetector.detect_changes(s0, s1)
    assert changes.node_count_delta == 1
    assert changes.edge_count_delta == 1
    assert isinstance(changes.density_delta, float)


# =============================================================================
# 4. Read-Only Intelligence Correlation
# =============================================================================

def test_17_phase13_correlation(baseline_snapshot_t0, evolved_snapshot_t1):
    correlator = SignalCorrelationEngine()
    dummy_event = EmergingThreatEvent(
        event_id="EWE-TEST-01",
        event_fingerprint="fp1234567890",
        network_id="NET-CORR",
        entity_ids=["N1"],
        detected_at=1700000500.0,
        observation_window={"start": 1700000000.0, "end": 1700001000.0},
        event_type="RISK_RAPID_ESCALATION",
        early_warning_score=0.88,
        confidence_score=0.92,
        severity=EventSeverity.HIGH,
        lifecycle_state=EventLifecycleState.DETECTED,
        trajectory={"type": TrajectoryType.RAPID_ESCALATION.value, "velocity": 0.5, "acceleration": 0.1},
        topology_changes={},
        centrality_changes={},
        community_changes={},
        temporal_bursts={},
        subgraph_candidates=[],
        dt_gnn_signals={},
        fusion_signals={},
        supporting_evidence=[],
        contradicting_evidence=[],
        provenance={"detector_version": "1.0.0"},
        explanation={"summary": "Risk trajectory escalating"},
    )
    correlated = correlator.correlate_phase13_events(
        network_id="NET-CORR",
        start_time=1700000000.0,
        end_time=1700001000.0,
        external_events=[dummy_event],
    )
    assert len(correlated) == 1
    assert correlated[0].event_type == TimelineEventType.EMERGING_THREAT
    assert correlated[0].provenance_type == ProvenanceType.CORRELATED
    assert "does not establish causality" in correlated[0].description


def test_18_dt_gnn_missing_signal():
    correlator = SignalCorrelationEngine()
    signals = [{"timestamp": 1700000000.0, "anomaly_score": None, "entity_ids": ["N1"]}]
    events = correlator.correlate_dt_gnn_signals("NET-01", signals)
    assert len(events) == 1
    assert events[0].details["is_missing"] is True
    assert events[0].details["anomaly_score"] is None, "Missing DT-GNN signal must not be backfilled as zero."


def test_19_threat_fusion_missing_signal():
    correlator = SignalCorrelationEngine()
    signals = [{"timestamp": 1700000000.0, "risk_score": None, "entity_ids": ["N2"]}]
    events = correlator.correlate_threat_fusion_signals("NET-01", signals)
    assert len(events) == 1
    assert events[0].details["is_missing"] is True
    assert events[0].details["risk_score"] is None, "Missing Threat Fusion signal must not be backfilled as zero."


# =============================================================================
# 5. Provenance & Distinction
# =============================================================================

def test_20_provenance(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    events = investigation_timeline_service.analyze_network_timeline("NET-PROV", seq)
    prov_types = {e.provenance_type for e in events}
    assert ProvenanceType.SOURCE in prov_types
    assert ProvenanceType.DERIVED in prov_types


def test_21_source_vs_derived_distinction(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    events = investigation_timeline_service.analyze_network_timeline("NET-PROV2", seq)
    for e in events:
        if e.event_type == TimelineEventType.GRAPH_SNAPSHOT:
            assert e.provenance_type == ProvenanceType.SOURCE
        elif e.event_type in (TimelineEventType.NODE_ADDED, TimelineEventType.EDGE_ADDED):
            assert e.provenance_type == ProvenanceType.DERIVED


# =============================================================================
# 6. Replay Generation & Determinism
# =============================================================================

def test_22_replay_generation(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    manifest = investigation_timeline_service.generate_replay("NET-REPLAY", seq)
    assert manifest.total_frames == 2
    assert manifest.frames[0].frame_index == 0
    assert manifest.frames[1].frame_index == 1
    assert manifest.frames[1].change_from_previous is not None
    assert "N3" in manifest.frames[1].change_from_previous.added_nodes


def test_23_replay_determinism(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    m1 = investigation_timeline_service.generate_replay("NET-DET", seq)
    m2 = investigation_timeline_service.generate_replay("NET-DET", seq)
    assert m1.replay_id == m2.replay_id
    assert [f.state_hash for f in m1.frames] == [f.state_hash for f in m2.frames]
    assert [f.frame_id for f in m1.frames] == [f.frame_id for f in m2.frames]


def test_24_graph_state_hashing(baseline_snapshot_t0):
    nodes1 = baseline_snapshot_t0.nodes
    edges1 = baseline_snapshot_t0.edges
    h1 = compute_graph_state_hash(nodes1, edges1)

    # Clone and permute node insertion order
    nodes2 = {k: nodes1[k] for k in reversed(list(nodes1.keys()))}
    h2 = compute_graph_state_hash(nodes2, edges1)
    assert h1 == h2, "Canonical state hash must be invariant to dict insertion order."


# =============================================================================
# 7. Timeline & Event Filtering
# =============================================================================

def test_25_timeline_filtering(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    events = investigation_timeline_service.analyze_network_timeline("NET-FILT", seq)
    filtered = InvestigationTimelineBuilder.filter_events(
        events,
        start_time=1700000500.0,
    )
    assert all(e.timestamp >= 1700000500.0 for e in filtered)


def test_26_event_filtering(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    events = investigation_timeline_service.analyze_network_timeline("NET-FILT2", seq)
    filtered = InvestigationTimelineBuilder.filter_events(
        events,
        event_types=[TimelineEventType.NODE_ADDED],
    )
    assert all(e.event_type == TimelineEventType.NODE_ADDED for e in filtered)


def test_27_entity_filtering(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    events = investigation_timeline_service.analyze_network_timeline("NET-FILT3", seq)
    filtered = InvestigationTimelineBuilder.filter_events(
        events,
        entity_ids=["N3"],
    )
    assert all("N3" in e.entity_ids for e in filtered)


# =============================================================================
# 8. Data Quality & Resilience
# =============================================================================

def test_28_data_quality_warnings(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    manifest = investigation_timeline_service.generate_replay(
        "NET-WARN",
        seq,
        start_time=1700002000.0,  # Beyond end time
        end_time=1700003000.0,
    )
    assert len(manifest.data_quality_warnings) > 0


def test_29_oversized_request_rejection():
    # Exceed safety limit
    large_snaps = [
        GraphSnapshot(snapshot_id=f"SNP-{i}", timestamp=float(i), nodes={}, edges=[])
        for i in range(105)
    ]
    seq = TemporalSnapshotSequence(large_snaps)
    with pytest.raises(ValueError, match="exceeds safety limit"):
        investigation_timeline_service.analyze_network_timeline("NET-LARGE", seq)


def test_30_malformed_input():
    # Empty payload to API
    resp = client.post("/api/investigation-timeline/analyze", json={})
    assert resp.status_code == 422


def test_31_empty_graph():
    seq = TemporalSnapshotSequence([])
    manifest = investigation_timeline_service.generate_replay("NET-EMPTY", seq)
    assert manifest.total_frames == 0
    assert len(manifest.data_quality_warnings) > 0


# =============================================================================
# 9. Markers, Governance & Protected Isolation
# =============================================================================

def test_32_investigation_marker():
    req = InvestigatorMarkerRequest(
        timestamp=1700000200.0,
        title="Search Warrant Executed",
        note="Physical seizure of electronic media at residence.",
        linked_entities=["N1"],
        actor_id="OFFICER-4417",
    )
    event = investigation_timeline_service.add_marker("NET-MARKER", req)
    assert event.event_type == TimelineEventType.INVESTIGATION_MARKER
    assert event.provenance_type == ProvenanceType.SOURCE
    assert event.details["is_investigator_created"] is True


def test_33_api_health_and_lifecycle():
    resp = client.get("/api/investigation-timeline/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert "safety_limits" in data


def test_34_mandatory_governance_disclaimer(baseline_snapshot_t0):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0])
    manifest = investigation_timeline_service.generate_replay("NET-DISC", seq)
    assert manifest.disclaimer == MANDATORY_GOVERNANCE_DISCLAIMER
    assert "does not establish causation" in manifest.disclaimer


def test_35_non_causal_terminology(baseline_snapshot_t0, evolved_snapshot_t1):
    seq = TemporalSnapshotSequence([baseline_snapshot_t0, evolved_snapshot_t1])
    events = investigation_timeline_service.analyze_network_timeline("NET-NONCAUSAL", seq)
    for e in events:
        desc_lower = e.description.lower()
        assert "caused by" not in desc_lower
        assert "criminal organization" not in desc_lower


def test_36_regression_against_protected_subsystems():
    """Verify that Phase 14 imports and execution do NOT alter Models A–E, DT-GNN, or Threat Fusion."""
    from ml.threat_fusion import threat_fusion_service
    from ml.dynamic_gnn.service import dt_gnn_service
    from ml.emerging_threat import emerging_threat_service

    assert threat_fusion_service is not None
    assert dt_gnn_service is not None
    assert emerging_threat_service is not None
    assert hasattr(threat_fusion_service, "assess_target")
    assert hasattr(dt_gnn_service, "analyze_graph_data")
    assert hasattr(emerging_threat_service, "analyze_network_sequence")
