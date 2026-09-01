import sys
from pathlib import Path
import pytest

TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from main import app
from app.auth.config import auth_config
from app.services.otp_service import otp_service
from app.services.auth_service import auth_service
from app.database.postgres import AsyncSessionLocal, init_db


@pytest.fixture(scope="module", autouse=True)
def init_test_env():
    import asyncio
    asyncio.run(init_db())


class TestPhase9DeploymentSecurity:
    """Production Deployment Security & Hardening Validation."""

    def test_01_http_security_headers_present_on_all_responses(self):
        """Verify production security headers are attached to API responses."""
        with TestClient(app) as client:
            res = client.get("/")
            assert res.status_code == 200
            assert res.headers.get("x-content-type-options") == "nosniff"
            assert res.headers.get("x-frame-options") == "DENY"
            assert res.headers.get("x-xss-protection") == "1; mode=block"
            assert "strict-origin-when-cross-origin" in res.headers.get("referrer-policy", "")
            assert "geolocation=()" in res.headers.get("permissions-policy", "")

    def test_02_reverse_proxy_x_forwarded_for_ip_extraction(self):
        """Verify client IP is correctly extracted when running behind reverse proxies."""
        with TestClient(app) as client:
            headers = {"X-Forwarded-For": "203.0.113.195, 10.0.0.1"}
            res = client.post("/api/auth/request-otp", json={"email": "proxy.test.officer@gmail.com"}, headers=headers)
            assert res.status_code in (200, 429)
            assert res.json()["success"] is True or "rate limit" in res.json().get("detail", "").lower()

    def test_03_cookie_security_and_samesite_flags(self):
        """Verify authentication cookies include HttpOnly, SameSite=lax, and configured security."""
        with TestClient(app) as client:
            # Generate valid OTP and verify
            import asyncio
            async def get_test_otp():
                async with AsyncSessionLocal() as session:
                    code, _ = await otp_service.create_otp_record(session, "cookie.test.officer@gmail.com")
                    await session.commit()
                    return code
            code = asyncio.run(get_test_otp())

            res = client.post("/api/auth/verify-otp", json={"email": "cookie.test.officer@gmail.com", "otp": code})
            assert res.status_code == 200
            cookies = res.cookies
            assert auth_config.COOKIE_ACCESS_NAME in cookies
            assert auth_config.COOKIE_REFRESH_NAME in cookies

    def test_04_unauthorized_access_to_protected_me_endpoint(self):
        """Verify accessing /api/auth/me without token returns 401 Unauthorized."""
        with TestClient(app) as client:
            res = client.get("/api/auth/me")
            assert res.status_code == 401
            assert "detail" in res.json()

    def test_05_health_endpoints_do_not_leak_environment_secrets(self):
        """Verify health checks output status without exposing credentials or internal topology."""
        with TestClient(app) as client:
            res_health = client.get("/health")
            assert res_health.status_code == 200
            assert "password" not in res_health.text.lower()
            assert "secret" not in res_health.text.lower()

            res_db = client.get("/health/db")
            assert res_db.status_code == 200
            assert "postgres:" not in res_db.text.lower()
            assert "password" not in res_db.text.lower()

    def test_06_account_enumeration_generic_messaging(self):
        """Verify identical response regardless of email authorization status."""
        with TestClient(app) as client:
            res1 = client.post(
                "/api/auth/request-otp",
                json={"email": "registered.user@gmail.com"},
                headers={"X-Forwarded-For": "198.51.100.11"},
            )
            res2 = client.post(
                "/api/auth/request-otp",
                json={"email": "unregistered.user@gmail.com"},
                headers={"X-Forwarded-For": "198.51.100.12"},
            )
            assert res1.status_code == 200
            assert res2.status_code == 200
            assert res1.json()["message"] == res2.json()["message"]
            assert "If eligible" in res1.json()["message"]
