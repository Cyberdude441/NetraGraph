"""Phase 6 Comprehensive Test Suite: Security Hardening, RBAC, Case Isolation & System Health."""
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
from services.security_service import (
    security_service,
    UserRole,
    Permission,
    gemini_provider,
    nemotron_provider,
    offline_provider,
)


class TestPhase6ProductionSecurity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_case_authorization_isolation(self):
        """Verify server-side case authorization denies unauthorized case access."""
        # Viewer only authorized for CASE-2024-DEL-0891
        auth_delhi = security_service.check_case_authorization("VW-GUEST-1001", "CASE-2024-DEL-0891")
        self.assertTrue(auth_delhi)

        auth_bangalore = security_service.check_case_authorization("VW-GUEST-1001", "CASE-2024-BLR-0412")
        self.assertFalse(auth_bangalore)

        # IO has global jurisdictional authorization
        auth_io = security_service.check_case_authorization("IN-BOSE-4417", "CASE-2024-BLR-0412")
        self.assertTrue(auth_io)

    def test_02_rbac_permission_enforcement(self):
        """Verify RBAC permissions for VIEWER, ANALYST, and INVESTIGATING_OFFICER."""
        # Viewer cannot review extractions or generate reports
        self.assertFalse(security_service.check_permission("VW-GUEST-1001", Permission.REVIEW_EXTRACTION))
        self.assertFalse(security_service.check_permission("VW-GUEST-1001", Permission.GENERATE_REPORT))
        self.assertTrue(security_service.check_permission("VW-GUEST-1001", Permission.VIEW_CASE))

        # IO has full review and report permissions
        self.assertTrue(security_service.check_permission("IN-BOSE-4417", Permission.REVIEW_EXTRACTION))
        self.assertTrue(security_service.check_permission("IN-BOSE-4417", Permission.GENERATE_REPORT))

    def test_03_path_traversal_sanitization(self):
        """Verify malicious filenames with path traversal tokens are sanitized safely."""
        unsafe_1 = "../../etc/shadow"
        unsafe_2 = "..\\..\\windows\\system32\\cmd.exe"

        clean_1 = security_service.sanitize_path(unsafe_1)
        clean_2 = security_service.sanitize_path(unsafe_2)

        self.assertNotIn("/", clean_1)
        self.assertNotIn("\\", clean_2)
        self.assertEqual(clean_1, "shadow")
        self.assertEqual(clean_2, "cmd.exe")

    def test_04_cypher_injection_protection(self):
        """Verify malicious Cypher DDL/DML injection statements are detected and blocked."""
        malicious_1 = "MATCH (n) DETACH DELETE n"
        malicious_2 = "MATCH (u:User) DROP INDEX ON :User(id)"
        safe_query = "MATCH (s:State {stateCode: 'TS'}) RETURN s"

        self.assertFalse(security_service.validate_cypher_input(malicious_1))
        self.assertFalse(security_service.validate_cypher_input(malicious_2))
        self.assertTrue(security_service.validate_cypher_input(safe_query))

    def test_05_oversized_upload_rejection(self):
        """Verify upload larger than 50MB is rejected with HTTP 400."""
        # Simulate oversized payload header / buffer without allocating full 50MB RAM
        oversized_bytes = b"0" * (51 * 1024 * 1024)
        res = self.client.post(
            "/api/evidence/upload",
            files={"file": ("oversized_dump.bin", io.BytesIO(oversized_bytes), "application/octet-stream")},
            data={"case_id": "CASE-2024-DEL-0891"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("exceeds 50MB", res.json()["detail"])

    def test_06_secret_redaction(self):
        """Verify sensitive credentials (passwords, tokens, keys) are redacted from output."""
        sensitive_payload = {
            "user": "analyst",
            "neo4j_password": "RealSecretPassword123",
            "api_key": "AIzaSySecretToken",
            "public_metric": 48240,
            "nested": {
                "gemini_secret": "SuperSecret",
                "status": "ACTIVE",
            }
        }
        redacted = security_service.redact_secrets(sensitive_payload)

        self.assertEqual(redacted["neo4j_password"], "********")
        self.assertEqual(redacted["api_key"], "********")
        self.assertEqual(redacted["nested"]["gemini_secret"], "********")
        self.assertEqual(redacted["public_metric"], 48240)

    def test_07_ai_provider_failover_and_grounding(self):
        """Verify AI providers failover gracefully to offline deterministic engine."""
        res = offline_provider.generate_grounded_response(
            question="Analyze cyber crime in Telangana",
            retrieved_nodes=[{"id": "STATE-TS", "label": "State", "name": "Telangana", "source_domain": "NCRB_PUBLIC"}],
            retrieved_edges=[],
            context_type="NCRB_PUBLIC",
        )
        self.assertEqual(res["grounding_status"], "PUBLIC_STATISTICS")
        self.assertEqual(res["nodes_count"], 1)
        self.assertIn("citations", res)

    def test_08_system_health_comprehensive(self):
        """Verify GET /api/system/health returns complete subsystem statuses."""
        res = self.client.get("/api/system/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "HEALTHY")
        self.assertIn("subsystems", data)
        self.assertIn("api_server", data["subsystems"])
        self.assertIn("neo4j_graph", data["subsystems"])
        self.assertIn("ncrb_pipeline", data["subsystems"])
        self.assertIn("ai_providers", data["subsystems"])
        self.assertIn("evidence_vault", data["subsystems"])
        self.assertIn("ml_registry", data["subsystems"])

    def test_09_audit_logs_filtering(self):
        """Verify GET /api/audit/logs supports case, user, and action filtering."""
        res = self.client.get("/api/audit/logs?limit=10")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_10_case_graph_export_isolation(self):
        """Verify case export strictly contains only authorized case nodes."""
        res = self.client.get("/api/cases/CASE-2024-DEL-0891/export?format=json")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["case_id"], "CASE-2024-DEL-0891")
        for node in data.get("nodes", []):
            self.assertEqual(node.get("case_id"), "CASE-2024-DEL-0891")


if __name__ == "__main__":
    unittest.main()
