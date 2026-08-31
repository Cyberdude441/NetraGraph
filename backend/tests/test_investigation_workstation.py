"""Comprehensive Verification Test Suite for NetraGraph AI Investigation Workstation."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
import sys

TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.neo4j import neo4j_db
from app.database.db import db
from services.graph_algorithms import graph_algorithms
from services.graph_ai import graph_reasoning_engine
from services.graph_builder import graph_builder
from services.report_generator import report_generator
from app.api.ml_router import _predict


class TestNetraGraphWorkstation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Rebuild fresh synchronized graphs
        graph_builder.rebuild_all_graphs()

    def test_01_neo4j_health_and_sync(self):
        health = neo4j_db.get_health()
        self.assertIn("status", health)
        self.assertIn(health["status"], ["CONNECTED", "SYNCHRONIZED_MEMORY_FALLBACK"])
        self.assertIn("graph_summary", health)
        self.assertGreater(health["graph_summary"]["total_nodes"], 0)
        self.assertGreater(health["graph_summary"]["total_relationships"], 0)

    def test_02_strict_public_ncrb_provenance_isolation(self):
        ncrb_res = neo4j_db.query_ncrb_graph()
        nodes = ncrb_res.get("nodes", [])
        self.assertGreater(len(nodes), 0)

        for n in nodes:
            # Must strictly contain public provenance
            self.assertEqual(n.get("graph_source"), "NCRB_PUBLIC_OGD")
            self.assertIn("source", n)
            # Must NEVER contain person or suspect labels in public NCRB graph
            self.assertNotIn(n.get("label"), ["Person", "Suspect", "BankAccount", "Device"])

    def test_03_real_graph_centrality_algorithms(self):
        stats = graph_algorithms.get_graph_stats("investigation_evidence")
        self.assertGreater(stats["total_nodes"], 0)
        self.assertGreater(stats["total_relationships"], 0)

        centralities = graph_algorithms.calculate_centralities("investigation_evidence", limit=5)
        self.assertIn("metrics", centralities)
        self.assertIn("top_betweenness_bridges", centralities)
        self.assertIn("top_pagerank_influencers", centralities)
        self.assertIn("top_degree_hubs", centralities)

        # Check values are normalized floats
        for node_id, metric in centralities["metrics"].items():
            self.assertGreaterEqual(metric["degree_centrality"], 0.0)
            self.assertGreaterEqual(metric["betweenness_centrality"], 0.0)
            self.assertGreaterEqual(metric["pagerank"], 0.0)

    def test_04_real_community_detection(self):
        comm_res = graph_algorithms.detect_communities("investigation_evidence")
        self.assertIn("total_communities", comm_res)
        self.assertGreater(comm_res["total_communities"], 0)
        self.assertIn("node_community_map", comm_res)
        self.assertIn("communities", comm_res)

    def test_05_real_shortest_path(self):
        # Find path between Amit Joshi (PER-05) and Escrow Account (FIN-03)
        path_res = graph_algorithms.find_shortest_path("PER-05", "FIN-03", "investigation_evidence")
        self.assertTrue(path_res["found"])
        self.assertEqual(path_res["path"], ["PER-05", "ORG-03", "FIN-03"])
        self.assertEqual(path_res["hop_count"], 2)
        self.assertEqual(len(path_res["path_nodes"]), 3)
        self.assertEqual(len(path_res["path_edges"]), 2)

    def test_06_strict_graphrag_zero_hallucination_guardrail(self):
        # Query for criminal gangs in public NCRB data without case context
        res = graph_reasoning_engine.execute_grounded_rag("Who are the criminal gangs operating cyber fraud in Telangana?")
        self.assertEqual(res["grounding_status"], "VERIFIED_NEGATIVE")
        self.assertIn("Insufficient verified data", res["answer"])
        self.assertIn("provenance", res)
        self.assertEqual(res["provenance"]["confidence"], "Grounded")

    def test_07_strict_graphrag_case_evidence_grounding(self):
        # Query for authorized Case evidence
        res = graph_reasoning_engine.execute_grounded_rag("What evidence is recorded for CASE-2024-DEL-0891 regarding Amit Joshi?")
        self.assertEqual(res["grounding_status"], "VERIFIED_GROUNDED")
        self.assertIn("Amit Joshi", res["answer"])
        self.assertIn("CASE-2024-DEL-0891", res["answer"])
        self.assertIn("provenance", res)
        self.assertEqual(res["provenance"]["confidence"], "Grounded")

    def test_08_ml_inference_to_knowledge_graph_lineage(self):
        # Execute ML inference for Model B (network-intrusion)
        test_payload = {
            "duration": 0, "protocol_type": "tcp", "service": "http", "flag": "SF",
            "src_bytes": 215, "dst_bytes": 450, "land": 0, "wrong_fragment": 0,
            "urgent": 0, "hot": 0, "num_failed_logins": 0, "logged_in": 1,
            "num_compromised": 0, "root_shell": 0, "su_attempted": 0, "num_root": 0,
            "num_file_creations": 0, "num_shells": 0, "num_access_files": 0,
            "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0,
            "count": 1, "srv_count": 1, "serror_rate": 0.0, "srv_serror_rate": 0.0,
            "rerror_rate": 0.0, "srv_rerror_rate": 0.0, "same_srv_rate": 1.0,
            "diff_srv_rate": 0.0, "srv_diff_host_rate": 0.0, "dst_host_count": 1,
            "dst_host_srv_count": 1, "dst_host_same_srv_rate": 1.0,
            "dst_host_diff_srv_rate": 0.0, "dst_host_same_src_port_rate": 1.0,
            "dst_host_srv_diff_host_rate": 0.0, "dst_host_serror_rate": 0.0,
            "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 0.0,
            "dst_host_srv_rerror_rate": 0.0,
            "model_name": "network-intrusion",
            "case_id": "CASE-2024-DEL-0891",
        }
        pred_res = _predict("intrusion", test_payload, model_name="network-intrusion")
        self.assertIn("prediction_id", pred_res)
        self.assertIn("prediction", pred_res)
        self.assertEqual(pred_res["assessment_type"], "MODEL_PREDICTION")
        self.assertTrue(pred_res["graph_lineage_recorded"])

        # Verify node was stored in Knowledge Graph
        pred_node = neo4j_db.get_node(pred_res["prediction_id"])
        self.assertIsNotNone(pred_node)
        self.assertEqual(pred_node["label"], "MLPrediction")
        self.assertEqual(pred_node["assessment_type"], "MODEL_PREDICTION")

    def test_09_evidence_case_report_section_65b_linkage(self):
        # Generate forensic case report for CASE-2024-DEL-0891
        report = report_generator.generate_case_investigation_report(
            case_id="CASE-2024-DEL-0891",
            officer_id="IN-BOSE-4417",
            officer_designation="Inspector of Police (Cyber Cell)",
        )
        self.assertEqual(report["case_id"], "CASE-2024-DEL-0891")
        self.assertIn("section_65b_certificate", report)
        self.assertEqual(report["section_65b_certificate"]["statutory_act"], "Section 65B, Indian Evidence Act / Section 63 BSA")
        self.assertIn("master_integrity_hash", report["section_65b_certificate"])
        self.assertGreater(len(report["section_65b_certificate"]["master_integrity_hash"]), 32)
        self.assertIn("knowledge_graph_findings", report)
        self.assertIn("machine_learning_telemetry", report)


if __name__ == "__main__":
    unittest.main()
