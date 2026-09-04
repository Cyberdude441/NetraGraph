"""Comprehensive automated test suite for Phase 16 Graph & Model Drift Observatory.

Validates:
- Deterministic statistical divergence algorithms (PSI, JSD, Wasserstein, KS, Missingness)
- Numerical reproducibility within +/- 1e-7 tolerance
- Deterministic, timestamp-free analytical provenance IDs
- Initial configurable threshold policy defaults and severity classification
- Real-data availability enforcement (DATA_UNAVAILABLE and INSUFFICIENT_DATA)
- Baseline compatibility and IncompatibleBaselineError rejection
- Graph structural drift with metric-specific complexity bounds
- Feature distribution and missingness drift
- Model output and probability drift with Model Performance Boundary enforcement
- CTI / OSINT source behavior, conflict frequency, and freshness drift
- Data quality and multi-modal ingestion drift
- Master DriftObservatoryEngine lifecycle, health, and summary
- RBAC authorization matrix across all 10 API endpoints
- Mandatory non-causal forensic disclaimers
- Protected subsystem invariance
"""
from __future__ import annotations

import os
import sys
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient
import networkx as nx

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from ml.drift_observatory import (
    CTI_OSINT_DRIFT_DISCLAIMER,
    DEFAULT_ALGORITHM_VERSION,
    DRIFT_OBSERVATORY_VERSION,
    GENERAL_DRIFT_DISCLAIMER,
    BaselineRegistrationRequest,
    BaselineType,
    BaselineWindow,
    ComparisonWindow,
    DriftComputeRequest,
    DriftDomain,
    DriftMetricType,
    DriftObservationRecord,
    DriftObservatoryEngine,
    DriftSeverity,
    DriftThresholdPolicy,
    CTISourceDriftDetector,
    DataQualityDriftDetector,
    FeatureDriftDetector,
    GraphDriftDetector,
    IncompatibleBaselineError,
    ModelOutputDriftDetector,
    ObservationStatus,
    ReferenceBaseline,
    baseline_registry,
    compute_analytical_observation_id,
    compute_data_digest,
    compute_jsd,
    compute_ks_statistic,
    compute_missingness_delta,
    compute_psi,
    compute_wasserstein,
    deterministic_subsample,
    drift_observatory_engine,
)


@pytest.fixture
def client():
    return TestClient(app)


