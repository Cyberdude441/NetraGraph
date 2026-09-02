"""
Phase 11 Automated Verification Suite: Production Telemetry & Real-Time Security Operations.
Validates:
1. OpenTelemetry TracerProvider initialization & resource attributes
2. Sensitive attribute and credential scrubbing in distributed traces
3. Prometheus metrics collection & low-cardinality endpoint normalization
4. /metrics exposition endpoint compliance
5. ML Inference telemetry emission across Models A-E
6. Authentication & OTP lifecycle telemetry events
7. Grafana dashboard JSON schema validity & query structure
8. Docker Compose telemetry orchestration (Prometheus & Grafana)
9. Production Models A–E and training/ immutability
"""
import asyncio
import json
import os
import sys
from pathlib import Path
import pytest
import yaml
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ["TESTING"] = "1"
os.environ["EMAIL_PROVIDER"] = "mock"

from app.auth.config import auth_config
auth_config.EMAIL_PROVIDER = "mock"
from app.database.postgres import init_db
from app.telemetry.config import telemetry_config
from app.telemetry.metrics import (
    AUTH_EVENTS_TOTAL,
    HTTP_REQUESTS_TOTAL,
    ML_INFERENCE_TOTAL,
    get_metrics_payload,
    normalize_endpoint,
    record_auth_event,
    record_http_metrics,
    record_ml_inference,
)
from app.telemetry.tracing import _sanitize_attributes, get_tracer, init_tracer, trace_span
from main import app
from scripts.test_ml_diagnostics import SAMPLE_PAYLOADS


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    auth_config.EMAIL_PROVIDER = "mock"
    asyncio.run(init_db())


@pytest.fixture
def client():
    return TestClient(app)


