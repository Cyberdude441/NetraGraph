"""Full Regression Test Suite for NetraGraph Core & ML Modules."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient
from main import app
from scripts.test_ml_diagnostics import SAMPLE_PAYLOADS

client = TestClient(app)


def test_regression():
    print("================================================================")
    print("NETRAGRAPH FULL REGRESSION TEST SUITE")
    print("================================================================")

    # 1. Health and Root
    r_root = client.get("/")
    print(f"1. GET / -> Status: {r_root.status_code}")
    assert r_root.status_code == 200

    r_health = client.get("/health")
    print(f"2. GET /health -> Status: {r_health.status_code}")
    assert r_health.status_code == 200

    # 2. Existing Cyber & Graph APIs
    r_cyber_ov = client.get("/api/cyber/overview")
    print(f"3. GET /api/cyber/overview -> Status: {r_cyber_ov.status_code}")
    assert r_cyber_ov.status_code == 200

    r_cyber_graph = client.get("/api/cyber/graph")
    print(f"4. GET /api/cyber/graph -> Status: {r_cyber_graph.status_code}")
    assert r_cyber_graph.status_code == 200

    r_entities = client.get("/api/entities")
    print(f"5. GET /api/entities -> Status: {r_entities.status_code}")
    assert r_entities.status_code == 200

    r_cases = client.get("/api/cases")
    print(f"6. GET /api/cases -> Status: {r_cases.status_code}")
    assert r_cases.status_code == 200

    r_evidence = client.get("/api/evidence")
    print(f"7. GET /api/evidence -> Status: {r_evidence.status_code}")
    assert r_evidence.status_code == 200

    r_analytics = client.get("/api/analytics/metrics")
    print(f"8. GET /api/analytics/metrics -> Status: {r_analytics.status_code}")
    assert r_analytics.status_code == 200

    # 3. ML Models Registry
    r_ml_models = client.get("/api/ml/models")
    print(f"9. GET /api/ml/models -> Status: {r_ml_models.status_code}")
    assert r_ml_models.status_code == 200
    models = r_ml_models.json().get("models", [])
    assert len(models) >= 5, f"Expected 5 models, found {len(models)}"

    # 4. ML Predictions
    # Model A: Session Intrusion
    r_pred_a = client.post("/api/ml/predict/intrusion?model=intrusion", json=SAMPLE_PAYLOADS["intrusion"])
    print(f"10. Model A (Session Intrusion) -> Status: {r_pred_a.status_code} | Pred: {r_pred_a.json().get('prediction')}")
    assert r_pred_a.status_code == 200

    # Model B: Network Intrusion
    r_pred_b = client.post("/api/ml/predict/intrusion?model=network-intrusion", json=SAMPLE_PAYLOADS["network-intrusion"])
    print(f"11. Model B (Network Intrusion) -> Status: {r_pred_b.status_code} | Pred: {r_pred_b.json().get('prediction')}")
    assert r_pred_b.status_code == 200

    # Model C: Phishing URL
    r_pred_c = client.post("/api/ml/predict/phishing-url", json=SAMPLE_PAYLOADS["phishing-url"])
    print(f"12. Model C (Phishing URL) -> Status: {r_pred_c.status_code} | Pred: {r_pred_c.json().get('prediction')}")
    assert r_pred_c.status_code == 200

    # Model D: Web Page Phishing
    r_pred_d = client.post("/api/ml/predict/webpage-phishing", json=SAMPLE_PAYLOADS["webpage-phishing"])
    print(f"13. Model D (Web Page Phishing) -> Status: {r_pred_d.status_code} | Pred: {r_pred_d.json().get('prediction')}")
    assert r_pred_d.status_code == 200

    # Model E: Phishing Email
    r_pred_e = client.post("/api/ml/predict/phishing-email", json=SAMPLE_PAYLOADS["phishing-email"])
    print(f"14. Model E (Phishing Email) -> Status: {r_pred_e.status_code} | Pred: {r_pred_e.json().get('prediction')}")
    assert r_pred_e.status_code == 200

    print("\n================================================================")
    print("ALL 14 REGRESSION TESTS PASSED (100% OK)")
    print("================================================================")


if __name__ == "__main__":
    test_regression()
