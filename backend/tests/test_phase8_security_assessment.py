"""Phase 8 Test Suite: Security Assessment, Threat Intelligence Fusion, Anomaly Engine, and Observability."""
from __future__ import annotations

import unittest
from pathlib import Path
import sys
from fastapi.testclient import TestClient

# Add backend directory to sys.path
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app
from services.threat_intelligence_service import threat_intelligence_service
from services.graph_anomaly_engine import graph_anomaly_engine
from services.ncrb_temporal_service import ncrb_temporal_service
from services.security_service import security_service, Permission


class TestPhase8SecurityAssessment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # =========================================================================
    # 1. Threat Intelligence Fusion Tests
    # =========================================================================
    def test_01_threat_intel_feed_lookup_and_domain_tagging(self):
        """Verify external IOC feed lookups are strictly tagged as EXTERNAL_THREAT_INTEL."""
        hit = threat_intelligence_service.lookup_indicator("103.145.22.18")
        self.assertIsNotNone(hit)
        self.assertEqual(hit["reputation"], "MALICIOUS")
        self.assertEqual(hit["domain_tag"], "EXTERNAL_THREAT_INTEL")

    def test_02_case_threat_intel_correlation(self):
        """Verify case entities correlate with external CTI feeds without mutating official graph records."""
        sample_entities = [
            {"id": "ip:103.145.22.18", "name": "103.145.22.18", "label": "IPAddress", "case_id": "CASE-2024-DEL-0891"},
            {"id": "dom:support-msft", "name": "support-helpdesk-msft.com", "label": "Domain", "case_id": "CASE-2024-DEL-0891"},
            {"id": "ip:benign", "name": "8.8.8.8", "label": "IPAddress", "case_id": "CASE-2024-DEL-0891"},
        ]
        matches = threat_intelligence_service.correlate_case_entities(sample_entities)
        self.assertEqual(len(matches), 2)
        matched_indicators = [m["entity_name"] for m in matches]
        self.assertIn("103.145.22.18", matched_indicators)
        self.assertIn("support-helpdesk-msft.com", matched_indicators)

    # =========================================================================
    # 2. Graph Structural Anomaly Detection Engine Tests
    # =========================================================================
    def test_03_graph_structural_anomalies_and_non_inculpatory_rules(self):
        """Verify anomaly detection identifies topological signals and includes non-judgmental disclaimers."""
        res = graph_anomaly_engine.analyze_case_structural_anomalies("CASE-2024-DEL-0891")
        self.assertIn("structural_signals", res)
        self.assertIn("governance_disclaimer", res)

        # Check that no signal mentions guilt or masterminds
        for sig in res["structural_signals"]:
            desc = sig["description"].lower()
            note = sig["investigative_note"].lower()
            self.assertNotIn("guilty", desc)
            self.assertNotIn("mastermind", desc)
            self.assertNotIn("guilty", note)
            self.assertNotIn("mastermind", note)

    # =========================================================================
    # 3. Investigation Scorecard & Timeline Tests
    # =========================================================================
    def test_04_investigation_intelligence_scorecard_api(self):
        """Verify /api/cases/{case_id}/scorecard returns actionable evidentiary gap analysis."""
        res = self.client.get("/api/cases/CASE-2024-DEL-0891/scorecard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("scorecard", data)
        self.assertIn("evidence_coverage_pct", data["scorecard"])
        self.assertIn("evidence_gaps", data)
        self.assertIn("investigative_guidance", data)

    def test_05_intelligence_timeline_stream_api(self):
        """Verify /api/cases/{case_id}/intelligence-timeline returns multi-stream chronological records."""
        res = self.client.get("/api/cases/CASE-2024-DEL-0891/intelligence-timeline")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("events", data)
        self.assertIn("streams", data)

    # =========================================================================
    # 4. Temporal Intelligence & Schema Drift Tests
    # =========================================================================
    def test_06_state_vs_national_differential_comparison(self):
        """Verify state-vs-national calculation computes proportions accurately."""
        res = ncrb_temporal_service.compare_state_vs_national("Telangana")
        self.assertEqual(res["state"], "Telangana")
        self.assertGreater(res["national_share_percentage"], 0.0)

    def test_07_ogd_schema_drift_resilience(self):
        """Verify schema resilience gracefully flags drift when OGD column headers vary."""
        drift_payload = [
            {"State_Name": "Odisha", "Total_Cyber_Crimes_2025": 2100, "Unrecognized_Column": "Test"}
        ]
        res = ncrb_temporal_service.validate_schema_resilience("ogd-it-act", drift_payload)
        self.assertTrue(res["drift_detected"])
        self.assertEqual(res["status"], "VALIDATED_WITH_DRIFT_COMPATIBILITY")

    # =========================================================================
    # 5. Production Observability & Milestone Nomenclature
    # =========================================================================
    def test_08_production_health_and_milestone_wording(self):
        """Verify /api/system/health returns correct status and academic milestone wording."""
        res = self.client.get("/api/system/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "HEALTHY")
        expected_milestone = "Engineering deployment-ready; pending operational security assessment and real-world pilot validation."
        self.assertEqual(data["deployment_milestone"], expected_milestone)

    def test_09_observability_metrics_endpoint(self):
        """Verify /api/system/metrics returns latency telemetry and zero failure counters."""
        res = self.client.get("/api/system/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("observability", data)
        self.assertEqual(data["observability"]["failed_requests_count"], 0)
        self.assertEqual(data["observability"]["database_connection_health"], "HEALTHY")

    def test_10_case_threat_intel_endpoint(self):
        """Verify /api/cases/{case_id}/threat-intel returns fused indicators."""
        res = self.client.get("/api/cases/CASE-2024-DEL-0891/threat-intel")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["domain_tag"], "EXTERNAL_THREAT_INTEL")


if __name__ == "__main__":
    unittest.main()