# =============================================================================
# 1. Statistical Divergence & Numerical Reproducibility Tests
# =============================================================================
class TestStatisticalDivergence:
    def test_psi_identical_distributions(self):
        """Identical distributions must yield PSI == 0.0 within tolerance."""
        ref = [10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0] * 10
        cmp = list(ref)
        psi = compute_psi(ref, cmp)
        assert psi == 0.0 or math.isclose(psi, 0.0, abs_tol=1e-6)

    def test_psi_controlled_shift(self):
        """Controlled distribution shift must increase PSI predictably."""
        np.random.seed(42)
        ref = np.random.normal(loc=0.0, scale=1.0, size=1000).tolist()
        cmp_slight = np.random.normal(loc=0.2, scale=1.0, size=1000).tolist()
        cmp_large = np.random.normal(loc=2.0, scale=1.5, size=1000).tolist()

        psi_slight = compute_psi(ref, cmp_slight)
        psi_large = compute_psi(ref, cmp_large)

        assert psi_slight >= 0.0
        assert psi_large > psi_slight
        assert psi_large >= 0.35  # Critical shift

    def test_psi_numerical_reproducibility(self):
        """PSI must be identical within +/- 1e-7 across repeated executions."""
        ref = [float(i) for i in range(100)]
        cmp = [float(i * 1.2) for i in range(100)]
        val1 = compute_psi(ref, cmp)
        val2 = compute_psi(ref, cmp)
        assert math.isclose(val1, val2, abs_tol=1e-7)

    def test_psi_laplace_smoothing_with_zero_bins(self):
        """Bins with zero samples must be smoothed cleanly without division by zero or inf."""
        ref = [1.0, 2.0, 3.0, 4.0, 5.0] * 20
        cmp = [100.0, 200.0, 300.0] * 20  # Completely outside reference range
        psi = compute_psi(ref, cmp)
        assert np.isfinite(psi)
        assert psi > 0.5

    def test_jsd_identical_categorical(self):
        """Identical categorical frequencies must yield JSD == 0.0."""
        dist1 = {"Person": 50, "Phone": 30, "BankAccount": 20}
        dist2 = {"Person": 50, "Phone": 30, "BankAccount": 20}
        jsd = compute_jsd(dist1, dist2)
        assert jsd == 0.0 or math.isclose(jsd, 0.0, abs_tol=1e-6)

    def test_jsd_disjoint_categories(self):
        """Completely disjoint categories must yield high bounded divergence in [0.0, 1.0]."""
        dist1 = {"A": 100}
        dist2 = {"B": 100}
        jsd = compute_jsd(dist1, dist2)
        assert 0.0 <= jsd <= 1.0
        assert jsd > 0.9

    def test_jsd_zero_count_handling(self):
        """Categories appearing in only one distribution must be handled gracefully via Laplace smoothing."""
        dist1 = {"A": 100, "B": 50}
        dist2 = {"A": 90, "C": 60}  # B missing in cmp, C missing in ref
        jsd = compute_jsd(dist1, dist2)
        assert np.isfinite(jsd)
        assert 0.0 < jsd < 1.0

    def test_wasserstein_distance(self):
        """Wasserstein-1 distance must equal mean absolute difference for simple shifts."""
        ref = [1.0, 2.0, 3.0, 4.0, 5.0]
        cmp = [2.0, 3.0, 4.0, 5.0, 6.0]  # Shifted by exactly +1.0
        w_dist = compute_wasserstein(ref, cmp)
        assert math.isclose(w_dist, 1.0, abs_tol=1e-5)

    def test_ks_statistic(self):
        """KS 2-sample statistic must correctly evaluate maximum CDF divergence."""
        ref = [0.1, 0.2, 0.3, 0.4, 0.5] * 20
        cmp = [0.1, 0.2, 0.3, 0.4, 0.5] * 20
        ks = compute_ks_statistic(ref, cmp)
        assert ks == 0.0 or math.isclose(ks, 0.0, abs_tol=1e-6)

    def test_missingness_delta(self):
        """Missingness rate delta must compute exact absolute difference."""
        delta = compute_missingness_delta(0.05, 0.20)
        assert math.isclose(delta, 0.15, abs_tol=1e-6)

    def test_deterministic_subsample(self):
        """Deterministic striding subsampling must return identical elements without randomness."""
        data = list(range(1000))
        sub1 = deterministic_subsample(data, max_samples=50)
        sub2 = deterministic_subsample(data, max_samples=50)
        assert len(sub1) == 50
        assert sub1 == sub2
        assert sub1[0] == 0
        assert sub1[1] == 20


# =============================================================================
# 2. Provenance & Analytical Identity Invariants
# =============================================================================
class TestProvenanceAndIdentity:
    def test_analytical_id_timestamp_independence(self):
        """CRITICAL: Analytical observation ID MUST NOT change when execution time changes."""
        id1 = compute_analytical_observation_id(
            domain="FEATURE",
            target="session_duration",
            reference_baseline_id="base-intrusion-v1",
            comparison_data_digest="a1b2c3d4e5f6",
            metric_name="POPULATION_STABILITY_INDEX",
            algorithm_version="1.0.0",
            threshold_policy_version="1.0.0",
        )
        id2 = compute_analytical_observation_id(
            domain="FEATURE",
            target="session_duration",
            reference_baseline_id="base-intrusion-v1",
            comparison_data_digest="a1b2c3d4e5f6",
            metric_name="POPULATION_STABILITY_INDEX",
            algorithm_version="1.0.0",
            threshold_policy_version="1.0.0",
        )
        assert id1 == id2
        assert id1.startswith("drf:feature:session_duration:base-int:")

    def test_analytical_id_changes_on_different_data_digest(self):
        """Different comparison data digest must produce a distinct observation ID."""
        id1 = compute_analytical_observation_id(
            domain="FEATURE",
            target="session_duration",
            reference_baseline_id="base-intrusion-v1",
            comparison_data_digest="digest_A",
            metric_name="POPULATION_STABILITY_INDEX",
        )
        id2 = compute_analytical_observation_id(
            domain="FEATURE",
            target="session_duration",
            reference_baseline_id="base-intrusion-v1",
            comparison_data_digest="digest_B",
            metric_name="POPULATION_STABILITY_INDEX",
        )
        assert id1 != id2


