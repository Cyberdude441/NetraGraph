"""Direct FastAPI Endpoint Integration Test for ML router."""
from __future__ import annotations

import json
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


def test_all_endpoints():
    print("================================================================")
    print("FASTAPI BACKEND ML ENDPOINTS INTEGRATION TEST")
    print("================================================================")

    # 1. GET /api/ml/models
    res = client.get("/api/ml/models")
    print(f"\n1. GET /api/ml/models -> Status: {res.status_code}")
    models_data = res.json()
    model_list = models_data.get("models", [])
    print(f"   Discovered {len(model_list)} registered models:")
    for m in model_list:
        print(f"   - {m['model_name']} ({m['version']}) | Active: {m.get('active')} | Task: {m.get('task_type')}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert len(model_list) >= 5, f"Expected at least 5 models, found {len(model_list)}"

    # 2. Activate all v1 versions to ensure each domain has active model
    for m in model_list:
        act_res = client.post(f"/api/ml/models/{m['model_name']}/{m['version']}/activate")
        print(f"   Activate {m['model_name']}/{m['version']} -> Status: {act_res.status_code}")

    # 3. Test POST /api/ml/predict/intrusion (Model A: Session Intrusion)
    res_a = client.post("/api/ml/predict/intrusion?model=intrusion", json=SAMPLE_PAYLOADS["intrusion"])
    print(f"\n2. POST /api/ml/predict/intrusion (Model A) -> Status: {res_a.status_code}")
    print(f"   Response: {json.dumps(res_a.json(), indent=2)}")
    assert res_a.status_code == 200, f"Model A failed: {res_a.text}"
    assert "prediction" in res_a.json()
    assert res_a.json()["model"] == "intrusion"

    # 4. Test POST /api/ml/predict/intrusion (Model B: Network Intrusion)
    res_b = client.post("/api/ml/predict/intrusion?model=network-intrusion", json=SAMPLE_PAYLOADS["network-intrusion"])
    print(f"\n3. POST /api/ml/predict/intrusion (Model B) -> Status: {res_b.status_code}")
    print(f"   Response: {json.dumps(res_b.json(), indent=2)}")
    assert res_b.status_code == 200, f"Model B failed: {res_b.text}"
    assert "prediction" in res_b.json()
    assert res_b.json()["model"] == "network-intrusion"

    # 5. Test POST /api/ml/predict/phishing-url (Model C: PhiUSIIL URL)
    res_c = client.post("/api/ml/predict/phishing-url", json=SAMPLE_PAYLOADS["phishing-url"])
    print(f"\n4. POST /api/ml/predict/phishing-url (Model C) -> Status: {res_c.status_code}")
    print(f"   Response: {json.dumps(res_c.json(), indent=2)}")
    assert res_c.status_code == 200, f"Model C failed: {res_c.text}"
    assert "prediction" in res_c.json()

    # 6. Test POST /api/ml/predict/webpage-phishing (Model D: Web Page Phishing)
    res_d = client.post("/api/ml/predict/webpage-phishing", json=SAMPLE_PAYLOADS["webpage-phishing"])
    print(f"\n5. POST /api/ml/predict/webpage-phishing (Model D) -> Status: {res_d.status_code}")
    print(f"   Response: {json.dumps(res_d.json(), indent=2)}")
    assert res_d.status_code == 200, f"Model D failed: {res_d.text}"
    assert "prediction" in res_d.json()

    # 7. Test POST /api/ml/predict/phishing-email (Model E: Phishing Email)
    res_e = client.post("/api/ml/predict/phishing-email", json=SAMPLE_PAYLOADS["phishing-email"])
    print(f"\n6. POST /api/ml/predict/phishing-email (Model E) -> Status: {res_e.status_code}")
    print(f"   Response: {json.dumps(res_e.json(), indent=2)}")
    assert res_e.status_code == 200, f"Model E failed: {res_e.text}"
    assert "prediction" in res_e.json()

    print("\n================================================================")
    print("ALL FASTAPI ML INFERENCE ENDPOINTS PASSED SUCCESSFULLY (200 OK)")
    print("================================================================")


if __name__ == "__main__":
    test_all_endpoints()
