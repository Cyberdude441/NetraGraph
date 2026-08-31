"""Automated Test for System Data Integrity Endpoint."""
from __future__ import annotations

import unittest
from pathlib import Path
import sys
from fastapi.testclient import TestClient

# Setup backend directory in sys.path
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app


class TestSystemDataIntegrity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_data_integrity_endpoint(self):
        response = self.client.get("/api/system/data-integrity")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check required fields
        self.assertIn("neo4j", data)
        self.assertIn("ncrb", data)
        self.assertIn("investigation", data)
        self.assertIn("synthetic_data_detected", data)

        # Check neo4j block
        self.assertIn("connected", data["neo4j"])
        self.assertIn("nodes", data["neo4j"])
        self.assertIn("relationships", data["neo4j"])
        self.assertGreater(data["neo4j"]["nodes"], 0)

        # Check ncrb block
        self.assertIn("datasets", data["ncrb"])
        self.assertIn("records", data["ncrb"])

        # Check investigation block
        self.assertIn("cases", data["investigation"])
        self.assertIn("evidence", data["investigation"])
        self.assertIn("entities", data["investigation"])

        # Check synthetic data detection is false
        self.assertFalse(data["synthetic_data_detected"])


if __name__ == "__main__":
    unittest.main()