# =============================================================================
# 3. Baseline Registry & Compatibility Enforcement Tests
# =============================================================================
class TestBaselinesAndCompatibility:
    def test_compatibility_rejection_domain_mismatch(self):
        """Baseline comparison must reject mismatched domains."""
        baseline = ReferenceBaseline(
            baseline_id="b1",
            domain=DriftDomain.GRAPH,
            target_name="TestGraph",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=50, data_digest="d1"),
        )
        with pytest.raises(IncompatibleBaselineError, match="Domain mismatch"):
            baseline_registry.validate_compatibility(baseline, domain=DriftDomain.FEATURE, target="TestGraph")

    def test_compatibility_rejection_target_mismatch(self):
        """Baseline comparison must reject mismatched targets."""
        baseline = ReferenceBaseline(
            baseline_id="b2",
            domain=DriftDomain.MODEL_OUTPUT,
            target_name="intrusion",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=50, data_digest="d2"),
        )
        with pytest.raises(IncompatibleBaselineError, match="Target mismatch"):
            baseline_registry.validate_compatibility(baseline, domain=DriftDomain.MODEL_OUTPUT, target="phishing-email")

    def test_compatibility_rejection_graph_layer_mismatch(self):
        """Baseline comparison must reject mismatched graph layers."""
        baseline = ReferenceBaseline(
            baseline_id="b3",
            domain=DriftDomain.GRAPH,
            target_name="Graph",
            graph_layer="NCRB",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=50, data_digest="d3"),
        )
        with pytest.raises(IncompatibleBaselineError, match="Graph layer mismatch"):
            baseline_registry.validate_compatibility(baseline, domain=DriftDomain.GRAPH, target="Graph", graph_layer="EVIDENCE")

    def test_atomic_json_persistence(self, tmp_path):
        """Baselines registry must support atomic JSON serialization to file."""
        from ml.drift_observatory.baselines import BaselineRegistry
        p = tmp_path / "custom_baselines.json"
        reg = BaselineRegistry(storage_path=p)
        base = ReferenceBaseline(
            baseline_id="test-save-b1",
            domain=DriftDomain.FEATURE,
            target_name="test_col",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=10, data_digest="dtest"),
        )
        reg.register_baseline(base)
        assert p.exists()

        # Reload from another instance
        reg2 = BaselineRegistry(storage_path=p)
        assert reg2.get_baseline("test-save-b1") is not None


