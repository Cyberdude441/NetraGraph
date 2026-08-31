"""Phase 5 Comprehensive Test Suite: Authorized Evidence Ingestion & Case Intelligence."""
from __future__ import annotations

import io
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
from services.evidence_intelligence_service import (
    evidence_intelligence_service,
    ProcessingStatus,
    ReviewAction,
)
from services.investigation_graph import investigation_graph_service


class TestPhase5EvidenceIntelligence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        investigation_graph_service.initialize_formal_investigation_graph()

    def test_01_evidence_upload_and_hashing(self):
        """Verify POST /api/evidence/upload validates file, computes SHA-256, and records custody."""
        sample_log = (
            "2024-03-16 14:30:00 [SIP-GATEWAY] Inbound call from +919811029182 via 103.145.22.18\n"
            "2024-03-16 14:31:00 [WEB-SERVER] Redirected victim to support-helpdesk-msft.com\n"
            "2024-03-16 14:35:00 [ESCROW-WIRE] Wire transfer to Account 918281920192 authorized by Suspect Amit Joshi\n"
        )
        file_bytes = sample_log.encode("utf-8")

        res = self.client.post(
            "/api/evidence/upload",
            files={"file": ("seizure_log_0891.txt", io.BytesIO(file_bytes), "text/plain")},
            data={
                "case_id": "CASE-2024-DEL-0891",
                "source": "CFSL Delhi Mirror Image",
                "description": "Server traffic syslog captured during raid",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("evidence_id", data)
        self.assertIn("sha256", data)
        self.assertEqual(data["case_id"], "CASE-2024-DEL-0891")
        self.assertGreater(data["staged_extractions_count"], 0)

        # Verify hash endpoint
        hash_res = self.client.get(f"/api/evidence/{data['evidence_id']}/hash")
        self.assertEqual(hash_res.status_code, 200)
        self.assertEqual(hash_res.json()["sha256"], data["sha256"])

    def test_02_chain_of_custody_tracking(self):
        """Verify GET /api/evidence/{id}/provenance returns immutable Section 65B custody log."""
        ev_list = self.client.get("/api/evidence").json()
        self.assertGreater(len(ev_list), 0)
        ev_id = ev_list[0]["id"]

        res = self.client.get(f"/api/evidence/{ev_id}/provenance")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("chain_of_custody_events", data)
        self.assertGreater(data["custody_count"], 0)

    def test_03_automated_entity_extraction_and_staging(self):
        """Verify automated extraction stages IPs, domains, phones, accounts, and person mentions."""
        staged = evidence_intelligence_service.get_staged_extractions(case_id="CASE-2024-DEL-0891")
        self.assertGreater(len(staged), 0)

        types_staged = {item["entity_type"] for item in staged}
        self.assertTrue({"IPAddress", "Domain"}.issubset(types_staged))

    def test_04_analyst_review_gate_accept(self):
        """Verify Analyst Review Gate: ACCEPT commits candidate entity to Knowledge Graph."""
        staged = evidence_intelligence_service.get_staged_extractions(case_id="CASE-2024-DEL-0891")
        target_item = next((i for i in staged if i["review_status"] == ProcessingStatus.REVIEW_REQUIRED), None)
        self.assertIsNotNone(target_item)

        ext_id = target_item["extraction_id"]
        res = self.client.post(
            f"/api/evidence/extractions/{ext_id}/review",
            json={"action": "ACCEPT", "actor": "IN-BOSE-4417"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["action"], "COMMITTED")
        self.assertIn("entity_id", data)

    def test_05_analyst_review_gate_reject(self):
        """Verify Analyst Review Gate: REJECT discards candidate link with justification."""
        staged = evidence_intelligence_service.get_staged_extractions(case_id="CASE-2024-DEL-0891")
        target_item = next((i for i in staged if i["review_status"] == ProcessingStatus.REVIEW_REQUIRED), None)
        if not target_item:
            # Create a mock staged item for rejection testing
            target_item = {
                "extraction_id": "EXT-TEST-REJECT-001",
                "entity_type": "Phone",
                "value": "9999999999",
                "review_status": ProcessingStatus.REVIEW_REQUIRED,
            }
            evidence_intelligence_service._staged_extractions["EXT-TEST-REJECT-001"] = target_item

        ext_id = target_item["extraction_id"]
        res = self.client.post(
            f"/api/evidence/extractions/{ext_id}/review",
            json={"action": "REJECT", "actor": "IN-BOSE-4417"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["action"], "REJECTED")

    def test_06_case_workspace_bundle_and_isolation(self):
        """Verify GET /api/cases/{case_id}/workspace retrieves complete isolated case bundle."""
        case_id = "CASE-2024-DEL-0891"
        res = self.client.get(f"/api/cases/{case_id}/workspace")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["case_id"], case_id)
        self.assertIn("overview", data)
        self.assertIn("evidence", data)
        self.assertIn("nodes", data)
        self.assertIn("relationships", data)
        self.assertIn("timeline", data)
        self.assertIn("analytics", data)

        # Verify strict isolation: All nodes in workspace belong to this case
        for node in data["nodes"]:
            self.assertEqual(node.get("case_id"), case_id)

    def test_07_investigation_timeline_generation(self):
        """Verify GET /api/cases/{case_id}/timeline returns chronological events."""
        case_id = "CASE-2024-DEL-0891"
        res = self.client.get(f"/api/cases/{case_id}/timeline")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("timeline", data)
        self.assertGreater(data["total_events"], 0)

    def test_08_case_graph_export(self):
        """Verify GET /api/cases/{case_id}/export exports graph in JSON and CSV."""
        case_id = "CASE-2024-DEL-0891"

        # JSON Export
        res_json = self.client.get(f"/api/cases/{case_id}/export?format=json")
        self.assertEqual(res_json.status_code, 200)
        self.assertEqual(res_json.json()["format"], "json")

        # CSV Export
        res_csv = self.client.get(f"/api/cases/{case_id}/export?format=csv")
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.json()["format"], "csv")
        self.assertIn("nodes_csv", res_csv.json())

    def test_09_ml_prediction_to_evidence_lineage(self):
        """Verify ML prediction connects decision support node to evidence artifact."""
        pred = evidence_intelligence_service.record_ml_prediction_for_evidence(
            case_id="CASE-2024-DEL-0891",
            evidence_id="EV-TEST-001",
            model_name="Phishing URL Detector v2.4 (Model C)",
            model_version="2.4.0",
            artifact_sha256="c891a88b19201a92819280192801928192819281928192819281928192819281",
            result={"prediction": 1, "verdict": "PHISHING_MALICIOUS"},
            confidence=0.97,
        )
        self.assertIn("prediction_id", pred)
        self.assertEqual(pred["status"], "DECISION_SUPPORT_ONLY")

    def test_10_negative_unresolved_name_handling(self):
        """CRITICAL NEGATIVE TEST: Extracted names remain UNRESOLVED until analyst confirmation."""
        text = "The raid at Sector 62 apprehended Suspect Ramesh Sharma operating the dialer."
        staged = evidence_intelligence_service.extract_entities_and_relationships_from_text(
            text=text,
            evidence_id="EV-TEST-002",
            case_id="CASE-2024-DEL-0891",
            source_filename="test_raid.txt",
        )
        person_items = [i for i in staged if i["entity_type"] == "Person"]
        self.assertGreater(len(person_items), 0)

        for p in person_items:
            self.assertEqual(p["resolution_status"], "UNRESOLVED")
            self.assertEqual(p["review_status"], ProcessingStatus.REVIEW_REQUIRED)


if __name__ == "__main__":
    unittest.main()
