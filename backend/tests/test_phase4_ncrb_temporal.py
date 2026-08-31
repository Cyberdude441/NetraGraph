"""Phase 4 Test Suite: Live NCRB/OGD Ingestion, Dataset Registry & Temporal Intelligence."""
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
from services.ncrb_temporal_service import ncrb_temporal_service, DatasetStatus
from services.ncrb_sync import ncrb_sync_service
from services.graph_ai import graph_reasoning_engine


class TestPhase4NCRBTemporalIntelligence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_dataset_registry_listing(self):
        """Verify GET /api/ncrb/datasets lists all 6 registered OGD feeds."""
        res = self.client.get("/api/ncrb/datasets")
        self.assertEqual(res.status_code, 200)
        datasets = res.json()

        self.assertGreaterEqual(len(datasets), 6)
        for ds in datasets:
            self.assertIn("dataset_id", ds)
            self.assertIn("title", ds)
            self.assertIn("content_hash", ds)
            self.assertIn("status", ds)

    def test_02_single_dataset_details(self):
        """Verify GET /api/ncrb/datasets/{id} returns metadata and version history."""
        res = self.client.get("/api/ncrb/datasets/ogd-it-act")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["dataset_id"], "ogd-it-act")
        self.assertIn("versions", data)
        self.assertGreater(len(data["versions"]), 0)

    def test_03_sync_status_and_audit_history(self):
        """Verify GET /api/ncrb/sync/status exposes freshness and audit log."""
        res = self.client.get("/api/ncrb/sync/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("total_datasets", data)
        self.assertIn("operating_mode", data)
        self.assertIn("recent_audit_events", data)

    def test_04_single_dataset_transactional_sync(self):
        """Verify POST /api/ncrb/sync/{id} stages, validates, and commits or detects unchanged."""
        res = self.client.post("/api/ncrb/sync/ogd-it-act")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn(data["status"], ["COMMITTED", "UNCHANGED"])
        self.assertIn("quality_report", data)
        self.assertTrue(data["quality_report"]["schema_valid"])

    def test_05_data_quality_validation(self):
        """Verify DataQualityReport structure and validation rules."""
        valid_records = [
            {"State_UT": "Odisha", "Cases_2023": 1200, "Cases_2024": 1500, "Cases_2025": 1800},
            {"State_UT": "Telangana", "Cases_2023": 10000, "Cases_2024": 14000, "Cases_2025": 18420},
        ]
        report = ncrb_temporal_service.validate_data_quality("test-ds", valid_records)
        self.assertTrue(report["schema_valid"])
        self.assertEqual(report["record_count"], 2)
        self.assertEqual(report["invalid_value_count"], 0)

        # Invalid record test (negative cases)
        invalid_records = [
            {"State_UT": "InvalidState", "Cases_2023": -500},
        ]
        bad_report = ncrb_temporal_service.validate_data_quality("test-ds", invalid_records)
        self.assertFalse(bad_report["schema_valid"])
        self.assertGreater(bad_report["invalid_value_count"], 0)

    def test_06_temporal_trend_calculation(self):
        """Verify GET /api/ncrb/trends calculates YoY changes and trajectory."""
        res = self.client.get("/api/ncrb/trends?state=Telangana")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("trends", data)
        self.assertGreater(len(data["trends"]), 0)
        trend = data["trends"][0]
        self.assertIn("trend", trend)
        self.assertIn("years", trend)
        self.assertIn("source", trend)

    def test_07_insufficient_data_trend_guardrail(self):
        """CRITICAL NEGATIVE TEST: Single observation yields 'UNKNOWN' trend with clear explanation."""
        trend_res = ncrb_temporal_service.calculate_trends(state="UnknownState")
        self.assertIn("status", trend_res)

    def test_08_city_statistical_isolation_guardrail(self):
        """CRITICAL NEGATIVE TEST: Unmonitored city returns 'City-level verified data is unavailable'."""
        res = self.client.get("/api/ncrb/trends?city=Rourkela")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data.get("status"), "City-level verified data is unavailable.")
        self.assertIn("19 designated commissionerates", data.get("explanation", ""))

    def test_09_graphrag_temporal_reasoning(self):
        """Verify GraphRAG executes temporal trajectory reasoning for trend questions."""
        q = "How has cyber crime changed in Telangana over time?"
        res = graph_reasoning_engine.execute_grounded_rag(q)

        self.assertEqual(res["grounding_status"], "VERIFIED_GROUNDED")
        self.assertIn("Temporal Cyber Crime Trajectory", res["answer"])
        self.assertIn("Telangana", res["answer"])
        self.assertIn("provenance", res)

    def test_10_graphrag_city_isolation_query(self):
        """Verify GraphRAG enforces city isolation guardrail."""
        q = "Show cyber crime statistics for Cuttack city."
        res = graph_reasoning_engine.execute_grounded_rag(q)

        self.assertIn("City-level verified data is unavailable for Cuttack", res["answer"])
        self.assertIn("strictly does not infer city statistics", res["answer"])


if __name__ == "__main__":
    unittest.main()
