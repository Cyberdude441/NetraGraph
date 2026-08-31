"""Automated Test Suite for GraphRAG Grounding & Data Integrity Audit."""
from __future__ import annotations

import unittest
from pathlib import Path
import sys

# Setup backend directory in sys.path
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.neo4j import neo4j_db
from services.graph_builder import graph_builder
from services.graph_ai import graph_reasoning_engine


class TestGraphRAGAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        graph_builder.rebuild_all_graphs()

    def test_01_analyze_cyber_crime_in_odisha(self):
        """TEST 1: Question: 'Analyze cyber crime in Odisha.' -> Grounded answer from NCRB records."""
        res = graph_reasoning_engine.execute_grounded_rag("Analyze cyber crime in Odisha.")
        self.assertEqual(res["grounding_status"], "VERIFIED_GROUNDED")
        self.assertIn("Odisha", res["answer"])
        self.assertIn("NCRB", res["provenance"]["source"])
        self.assertEqual(res["provenance"]["confidence"], "Grounded")
        self.assertGreater(res["graph_nodes_used"], 0)

    def test_02_criminal_kingpin_in_odisha(self):
        """TEST 2: Question: 'Who is the criminal kingpin in Odisha?' -> 'Insufficient verified data.'"""
        res = graph_reasoning_engine.execute_grounded_rag("Who is the criminal kingpin in Odisha?")
        self.assertEqual(res["grounding_status"], "VERIFIED_NEGATIVE")
        self.assertIn("Insufficient verified data", res["answer"])
        self.assertEqual(res["provenance"]["confidence"], "Grounded")

    def test_03_which_bank_account_connected_to_suspect(self):
        """TEST 3: Question: 'Which bank account is connected to this suspect?' -> 'Insufficient verified data.'"""
        res = graph_reasoning_engine.execute_grounded_rag("Which bank account is connected to this suspect?")
        self.assertEqual(res["grounding_status"], "VERIFIED_NEGATIVE")
        self.assertIn("Insufficient verified data", res["answer"])

    def test_04_nonexistent_statistic(self):
        """TEST 4: Ask for a statistic that does not exist -> 'No verified data available.'"""
        res = graph_reasoning_engine.execute_grounded_rag("What was the crypto hacking rate in 1980 by alien syndicates?")
        self.assertEqual(res["grounding_status"], "NOT_AVAILABLE")
        self.assertIn("No verified data available", res["answer"])

    def test_05_actual_graph_record_query(self):
        """TEST 5: Ask for information contained in an actual graph record -> Grounded answer with provenance."""
        res = graph_reasoning_engine.execute_grounded_rag("Show evidence and details for CASE-2024-DEL-0891 regarding Amit Joshi.")
        self.assertEqual(res["grounding_status"], "VERIFIED_GROUNDED")
        self.assertIn("Amit Joshi", res["answer"])
        self.assertIn("CASE-2024-DEL-0891", res["answer"])
        self.assertIn("Case (CASE-2024-DEL-0891)", res["provenance"]["graph_path"])
        self.assertEqual(res["provenance"]["confidence"], "Grounded")

    def test_06_internal_query_audit_logging(self):
        """Verify internal query audit logger recorded all 5 queries with required fields."""
        logs = graph_reasoning_engine.get_audit_logs()
        self.assertGreaterEqual(len(logs), 5)
        for log in logs:
            self.assertIn("query_id", log)
            self.assertIn("timestamp", log)
            self.assertIn("user_question", log)
            self.assertIn("generated_query", log)
            self.assertIn("retrieved_node_count", log)
            self.assertIn("retrieved_relationship_count", log)
            self.assertIn("source_count", log)
            self.assertIn("provenance_status", log)
            self.assertIn("answer_type", log)


if __name__ == "__main__":
    unittest.main()