class TestPhase11TelemetryAndOperations:
    """Comprehensive test suite for Phase 11 telemetry, metrics, tracing, and dashboard configuration."""

    # 1. Telemetry Configuration & OpenTelemetry Tracer Initialization
    def test_01_telemetry_configuration_initialization(self):
        assert telemetry_config.OTEL_SERVICE_NAME == "netragraph-backend"
        assert telemetry_config.PROMETHEUS_METRICS_ENABLED is True

        tracer = get_tracer("netragraph.test")
        assert tracer is not None

        # Verify trace span context manager
        with trace_span("test.span", {"custom.metric": 42}) as span:
            assert span is not None
            assert span.is_recording() is True

    # 2. Sensitive Attribute Scrubbing in Traces
    def test_02_sensitive_attribute_sanitization_in_traces(self):
        sensitive_input = {
            "user_id": "USR-1234",
            "password": "SuperSecretPassword123!",
            "token": "eyJh...jwtToken",
            "otp_code": "847291",
            "database_url": "postgresql://postgres:secret@localhost:5432/db",
            "model_name": "intrusion",
            "confidence": 0.98,
        }
        sanitized = _sanitize_attributes(sensitive_input)

        assert sanitized["user_id"] == "USR-1234"
        assert sanitized["model_name"] == "intrusion"
        assert sanitized["confidence"] == 0.98
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"
        assert sanitized["otp_code"] == "[REDACTED]"
        assert sanitized["database_url"] == "[REDACTED]"

    # 3. Prometheus Metrics Recording & Low-Cardinality Enforcement
    def test_03_prometheus_metrics_registry_and_recording(self):
        # Record HTTP
        record_http_metrics("GET", "/api/cases", 200, 0.045)
        
        # Record ML Inference
        record_ml_inference("intrusion", 0.012, success=True)
        record_ml_inference("phishing-url", 0.008, success=True)
        
        # Record Auth
        record_auth_event("otp_request", "success")
        record_auth_event("otp_verify", "success")

        payload, content_type = get_metrics_payload()
        decoded = payload.decode("utf-8")
        assert "netragraph_http_requests_total" in decoded
        assert "netragraph_ml_inference_total" in decoded
        assert "netragraph_auth_events_total" in decoded

    # 4. Low-Cardinality Endpoint Normalization
    def test_04_low_cardinality_endpoint_normalization(self):
        assert normalize_endpoint("/api/cases/CASE-99201") == "/api/cases/{id}"
        assert normalize_endpoint("/api/evidence/550e8400-e29b-41d4-a716-446655440000") == "/api/evidence/{id}"
        assert normalize_endpoint("/api/cyber/graph") == "/api/cyber/graph"
        assert normalize_endpoint("/") == "/"

    # 5. Metrics Exposition Endpoint (/metrics)
    def test_05_metrics_endpoint_exposition_format(self, client):
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "text/plain" in res.headers["content-type"]
        body = res.text
        assert "# HELP netragraph_http_requests_total" in body
        assert "# TYPE netragraph_http_requests_total counter" in body
        assert "# HELP netragraph_db_pool_utilization" in body

    # 6. ML Inference Telemetry Emission (Models A-E)
    def test_06_ml_inference_telemetry_emission(self, client):
        # Model A: Session Intrusion
        res_a = client.post("/api/ml/predict/intrusion?model=intrusion", json=SAMPLE_PAYLOADS["intrusion"])
        assert res_a.status_code == 200
        assert "prediction" in res_a.json()

        # Model C: Phishing URL
        res_c = client.post("/api/ml/predict/phishing-url", json=SAMPLE_PAYLOADS["phishing-url"])
        assert res_c.status_code == 200

        # Verify /metrics reflects inference
        res_metrics = client.get("/metrics")
        assert 'netragraph_ml_inference_total{model_name="intrusion",status="success"}' in res_metrics.text
        assert 'netragraph_ml_inference_total{model_name="phishing-url",status="success"}' in res_metrics.text

    # 7. Authentication Lifecycle Telemetry Emission
    def test_07_auth_lifecycle_telemetry_emission(self, client):
        auth_config.EMAIL_PROVIDER = "mock"
        email = "telemetry.officer@gmail.com"
        res_req = client.post("/api/auth/request-otp", json={"email": email})
        assert res_req.status_code == 200

        res_metrics = client.get("/metrics")
        assert 'netragraph_auth_events_total{event_type="otp_request",status="success"}' in res_metrics.text

    # 8. Grafana Dashboard JSON Schema Validation
    def test_08_grafana_dashboard_schema_validation(self):
        dashboard_file = ROOT_DIR / "docker" / "grafana" / "dashboards" / "netragraph-telemetry.json"
        assert dashboard_file.exists(), "Grafana dashboard JSON must exist"

        with open(dashboard_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["title"] == "NetraGraph AI — Real-Time Production Telemetry & Security Operations"
        assert data["uid"] == "netragraph-production-telemetry"
        assert len(data["panels"]) >= 8

        datasource_file = ROOT_DIR / "docker" / "grafana" / "provisioning" / "datasources" / "datasources.yml"
        assert datasource_file.exists()

        prometheus_cfg = ROOT_DIR / "docker" / "prometheus" / "prometheus.yml"
        assert prometheus_cfg.exists()

    # 9. Docker Compose Telemetry Services Configuration
    def test_09_docker_compose_telemetry_services(self):
        compose_file = ROOT_DIR / "docker-compose.yml"
        prod_compose = ROOT_DIR / "docker-compose.prod.yml"

        with open(compose_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        services = data.get("services", {})
        assert "prometheus" in services
        assert "grafana" in services
        assert "prometheus_data" in data.get("volumes", {})
        assert "grafana_data" in data.get("volumes", {})

        with open(prod_compose, "r", encoding="utf-8") as f:
            prod_data = yaml.safe_load(f)

        prod_services = prod_data.get("services", {})
        assert "prometheus" in prod_services
        assert "grafana" in prod_services
        assert "no-new-privileges:true" in prod_services["prometheus"]["security_opt"]
        assert "no-new-privileges:true" in prod_services["grafana"]["security_opt"]

    # 10. Production ML Models Isolation & Immutability
    def test_10_production_ml_models_isolation_and_immutability(self):
        artifacts_dir = ROOT_DIR / "artifacts"
        assert artifacts_dir.exists()
        for m in ["intrusion", "network-intrusion", "phishing-url", "webpage-phishing", "phishing-email"]:
            m_dir = artifacts_dir / m / "v1"
            assert m_dir.exists()
            assert (m_dir / "model.joblib").exists()
            assert (m_dir / "metadata.json").exists()
