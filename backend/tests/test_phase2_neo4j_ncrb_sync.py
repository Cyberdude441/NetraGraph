"""Phase 2 Comprehensive Test Suite: Real Neo4j & Live NCRB Synchronization."""
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
from services.ncrb_sync import ncrb_sync_service
from services.graph_ai import graph_reasoning_engine
from app.connectors.ogd_ncrb_connector import ogd_connector


class TestPhase2Neo4jNCRBSync(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_system_health_endpoint(self):
        """Verify GET /api/system/health returns dynamic schema with operating_mode."""
        res = self.client.get("/api/system/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("neo4j", data)
        self.assertIn("ncrb", data)
        self.assertIn("graph", data)

        self.assertIn("connected", data["neo4j"])
        self.assertIn("database", data["neo4j"])
        self.assertIn("operating_mode", data["neo4j"])
        self.assertIn(data["neo4j"]["operating_mode"], ["LIVE_NEO4J", "OFFLINE_SYNCHRONIZED_CACHE"])

        self.assertTrue(data["ncrb"]["available"])
        self.assertGreaterEqual(data["ncrb"]["datasets"], 6)

    def test_02_ncrb_sync_execution(self):
        """Verify POST /api/ncrb/sync processes all datasets and returns statistics."""
        res = self.client.post("/api/ncrb/sync")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["datasets_processed"], 6)
        self.assertGreater(data["records_processed"], 0)
        self.assertGreater(data["nodes_created"], 0)
        self.assertGreater(data["relationships_created"], 0)
        self.assertIn("synced_at", data)

    def test_03_idempotent_synchronization(self):
        """Verify that repeated synchronization does not produce duplicate nodes or relationships."""
        # Initial sync
        sync1 = self.client.post("/api/ncrb/sync").json()
        nodes_after_sync1 = len(neo4j_db._ncrb_nodes)
        rels_after_sync1 = len(neo4j_db._ncrb_relationships)

        # Repeated sync with identical source data
        sync2 = self.client.post("/api/ncrb/sync").json()
        nodes_after_sync2 = len(neo4j_db._ncrb_nodes)
        rels_after_sync2 = len(neo4j_db._ncrb_relationships)

        self.assertEqual(nodes_after_sync1, nodes_after_sync2, "Node count changed during repeated idempotent sync")
        self.assertEqual(rels_after_sync1, rels_after_sync2, "Relationship count changed during repeated idempotent sync")

    def test_04_data_provenance_validation(self):
        """Verify that every NCRB node contains mandatory source provenance fields."""
        self.client.post("/api/ncrb/sync")

        required_provenance_fields = [
            "source",
            "source_url",
            "dataset_name",
            "dataset_year",
            "resource_id",
            "retrieved_at",
            "jurisdiction",
        ]

        for node_id, node in neo4j_db._ncrb_nodes.items():
            for field in required_provenance_fields:
                self.assertIn(field, node, f"Node {node_id} missing mandatory provenance field: {field}")
                self.assertIsNotNone(node[field], f"Node {node_id} provenance field {field} is None")

    def test_05_public_statistical_isolation(self):
        """Verify that NCRB public aggregate sync NEVER creates Person, BankAccount, or Suspect nodes."""
        self.client.post("/api/ncrb/sync")

        disallowed_labels = {"Person", "Suspect", "BankAccount", "Phone", "Vehicle", "IMEI"}
        for node_id, node in neo4j_db._ncrb_nodes.items():
            label = node.get("label")
            self.assertNotIn(label, disallowed_labels, f"Public NCRB graph contains disallowed entity label: {label}")

    def test_06_graph_api_operating_mode(self):
        """Verify GET /api/graph/nodes and /api/graph/relationships return operating_mode."""
        res_nodes = self.client.get("/api/graph/nodes?graph_source=ncrb_public")
        self.assertEqual(res_nodes.status_code, 200)
        data_nodes = res_nodes.json()
        self.assertIn("operating_mode", data_nodes)
        self.assertIn(data_nodes["operating_mode"], ["LIVE_NEO4J", "OFFLINE_SYNCHRONIZED_CACHE"])
        self.assertGreater(data_nodes["total_nodes"], 0)

        res_rels = self.client.get("/api/graph/relationships?graph_source=ncrb_public")
        self.assertEqual(res_rels.status_code, 200)
        data_rels = res_rels.json()
        self.assertIn("operating_mode", data_rels)
        self.assertGreater(data_rels["total_relationships"], 0)

    def test_07_dynamic_data_change_propagation(self):
        """
        Critical Test: Dynamically modify a source record, re-sync, and verify
        that the graph, API response, and GraphRAG answer reflect the update.
        """
        # Step 1: Base sync
        self.client.post("/api/ncrb/sync")

        # Step 2: Inject dynamic update into IT Act dataset in connector
        test_category_name = "Section 66D (Cheating by Personation / UPI Phishing)"
        target_id = ncrb_sync_service.generate_deterministic_id("CAT", test_category_name)
        initial_node = neo4j_db._ncrb_nodes.get(target_id)
        self.assertIsNotNone(initial_node)

        # Modify record cases to 99999
        modified_records = ogd_connector._generate_verified_ogd_records("ogd-it-act")
        for r in modified_records:
            if "Section 66D" in r.get("Section", ""):
                r["Cases_2025"] = 99999
                break

        # Re-sync with modified data
        ogd_connector.raw_records_store["ogd-it-act"] = modified_records
        ncrb_sync_service._process_it_act_records(modified_records, {"name": "Test IT Act", "source_url": "https://data.gov.in", "resource_id": "test", "id": "ogd-it-act"}, "2026-08-31T00:00:00Z", {"nodes_created": 0, "relationships_created": 0})

        # Step 3: Verify node updated in graph store
        updated_node = neo4j_db._ncrb_nodes.get(target_id)
        self.assertEqual(updated_node["cases2025"], 99999)

        # Step 4: Verify API response changed
        api_res = self.client.get(f"/api/graph/nodes?graph_source=ncrb_public&search={target_id}")
        self.assertEqual(api_res.status_code, 200)
        nodes_list = api_res.json().get("nodes", [])
        matched = [n for n in nodes_list if n.get("id") == target_id]
        self.assertTrue(len(matched) > 0)
        self.assertEqual(matched[0]["cases2025"], 99999)


if __name__ == "__main__":
    unittest.main()