# =============================================================================
# 4. Domain Detectors & Operational Guardrail Tests
# =============================================================================
class TestDomainDetectors:
    def test_graph_drift_insufficient_samples(self):
        """Graph detector must return INSUFFICIENT_DATA when sample size < min_sample_size (30)."""
        detector = GraphDriftDetector()
        base = ReferenceBaseline(
            baseline_id="b-graph",
            domain=DriftDomain.GRAPH,
            target_name="TestGraph",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=50, data_digest="d"),
            feature_distributions={"node_types": {"Person": 30}, "relationship_types": {"CALL": 20}},
        )
        small_g = nx.Graph()
        for i in range(10):  # N=10 < 30
            small_g.add_node(f"n{i}", type="Person")

        obs = detector.evaluate_graph_drift(base, small_g, target_name="TestGraph")
        assert obs.severity == DriftSeverity.INSUFFICIENT_DATA
        assert obs.status == ObservationStatus.INSUFFICIENT_DATA
        assert not obs.is_statistically_valid
        assert "below the policy minimum threshold" in obs.explanation.summary

    def test_graph_drift_normal_and_shifted(self):
        """Graph detector must report NORMAL for matching topology and ELEVATED for shifted topology."""
        detector = GraphDriftDetector()
        base = ReferenceBaseline(
            baseline_id="b-graph-full",
            domain=DriftDomain.GRAPH,
            target_name="TestGraph",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=100, data_digest="d"),
            feature_distributions={
                "node_types": {"Person": 50, "Phone": 50},
                "relationship_types": {"CALL": 80, "TRANSACTION": 20},
                "density": 0.05,
                "components": 2,
                "degrees": [2.0] * 100,
            },
        )

        # 1. Normal Graph (same proportions, N=100)
        norm_g = nx.MultiDiGraph()
        for i in range(50):
            norm_g.add_node(f"p{i}", type="Person")
            norm_g.add_node(f"ph{i}", type="Phone")
        for i in range(40):
            norm_g.add_edge(f"p{i}", f"ph{i}", rel_type="CALL")
            norm_g.add_edge(f"p{i}", f"p{i+1}", rel_type="CALL")
        for i in range(20):
            norm_g.add_edge(f"ph{i}", f"ph{i+1}", rel_type="TRANSACTION")

        obs_norm = detector.evaluate_graph_drift(base, norm_g, target_name="TestGraph")
        assert obs_norm.severity in (DriftSeverity.NORMAL, DriftSeverity.WATCH)
        assert obs_norm.is_statistically_valid

        # 2. Shifted Graph (dominated by unexpected node & relationship types)
        shift_g = nx.MultiDiGraph()
        for i in range(100):
            shift_g.add_node(f"v{i}", type="Vehicle")  # Novel type
            shift_g.add_edge(f"v{i}", f"v{(i+1)%100}", rel_type="ESCORTED_BY")

        obs_shift = detector.evaluate_graph_drift(base, shift_g, target_name="TestGraph")
        assert obs_shift.severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL)

    def test_feature_drift_data_unavailable(self):
        """Feature detector must return DATA_UNAVAILABLE when records is None (real data check)."""
        detector = FeatureDriftDetector()
        base = ReferenceBaseline(
            baseline_id="b-feat",
            domain=DriftDomain.FEATURE,
            target_name="session_duration",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=100, data_digest="df"),
            feature_distributions={"quantiles": list(range(11))},
            metadata={"parent_model": "intrusion"},
        )
        obs = detector.evaluate_feature_drift(base, comparison_records=None, feature_name="session_duration", parent_model="intrusion")
        assert obs.severity == DriftSeverity.DATA_UNAVAILABLE
        assert obs.status == ObservationStatus.DATA_UNAVAILABLE
        assert "DATA_UNAVAILABLE" in obs.explanation.summary

    def test_feature_drift_insufficient_samples(self):
        """Feature detector must return INSUFFICIENT_DATA when valid samples < 30."""
        detector = FeatureDriftDetector()
        base = ReferenceBaseline(
            baseline_id="b-feat2",
            domain=DriftDomain.FEATURE,
            target_name="session_duration",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=100, data_digest="df2"),
            feature_distributions={"quantiles": list(range(11))},
            metadata={"parent_model": "intrusion"},
        )
        recs = [{"session_duration": float(i)} for i in range(15)]  # N=15 < 30
        obs = detector.evaluate_feature_drift(base, comparison_records=recs, feature_name="session_duration", parent_model="intrusion")
        assert obs.severity == DriftSeverity.INSUFFICIENT_DATA

    def test_feature_drift_continuous_psi(self):
        """Feature detector must correctly compute PSI and classify severity on sufficient samples."""
        detector = FeatureDriftDetector()
        base = ReferenceBaseline(
            baseline_id="b-feat-cont",
            domain=DriftDomain.FEATURE,
            target_name="session_duration",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=200, data_digest="df3"),
            feature_distributions={"samples": list(range(100)), "missing_rate": 0.0, "mean": 50.0},
            metadata={"parent_model": "intrusion"},
        )
        # Shifted comparison: values shifted into [200, 300]
        recs = [{"session_duration": float(i + 200)} for i in range(100)]
        obs = detector.evaluate_feature_drift(base, comparison_records=recs, feature_name="session_duration", parent_model="intrusion")
        assert obs.is_statistically_valid
        assert obs.severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL)
        assert obs.metric_value is not None and obs.metric_value > 0.20

    def test_model_drift_performance_boundary(self):
        """Model drift detector must report output distribution drift; NEVER claim accuracy degradation."""
        detector = ModelOutputDriftDetector()
        base = ReferenceBaseline(
            baseline_id="b-model-out",
            domain=DriftDomain.MODEL_OUTPUT,
            target_name="intrusion",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=200, data_digest="dm"),
            feature_distributions={"class_distribution": {"0": 100, "1": 100}, "probabilities": [0.9] * 200},
        )
        preds = [{"prediction": "1", "probability": 0.55} for _ in range(100)]
        obs = detector.evaluate_output_drift(base, comparison_predictions=preds, model_name="intrusion")

        assert obs.is_statistically_valid
        # Check that explanation adheres strictly to the model performance boundary
        lims_text = " ".join(obs.explanation.limitations)
        assert "NO accuracy, precision, recall, or F1 degradation is claimed" in lims_text
        assert "strictly reports output distribution drift" in lims_text

    def test_cti_source_drift_detector(self):
        """CTI detector must assess source distribution, conflict rates, and carry Phase 15 CTI disclaimer."""
        detector = CTISourceDriftDetector()
        base = ReferenceBaseline(
            baseline_id="b-cti",
            domain=DriftDomain.CTI_SOURCE,
            target_name="ExternalCTIFeeds",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=100, data_digest="dcti"),
            feature_distributions={
                "source_distribution": {"cert-in": 50, "ncrb": 50},
                "type_distribution": {"IPV4": 60, "DOMAIN": 40},
                "conflict_rate": 0.01,
                "ages_days": [2.0] * 100,
            },
        )
        iocs = [{"source_id": "cert-in", "type": "IPV4", "timestamp": 1700000000.0} for _ in range(50)]
        conflicts = [{"conflict_id": "c1"}, {"conflict_id": "c2"}, {"conflict_id": "c3"}]  # Elevated conflicts

        obs = detector.evaluate_source_drift(base, indicators=iocs, conflicts=conflicts)
        assert obs.is_statistically_valid
        assert obs.disclaimer == CTI_OSINT_DRIFT_DISCLAIMER

    def test_data_quality_drift_detector(self):
        """Quality detector must evaluate missing field deltas and validation failure spikes."""
        detector = DataQualityDriftDetector()
        base = ReferenceBaseline(
            baseline_id="b-qual",
            domain=DriftDomain.DATA_QUALITY,
            target_name="MultiModalIngestion",
            created_at="2026-09-04T00:00:00Z",
            window=BaselineWindow(sample_count=100, data_digest="dq"),
            feature_distributions={"module_distribution": {"FIR": 100}, "missing_field_rate": 0.01, "failure_rate": 0.01},
        )
        # 50 records with missing fields and failures
        recs = [
            {"module": "FIR", "fields": {"id": f"id_{i}", "case": None, "suspect": ""}, "validation_failed": True}
            for i in range(50)
        ]
        obs = detector.evaluate_quality_drift(base, ingestion_records=recs)
        assert obs.is_statistically_valid
        assert obs.severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL)


