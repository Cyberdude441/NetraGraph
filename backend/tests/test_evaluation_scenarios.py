"""Automated Evaluation Runner for 10 Controlled Investigation Scenarios."""
from __future__ import annotations

import json
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
from services.evidence_intelligence_service import evidence_intelligence_service
from services.graph_ai import forensic_graphrag


class TestEvaluationScenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        scenario_file = TEST_DIR / "data" / "evaluation_scenarios.json"
        with open(scenario_file, "r", encoding="utf-8") as f:
            cls.scenarios_data = json.load(f)["scenarios"]

    def test_all_10_scenarios_execution(self):
        """Executes all 10 controlled scenarios and verifies extraction, resolution, and GraphRAG accuracy."""
        for sc in self.scenarios_data:
            s_id = sc["scenario_id"]
            case_id = sc["case_id"]
            ev_input = sc["evidence_input"]

            # 1. Extraction Test
            staged = evidence_intelligence_service.extract_entities_and_relationships_from_text(
                text=ev_input["content"],
                evidence_id=f"EV-{s_id[:8]}",
                case_id=case_id,
                source_filename=ev_input["filename"],
            )

            for exp_ent in sc.get("expected_entities", []):
                matching = [
                    e for e in staged
                    if e["entity_type"] == exp_ent["type"] and exp_ent["value"].lower() in e["value"].lower()
                ]
                self.assertGreater(
                    len(matching), 0,
                    f"Scenario '{s_id}': Failed to extract entity {exp_ent['type']} '{exp_ent['value']}'"
                )
                self.assertEqual(
                    matching[0]["resolution_status"], exp_ent["resolution"],
                    f"Scenario '{s_id}': Resolution mismatch for '{exp_ent['value']}'"
                )

            # Accept staged candidate extractions to commit them to the investigation graph
            for item in staged:
                ext_id = item["extraction_id"]
                if item["entity_type"] != "Person":  # Keep person uncorroborated to test unresolved logic
                    evidence_intelligence_service.review_staged_extraction(ext_id, "ACCEPT")

            # 2. GraphRAG Grounding & Answer Test
            rag_res = forensic_graphrag.query(
                question=sc["graphrag_question"],
                provider="gemini",
                case_id=case_id if case_id != "NCRB_PUBLIC" else None,
            )

            # Assert expected keywords are present in response
            for kw in sc.get("expected_answer_keywords", []):
                self.assertIn(
                    kw.lower(), rag_res["answer"].lower(),
                    f"Scenario '{s_id}': Keyword '{kw}' missing from GraphRAG answer: {rag_res['answer']}"
                )


if __name__ == "__main__":
    unittest.main()
