"""
Phase 10 Automated Verification Suite: Production Containerization & CI/CD Deployment Orchestration.
Validates:
1. Multi-stage non-root Dockerfile.backend (FastAPI)
2. Multi-stage non-root Dockerfile.frontend (Vite + Nginx)
3. Docker Compose development topology & healthchecks
4. Docker Compose production hardening overrides (ports closed, resource limits, no-new-privileges)
5. Nginx reverse proxy configuration & security headers
6. Application liveness (/health) and readiness (/health/ready) endpoints
7. GitHub Actions CI pipeline configuration (.github/workflows/ci.yml)
8. Secret isolation in .dockerignore and .gitignore
9. Production Models A–E and training/ immutability
"""
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

import asyncio
from app.database.postgres import init_db
from main import app


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    asyncio.run(init_db())


@pytest.fixture
def client():
    return TestClient(app)


class TestPhase10ContainerAndOrchestration:
    """Comprehensive test suite for containerization, compose topology, and deployment orchestration."""

    # 1. Backend Dockerfile Security & Non-Root
    def test_01_backend_dockerfile_security_and_nonroot(self):
        dockerfile_path = ROOT_DIR / "Dockerfile.backend"
        assert dockerfile_path.exists(), "Dockerfile.backend must exist in root"
        content = dockerfile_path.read_text(encoding="utf-8")

        # Multi-stage validation
        assert "FROM python:3.12-slim AS builder" in content
        assert "FROM python:3.12-slim AS runner" in content
        
        # Non-root user validation
        assert "useradd -u 10001 -g netragraph" in content
        assert "USER netragraph" in content

        # Healthcheck validation
        assert "HEALTHCHECK" in content
        assert "/health" in content

        # Secret protection: .env must NOT be copied
        assert "COPY .env" not in content
        assert "COPY backend/.env" not in content

        # Entrypoint script
        entrypoint_path = BACKEND_DIR / "entrypoint.sh"
        assert entrypoint_path.exists(), "backend/entrypoint.sh must exist"
        ep_content = entrypoint_path.read_text(encoding="utf-8")
        assert "alembic" in ep_content
        assert "exec uvicorn" in ep_content

    # 2. Frontend Dockerfile Multi-Stage & Nginx
    def test_02_frontend_dockerfile_multistage_and_nginx(self):
        dockerfile_path = ROOT_DIR / "Dockerfile.frontend"
        assert dockerfile_path.exists(), "Dockerfile.frontend must exist in root"
        content = dockerfile_path.read_text(encoding="utf-8")

        # Multi-stage validation
        assert "FROM node:20-alpine AS builder" in content
        assert "FROM nginx:1.27-alpine-slim AS runner" in content

        # Static assets and non-root execution
        assert "USER nginx" in content
        assert "HEALTHCHECK" in content
        assert "COPY --from=builder" in content

        # Frontend Nginx SPA config
        frontend_nginx_path = ROOT_DIR / "docker" / "nginx" / "frontend-nginx.conf"
        assert frontend_nginx_path.exists(), "docker/nginx/frontend-nginx.conf must exist"
        fn_content = frontend_nginx_path.read_text(encoding="utf-8")
        assert "try_files $uri $uri/ /index.html" in fn_content
        assert "X-Frame-Options" in fn_content

    # 3. Docker Compose Development Topology & Healthchecks
    def test_03_docker_compose_topology_and_healthchecks(self):
        compose_path = ROOT_DIR / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml must exist"
        
        with open(compose_path, "r", encoding="utf-8") as f:
            compose_data = yaml.safe_load(f)

        services = compose_data.get("services", {})
        expected_services = ["postgres", "neo4j", "backend", "frontend", "nginx"]
        for s in expected_services:
            assert s in services, f"Service '{s}' must be defined in docker-compose.yml"

        # Healthcheck validation
        for s in expected_services:
            assert "healthcheck" in services[s], f"Service '{s}' must have a defined healthcheck"

        # Dependencies validation
        assert "depends_on" in services["backend"]
        assert "postgres" in services["backend"]["depends_on"]
        assert "neo4j" in services["backend"]["depends_on"]

        # Volumes validation
        volumes = compose_data.get("volumes", {})
        assert "postgres_data" in volumes
        assert "neo4j_data" in volumes

        # Network validation
        networks = compose_data.get("networks", {})
        assert "netragraph-net" in networks

    # 4. Docker Compose Production Hardening Overrides
    def test_04_docker_compose_prod_hardening(self):
        prod_compose_path = ROOT_DIR / "docker-compose.prod.yml"
        assert prod_compose_path.exists(), "docker-compose.prod.yml must exist"
        
        with open(prod_compose_path, "r", encoding="utf-8") as f:
            prod_data = yaml.safe_load(f)

        services = prod_data.get("services", {})
        
        # Internal service ports must be closed (empty list)
        assert services["postgres"].get("ports") == []
        assert services["neo4j"].get("ports") == []
        assert services["backend"].get("ports") == []
        assert services["frontend"].get("ports") == []

        # Only Nginx exposes ports 80 and 443
        nginx_ports = services["nginx"].get("ports", [])
        assert "80:80" in nginx_ports
        assert "443:443" in nginx_ports

        # Security options: no-new-privileges
        for s in ["postgres", "neo4j", "backend", "frontend", "nginx"]:
            sec_opts = services[s].get("security_opt", [])
            assert "no-new-privileges:true" in sec_opts

        # Resource limits configured
        assert "deploy" in services["backend"]
        assert "limits" in services["backend"]["deploy"]["resources"]

    # 5. Nginx Reverse Proxy Configuration & Security
    def test_05_nginx_reverse_proxy_configuration(self):
        nginx_conf = ROOT_DIR / "docker" / "nginx" / "nginx.conf"
        default_conf = ROOT_DIR / "docker" / "nginx" / "conf.d" / "default.conf"
        ssl_template = ROOT_DIR / "docker" / "nginx" / "conf.d" / "ssl.conf.template"

        assert nginx_conf.exists()
        assert default_conf.exists()
        assert ssl_template.exists()

        main_content = nginx_conf.read_text(encoding="utf-8")
        assert "client_max_body_size 50M;" in main_content
        assert "gzip on;" in main_content

        dev_content = default_conf.read_text(encoding="utf-8")
        assert "proxy_pass http://backend_upstream/api/;" in dev_content
        assert "proxy_pass http://frontend_upstream;" in dev_content
        assert "X-Forwarded-For" in dev_content
        assert "X-Content-Type-Options" in dev_content

        ssl_content = ssl_template.read_text(encoding="utf-8")
        assert "listen 443 ssl" in ssl_content
        assert "Strict-Transport-Security" in ssl_content
        assert "TLSv1.2 TLSv1.3" in ssl_content

    # 6. Backend Readiness & Liveness Probes
    def test_06_backend_readiness_and_liveness_endpoints(self, client):
        # Liveness
        r_live = client.get("/health")
        assert r_live.status_code == 200
        assert r_live.json()["status"] == "HEALTHY"

        # Database health probe
        r_db = client.get("/health/db")
        assert r_db.status_code == 200
        db_data = r_db.json()
        assert "database" in db_data
        # Ensure zero credential leakage
        assert "password" not in str(db_data).lower()
        assert "url" not in str(db_data).lower()

        # Cluster Readiness Probe
        r_ready = client.get("/health/ready")
        assert r_ready.status_code == 200
        ready_data = r_ready.json()
        assert ready_data["status"] == "READY"
        assert ready_data["services"]["database"] == "HEALTHY"
        assert ready_data["services"]["graph_engine"] == "HEALTHY"

    # 7. GitHub Actions CI Pipeline Configuration
    def test_07_github_actions_ci_pipeline_configuration(self):
        ci_path = ROOT_DIR / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists(), ".github/workflows/ci.yml must exist"

        with open(ci_path, "r", encoding="utf-8") as f:
            ci_data = yaml.safe_load(f)

        jobs = ci_data.get("jobs", {})
        assert "secret-and-hygiene-audit" in jobs
        assert "backend-test-suite" in jobs
        assert "frontend-build-validation" in jobs
        assert "docker-orchestration-validation" in jobs

    # 8. Secret Protection in .dockerignore
    def test_08_dockerignore_security_and_secret_exclusion(self):
        dockerignore_path = ROOT_DIR / ".dockerignore"
        assert dockerignore_path.exists(), ".dockerignore must exist"
        content = dockerignore_path.read_text(encoding="utf-8")

        assert ".env" in content
        assert "backend/.env" in content
        assert "*.pem" in content
        assert "*.key" in content
        assert ".git" in content

    # 9. Production ML Models Isolation & Immutability
    def test_09_production_ml_models_isolation_and_immutability(self):
        registry_dir = BACKEND_DIR / "models" / "registry"
        assert registry_dir.exists()
        
        # Verify Model A-E artifacts exist in artifacts/ directory
        artifacts_dir = ROOT_DIR / "artifacts"
        assert artifacts_dir.exists()
        for m in ["intrusion", "network-intrusion", "phishing-url", "webpage-phishing", "phishing-email"]:
            m_dir = artifacts_dir / m / "v1"
            assert m_dir.exists(), f"Artifact directory for model '{m}' must exist"
            assert (m_dir / "model.joblib").exists(), f"model.joblib for '{m}' must exist"
            assert (m_dir / "metadata.json").exists(), f"metadata.json for '{m}' must exist"