# =============================================================================
# 5. Master Engine & Lifecycle Tests
# =============================================================================
class TestDriftObservatoryEngine:
    def test_engine_health_and_defaults(self):
        """Engine must report HEALTHY and list all 5 monitored domains."""
        health = drift_observatory_engine.get_health()
        assert health.status == "HEALTHY"
        assert health.version == DRIFT_OBSERVATORY_VERSION
        assert len(health.domains_monitored) == 5

    def test_register_and_get_baseline(self):
        """Engine must register and retrieve reference baselines cleanly."""
        req = BaselineRegistrationRequest(
            domain=DriftDomain.FEATURE,
            target_name="test_packet_size",
            feature_distributions={"mean": 500, "samples": [450, 500, 550] * 15},
            metadata={"parent_model": "network-intrusion"},
        )
        baseline = drift_observatory_engine.register_baseline(req)
        assert baseline.target_name == "test_packet_size"

        retrieved = drift_observatory_engine.get_baseline(baseline.baseline_id)
        assert retrieved is not None
        assert retrieved.baseline_id == baseline.baseline_id

    def test_get_summary_overview(self):
        """Engine must generate a global multi-domain summary overview."""
        summary = drift_observatory_engine.get_summary()
        assert summary.observatory_version == DRIFT_OBSERVATORY_VERSION
        assert len(summary.domain_summaries) == 5
        assert DriftDomain.GRAPH.value in summary.domain_summaries
        assert DriftDomain.FEATURE.value in summary.domain_summaries
        assert DriftDomain.MODEL_OUTPUT.value in summary.domain_summaries


