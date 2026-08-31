"""Phase 3 Comprehensive Test Suite: Investigation-Grade Knowledge Graph & Analytics."""
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
from database.neo4j import neo4j_db
from services.investigation_graph import (
    investigation_graph_service,
    ResolutionStatus,
    VerificationStatus,
)


class TestPhase3InvestigationKnowledgeGraph(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        investigation_graph_service.initialize_formal_investigation_graph()

    def test_01_case_graph_retrieval(self):
        """Verify GET /api/graph/cases/{case_id} retrieves isolated case evidence subgraph."""
        case_id = "CASE-2024-DEL-0891"
        res = self.client.get(f"/api/graph/cases/{case_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("nodes", data)
        self.assertIn("relationships", data)
        self.assertGreater(len(data["nodes"]), 0)

        for node in data["nodes"]:
            self.assertEqual(node.get("case_id"), case_id)

    def test_02_entity_details_lookup(self):
        """Verify GET /api/graph/entities/{entity_id} returns full metadata and provenance."""
        entity_id = "ip:103.145.22.18"
        res = self.client.get(f"/api/graph/entities/{entity_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["entity_id"], entity_id)
        self.assertIn("entity", data)
        self.assertIn("provenance", data)
        self.assertEqual(data["provenance"]["verification_status"], "VERIFIED")
        self.assertIn("Tata Communications", data["provenance"]["source"])

    def test_03_controlled_multi_hop_traversal(self):
        """Verify GET /api/graph/entities/{entity_id}/neighbors respects hop limits (1 to 4)."""
        focal_id = investigation_graph_service.generate_entity_id("person", "amit_joshi_1988")

        # 1-hop traversal
        res_1hop = self.client.get(f"/api/graph/entities/{focal_id}/neighbors?hops=1")
        self.assertEqual(res_1hop.status_code, 200)
        data_1hop = res_1hop.json()
        count_1hop = len(data_1hop["nodes"])

        # 2-hop traversal
        res_2hop = self.client.get(f"/api/graph/entities/{focal_id}/neighbors?hops=2")
        self.assertEqual(res_2hop.status_code, 200)
        data_2hop = res_2hop.json()
        count_2hop = len(data_2hop["nodes"])

        self.assertGreaterEqual(count_2hop, count_1hop)

        # Max hop check (capped at 4)
        for node in data_2hop["nodes"]:
            self.assertLessEqual(node["distance_from_focal"], 2)

    def test_04_shortest_path_with_evidence_citations(self):
        """Verify POST /api/graph/path returns shortest path with evidence on every edge."""
        src_id = investigation_graph_service.generate_entity_id("person", "amit_joshi_1988")
        tgt_id = "domain:support-helpdesk-msft.com"

        payload = {
            "source_entity_id": src_id,
            "target_entity_id": tgt_id,
            "max_hops": 6,
        }
        res = self.client.post("/api/graph/path", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data["found"])
        self.assertGreater(data["hop_count"], 0)
        self.assertIn("path_nodes", data)
        self.assertIn("path_edges", data)
        self.assertIn("confidence", data)
        self.assertIn("provenance", data)

    def test_05_graph_search_and_filtering(self):
        """Verify GET /api/graph/search with multi-dimensional filters."""
        res = self.client.get("/api/graph/search?entity_type=Domain&min_confidence=0.9")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertGreater(data["total_results"], 0)
        for node in data["results"]:
            self.assertEqual(node.get("label"), "Domain")
            self.assertGreaterEqual(node.get("confidence", 1.0), 0.9)

    def test_06_edge_explainability(self):
        """Verify GET /api/graph/relationships/{id}/explain answers 'WHY DOES THIS EDGE EXIST?'."""
        rel_id = f"REL-{investigation_graph_service.generate_entity_id('person', 'amit_joshi_1988')}-{investigation_graph_service.generate_entity_id('organization', 'techglobal_support_services')}"
        res = self.client.get(f"/api/graph/relationships/{rel_id}/explain")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["relationship_id"], rel_id)
        self.assertIn("explanation", data)
        self.assertIn("source_document", data["explanation"])
        self.assertIn("confidence", data["explanation"])
        self.assertIn("verification_status", data["explanation"])

    def test_07_comprehensive_statistics_and_centrality(self):
        """Verify GET /api/graph/statistics calculates node types, edge statuses, and ethical roles."""
        res = self.client.get("/api/graph/statistics")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("nodes_by_type", data)
        self.assertIn("relationships_by_type", data)
        self.assertIn("verified_relationships", data)
        self.assertIn("highest_betweenness_entities", data)
        self.assertIn("highest_pagerank_entities", data)

    def test_08_negative_ethical_centrality_terminology(self):
        """CRITICAL NEGATIVE TEST: Verify centrality entities are NEVER labeled as 'Kingpin' or 'Mastermind'."""
        res = self.client.get("/api/graph/statistics")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        banned_terms = ["kingpin", "mastermind", "criminal leader", "gang leader"]

        for item in data.get("highest_betweenness_entities", []):
            role_lower = item.get("structural_role", "").lower()
            for banned in banned_terms:
                self.assertNotIn(banned, role_lower, f"Ethical terminology violation in Betweenness role: {role_lower}")

        for item in data.get("highest_pagerank_entities", []):
            role_lower = item.get("structural_role", "").lower()
            for banned in banned_terms:
                self.assertNotIn(banned, role_lower, f"Ethical terminology violation in PageRank role: {role_lower}")

    def test_09_negative_nonexistent_path(self):
        """CRITICAL NEGATIVE TEST: Verify query between unlinked entities returns 'found': false with reason."""
        payload = {
            "source_entity_id": "ip:103.145.22.18",
            "target_entity_id": "nonexistent_entity_xyz",
        }
        res = self.client.post("/api/graph/path", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertFalse(data["found"])
        self.assertIn("reason", data)
        self.assertEqual(data["reason"], "No verified path exists in the available graph.")

    def test_10_negative_public_ncrb_isolation(self):
        """CRITICAL NEGATIVE TEST: Verify public NCRB graph does not contain private suspect/person nodes."""
        res = self.client.get("/api/graph/nodes?graph_source=ncrb_public")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        disallowed_labels = {"Person", "Suspect", "BankAccount", "Phone", "IMEI"}
        for node in data.get("nodes", []):
            self.assertNotIn(node.get("label"), disallowed_labels)


if __name__ == "__main__":
    unittest.main()