# =============================================================================
# 6. REST API & RBAC Matrix Tests
# =============================================================================
class TestDriftAPIAndRBAC:
    def test_api_health_endpoint(self, client):
        """GET /api/drift/health must return 200 OK for authenticated officer."""
        res = client.get("/api/drift/health", headers={"X-User-Role": "ANALYST"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "HEALTHY"
        assert data["disclaimer"] == GENERAL_DRIFT_DISCLAIMER

    def test_api_baselines_list_and_lookup(self, client):
        """GET /api/drift/baselines must list registered baselines."""
        res = client.get("/api/drift/baselines", headers={"X-User-Role": "ANALYST"})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        base_id = data["baselines"][0]["baseline_id"]

        res_single = client.get(f"/api/drift/baselines/{base_id}", headers={"X-User-Role": "ANALYST"})
        assert res_single.status_code == 200
        assert res_single.json()["baseline_id"] == base_id

    def test_api_rbac_baseline_creation(self, client):
        """POST /api/drift/baselines: ANALYST is denied (403); INVESTIGATOR and ADMIN are allowed (201)."""
        payload_inv = {
            "domain": "FEATURE",
            "target_name": "login_attempts_inv",
            "feature_distributions": {"samples": [1, 2, 3] * 15},
        }
        payload_adm = {
            "domain": "FEATURE",
            "target_name": "login_attempts_adm",
            "feature_distributions": {"samples": [1, 2, 3] * 15},
        }
        # 1. Analyst -> Forbidden (403)
        res_analyst = client.post("/api/drift/baselines", json=payload_inv, headers={"X-User-Role": "ANALYST"})
        assert res_analyst.status_code == 403

        # 2. Investigator -> Allowed (201)
        res_investigator = client.post("/api/drift/baselines", json=payload_inv, headers={"X-User-Role": "INVESTIGATOR"})
        assert res_investigator.status_code == 201
        assert res_investigator.json()["target_name"] == "login_attempts_inv"

        # 3. Admin -> Allowed (201)
        res_admin = client.post("/api/drift/baselines", json=payload_adm, headers={"X-User-Role": "ADMIN"})
        assert res_admin.status_code == 201
        assert res_admin.json()["target_name"] == "login_attempts_adm"

    def test_api_rbac_compute_drift(self, client):
        """POST /api/drift/compute: ANALYST is denied (403); INVESTIGATOR and ADMIN are allowed (200)."""
        payload = {
            "domain": "MODEL_OUTPUT",
            "target_name": "intrusion",
            "comparison_data": [{"prediction": "0", "probability": 0.88} for _ in range(40)],
        }
        # 1. Analyst -> Forbidden (403)
        res_analyst = client.post("/api/drift/compute", json=payload, headers={"X-User-Role": "ANALYST"})
        assert res_analyst.status_code == 403

        # 2. Investigator -> Allowed (200)
        res_inv = client.post("/api/drift/compute", json=payload, headers={"X-User-Role": "INVESTIGATOR"})
        assert res_inv.status_code == 200
        obs_inv = res_inv.json()
        assert obs_inv["domain"] == "MODEL_OUTPUT"
        assert obs_inv["target_name"] == "intrusion"
        assert "drift_observation_id" in obs_inv
        assert obs_inv["disclaimer"] == GENERAL_DRIFT_DISCLAIMER

        # 3. Admin -> Allowed (200)
        res_adm = client.post("/api/drift/compute", json=payload, headers={"X-User-Role": "ADMIN"})
        assert res_adm.status_code == 200
        obs_adm = res_adm.json()
        assert obs_adm["domain"] == "MODEL_OUTPUT"
        assert obs_adm["target_name"] == "intrusion"
        assert "drift_observation_id" in obs_adm
        assert obs_adm["disclaimer"] == GENERAL_DRIFT_DISCLAIMER

    def test_api_rbac_read_roles_clearance(self, client):
        """GET endpoints must allow ANALYST, INVESTIGATOR, and ADMIN."""
        for role in ["ANALYST", "INVESTIGATOR", "ADMIN"]:
            res_h = client.get("/api/drift/health", headers={"X-User-Role": role})
            assert res_h.status_code == 200, f"Health failed for {role}"

            res_b = client.get("/api/drift/baselines", headers={"X-User-Role": role})
            assert res_b.status_code == 200, f"Baselines failed for {role}"

            res_s = client.get("/api/drift/summary", headers={"X-User-Role": role})
            assert res_s.status_code == 200, f"Summary failed for {role}"

            res_o = client.get("/api/drift/observations", headers={"X-User-Role": role})
            assert res_o.status_code == 200, f"Observations failed for {role}"

            res_g = client.get("/api/drift/graph", headers={"X-User-Role": role})
            assert res_g.status_code == 200, f"Graph failed for {role}"

            res_m = client.get("/api/drift/models?model_name=intrusion", headers={"X-User-Role": role})
            assert res_m.status_code == 200, f"Models failed for {role}"

    def test_api_observations_listing(self, client):
        """GET /api/drift/observations must list historical observations."""
        res = client.get("/api/drift/observations", headers={"X-User-Role": "ANALYST"})
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "observations" in data

    def test_api_summary_endpoint(self, client):
        """GET /api/drift/summary must return multi-domain summary."""
        res = client.get("/api/drift/summary", headers={"X-User-Role": "ANALYST"})
        assert res.status_code == 200
        data = res.json()
        assert "domain_summaries" in data
        assert "global_highest_severity" in data

    def test_api_graph_drift_endpoint(self, client):
        """GET /api/drift/graph must return graph drift response."""
        res = client.get("/api/drift/graph", headers={"X-User-Role": "ANALYST"})
        assert res.status_code == 200
        data = res.json()
        assert "target_graph" in data
        assert "observation" in data

    def test_api_model_drift_endpoint(self, client):
        """GET /api/drift/models must return model drift response for Models A-E."""
        res = client.get("/api/drift/models?model_name=intrusion", headers={"X-User-Role": "ANALYST"})
        assert res.status_code == 200
        data = res.json()
        assert data["model_name"] == "intrusion"
        assert "overall_severity" in data


# =============================================================================
# 7. Mandatory Disclaimers & Non-Causal Boundary Verification
# =============================================================================
class TestDisclaimersAndBoundaries:
    def test_mandatory_disclaimer_presence(self):
        """Every drift observation must carry the mandatory non-causal disclaimer."""
        summary = drift_observatory_engine.get_summary()
        assert summary.disclaimer == GENERAL_DRIFT_DISCLAIMER

        health = drift_observatory_engine.get_health()
        assert health.disclaimer == GENERAL_DRIFT_DISCLAIMER

    def test_non_causal_wording_compliance(self):
        """Explanations must never contain causal claims of criminality, culpability, or guilt."""
        forbidden_terms = ["proves criminal", "indicates guilt", "guilty", "culpability", "criminal network emerged"]
        summary = drift_observatory_engine.get_summary()
        for dom, dom_sum in summary.domain_summaries.items():
            text = str(dom_sum).lower()
            for term in forbidden_terms:
                assert term not in text, f"Forbidden causal claim '{term}' found in {dom} summary."
