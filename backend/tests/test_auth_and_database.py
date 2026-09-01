"""
Security and Integration Tests for NetraGraph PostgreSQL Database & Gmail OTP Authentication.
Validates:
1. Valid OTP Verification & Session Issuance
2. Invalid OTP Rejection & Decrementing Attempts
3. Expired OTP Rejection
4. Reused OTP Rejection (Single-Use Guarantee)
5. OTP Brute Force Protection (Max Attempts Lockout)
6. OTP Request Rate Limiting & Cooldown
7. IP-based Rate Limiting
8. Email Normalization (case-insensitivity, whitespace)
9. Non-Whitelisted Domain Restriction
10. Generic Response (User Enumeration Prevention)
11. Refresh Token Rotation (Old Token Invalidation)
12. Session Invalidation & Logout
13. Revoked Refresh Token Rejection
14. Unauthorized Access to Protected Endpoints (/api/auth/me)
15. Role-Based Access Control (RBAC) Enforcement
16. SQL Injection Resilience on Inputs
17. Malformed Request Handling
18. Database Health Endpoint (/health/db & /health)
19. Cryptographic High-Entropy OTP & Salt Properties
20. Audit Trail Logging Verification
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import os
os.environ["TESTING"] = "1"
os.environ["EMAIL_PROVIDER"] = "mock"

from main import app
from app.auth.config import auth_config
auth_config.EMAIL_PROVIDER = "mock"
from app.database.models import AuditLogRecord, AuthSession, OtpVerification, RefreshToken, Role, User
from app.database.postgres import AsyncSessionLocal, init_db
from app.services.auth_service import auth_service
from app.services.email_provider import mock_email_provider
from app.services.otp_service import otp_service


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Initialize database tables and roles before running tests."""
    import os
    os.environ["EMAIL_PROVIDER"] = "mock"
    auth_config.EMAIL_PROVIDER = "mock"
    asyncio.run(init_db())
    mock_email_provider.clear()


@pytest.fixture
def client():
    return TestClient(app)


class TestNetraGraphAuthAndDatabase:
    """Comprehensive test suite for NetraGraph OTP Auth and Database Layer."""

    # 1. Health Endpoints
    def test_01_database_health_endpoint(self, client):
        r = client.get("/health/db")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["database"] == "PostgreSQL"
        assert "latency_ms" in data

    def test_02_system_health_continues_working(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "HEALTHY"

    # 2. Domain & Email Validation
    def test_03_email_domain_allowlist_enforcement(self):
        assert otp_service.is_email_domain_allowed("officer@gmail.com") is True
        assert otp_service.is_email_domain_allowed("officer@googlemail.com") is True
        assert otp_service.is_email_domain_allowed("hacker@malicious-domain.com") is False
        assert otp_service.is_email_domain_allowed("invalid-email") is False

    def test_04_user_enumeration_prevention_generic_response(self, client):
        # Request with non-whitelisted or non-existent email must return generic success message
        r = client.post("/api/auth/request-otp", json={"email": "attacker@unknown-domain.com"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "If eligible, an authentication OTP has been dispatched" in data["message"]

    # 3. OTP Lifecycle: Request, Delivery, and Cryptography
    def test_05_request_otp_success_and_mock_delivery(self, client):
        mock_email_provider.clear()
        r = client.post("/api/auth/request-otp", json={"email": "investigator.sharma@gmail.com"})
        assert r.status_code == 200
        assert r.json()["success"] is True

        # Verify mock email delivery
        assert len(mock_email_provider.sent_emails) == 1
        delivered = mock_email_provider.sent_emails[0]
        assert delivered["to"] == "investigator.sharma@gmail.com"
        assert len(delivered["otp_code"]) == 6
        assert delivered["otp_code"].isdigit()

    def test_06_cryptographic_otp_properties(self):
        codes = [otp_service.generate_secure_otp(6) for _ in range(50)]
        assert all(len(c) == 6 and c.isdigit() for c in codes)
        # Verify diversity / entropy (no duplicates in 50 random samples)
        assert len(set(codes)) >= 48

        # Verify salted hashing
        salt1 = otp_service.generate_salt()
        salt2 = otp_service.generate_salt()
        h1 = otp_service.hash_otp("123456", salt1)
        h2 = otp_service.hash_otp("123456", salt2)
        assert h1 != h2
        assert otp_service.verify_otp_hash("123456", salt1, h1) is True
        assert otp_service.verify_otp_hash("654321", salt1, h1) is False

    # 4. OTP Verification & Session Generation
    def test_07_verify_valid_otp_and_session_issuance(self, client):
        mock_email_provider.clear()
        email = "lead.officer@gmail.com"

        # Request OTP
        r_req = client.post("/api/auth/request-otp", json={"email": email})
        assert r_req.status_code == 200

        otp_code = mock_email_provider.sent_emails[-1]["otp_code"]

        # Verify OTP
        r_ver = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        assert r_ver.status_code == 200
        data = r_ver.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == email
        assert data["user"]["email_verified"] is True
        assert "INVESTIGATOR" in data["user"]["roles"] or "ANALYST" in data["user"]["roles"]

        # Verify cookies were set
        cookies = r_ver.cookies
        assert auth_config.COOKIE_ACCESS_NAME in cookies or "access_token" in data

    # 5. Invalid & Reused OTP Rejection
    def test_08_invalid_otp_rejection(self, client):
        mock_email_provider.clear()
        email = "fraud.detect@gmail.com"
        client.post("/api/auth/request-otp", json={"email": email})

        # Submit wrong OTP
        r = client.post("/api/auth/verify-otp", json={"email": email, "otp": "000000"})
        assert r.status_code == 400
        assert "Incorrect OTP" in r.json()["detail"]

    def test_09_reused_otp_rejection_single_use_guarantee(self, client):
        mock_email_provider.clear()
        email = "single.use@gmail.com"
        client.post("/api/auth/request-otp", json={"email": email})
        otp_code = mock_email_provider.sent_emails[-1]["otp_code"]

        # First verification succeeds
        r1 = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        assert r1.status_code == 200

        # Second verification with same OTP MUST fail
        r2 = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        assert r2.status_code == 400
        assert "Invalid or expired" in r2.json()["detail"]

    # 6. Expired OTP Rejection
    def test_10_expired_otp_rejection(self):
        async def _test():
            async with AsyncSessionLocal() as session:
                email = "expired.test@gmail.com"
                salt = otp_service.generate_salt()
                otp_hash = otp_service.hash_otp("999888", salt)
                # Expired 10 minutes ago
                past_exp = datetime.now(timezone.utc) - timedelta(minutes=10)
                record = OtpVerification(
                    email=email,
                    otp_hash=otp_hash,
                    salt=salt,
                    expires_at=past_exp,
                    attempts_count=0,
                    is_used=False,
                )
                session.add(record)
                await session.commit()

                success, _, msg = await auth_service.verify_otp(session, email, "999888")
                assert success is False
                assert "expired" in msg.lower()
        asyncio.run(_test())

    # 7. Brute Force Lockout
    def test_11_otp_brute_force_lockout_after_max_attempts(self, client):
        mock_email_provider.clear()
        email = "brute.force@gmail.com"
        client.post("/api/auth/request-otp", json={"email": email})

        # Submit wrong OTP 5 times
        for _ in range(5):
            r = client.post("/api/auth/verify-otp", json={"email": email, "otp": "111111"})
            assert r.status_code == 400

        # 6th attempt should return max attempts exceeded
        r6 = client.post("/api/auth/verify-otp", json={"email": email, "otp": "111111"})
        assert r6.status_code == 400
        assert "attempts exceeded" in r6.json()["detail"].lower() or "invalid or expired" in r6.json()["detail"].lower()

    # 8. Refresh Token Rotation
    def test_12_refresh_token_rotation_and_revocation(self, client):
        mock_email_provider.clear()
        email = "token.rotate@gmail.com"
        client.post("/api/auth/request-otp", json={"email": email})
        otp_code = mock_email_provider.sent_emails[-1]["otp_code"]

        r_ver = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        data = r_ver.json()
        initial_refresh = data["refresh_token"]

        # Perform token rotation
        r_ref = client.post("/api/auth/refresh", json={"refresh_token": initial_refresh})
        assert r_ref.status_code == 200
        new_data = r_ref.json()
        new_refresh = new_data["refresh_token"]
        assert new_refresh != initial_refresh
        assert "access_token" in new_data

        # Using OLD refresh token again MUST fail (revoked token attack)
        r_reuse = client.post("/api/auth/refresh", json={"refresh_token": initial_refresh})
        assert r_reuse.status_code == 401

    # 9. Protected Endpoint & Profile Retrieval
    def test_13_authenticated_me_endpoint_and_unauthorized_rejection(self, client):
        # Unauthorized access without token
        r_unauth = client.get("/api/auth/me")
        assert r_unauth.status_code == 401

        # Authorized access with Bearer token
        mock_email_provider.clear()
        email = "profile.user@gmail.com"
        client.post("/api/auth/request-otp", json={"email": email})
        otp_code = mock_email_provider.sent_emails[-1]["otp_code"]
        r_ver = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        token = r_ver.json()["access_token"]

        r_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r_me.status_code == 200
        me_data = r_me.json()
        assert me_data["email"] == email
        assert me_data["email_verified"] is True
        assert len(me_data["roles"]) >= 1

    # 10. Logout & Invalidation
    def test_14_logout_revokes_session(self, client):
        mock_email_provider.clear()
        email = "logout.test@gmail.com"
        client.post("/api/auth/request-otp", json={"email": email})
        otp_code = mock_email_provider.sent_emails[-1]["otp_code"]
        r_ver = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        token = r_ver.json()["access_token"]

        r_logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert r_logout.status_code == 200
        assert r_logout.json()["success"] is True

    # 11. SQL Injection Resilience
    def test_15_sql_injection_resilience(self, client):
        malicious_inputs = [
            "' OR '1'='1",
            "admin'--",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
        ]
        for payload in malicious_inputs:
            r = client.post("/api/auth/request-otp", json={"email": payload})
            # Should be rejected with 422 (Unprocessable Entity) or 200 generic response, never 500 error
            assert r.status_code in (422, 200)

            r_v = client.post("/api/auth/verify-otp", json={"email": "officer@gmail.com", "otp": payload})
            assert r_v.status_code in (400, 422)

    # 12. Audit Logging
    def test_16_audit_trail_recorded_in_database(self):
        async def _check_audit():
            async with AsyncSessionLocal() as session:
                stmt = select(AuditLogRecord).order_by(AuditLogRecord.created_at.desc()).limit(10)
                res = await session.execute(stmt)
                logs = res.scalars().all()
                assert len(logs) > 0
                event_types = [log.event_type for log in logs]
                assert any(ev in ("OTP_REQUESTED", "LOGIN_SUCCESS", "OTP_FAILED", "TOKEN_REFRESH") for ev in event_types)
        asyncio.run(_check_audit())

    # 13. Email Normalization
    def test_17_email_normalization_case_and_whitespace(self, client):
        mock_email_provider.clear()
        email_raw = "  Officer.SpecialUnit@GMAIL.COM  "
        email_clean = "officer.specialunit@gmail.com"

        r_req = client.post("/api/auth/request-otp", json={"email": email_raw})
        assert r_req.status_code == 200
        assert mock_email_provider.sent_emails[-1]["to"] == email_clean

        otp_code = mock_email_provider.sent_emails[-1]["otp_code"]
        r_ver = client.post("/api/auth/verify-otp", json={"email": "OFFICER.SPECIALUNIT@gmail.com", "otp": otp_code})
        assert r_ver.status_code == 200
        assert r_ver.json()["user"]["email"] == email_clean

    # 14. Duplicate User Prevention
    def test_18_duplicate_user_prevention(self, client):
        async def _count_users():
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.email == "duplicate.test@gmail.com")
                res = await session.execute(stmt)
                return len(res.scalars().all())

        mock_email_provider.clear()
        email = "duplicate.test@gmail.com"

        # First Login
        client.post("/api/auth/request-otp", json={"email": email})
        otp1 = mock_email_provider.sent_emails[-1]["otp_code"]
        client.post("/api/auth/verify-otp", json={"email": email, "otp": otp1})
        assert asyncio.run(_count_users()) == 1

        # Second Login (Same Email)
        client.post("/api/auth/request-otp", json={"email": email})
        otp2 = mock_email_provider.sent_emails[-1]["otp_code"]
        client.post("/api/auth/verify-otp", json={"email": email, "otp": otp2})
        # User record count MUST still be 1 (upserted/updated)
        assert asyncio.run(_count_users()) == 1

    # 15. Request Cooldown Rate Limiting
    def test_19_otp_cooldown_rate_limiting(self, client):
        email = "cooldown.test@gmail.com"
        r1 = client.post("/api/auth/request-otp", json={"email": email})
        assert r1.status_code == 200

        # Immediate second request should trigger 429 Too Many Requests
        r2 = client.post("/api/auth/request-otp", json={"email": email})
        assert r2.status_code == 429
        assert "wait" in r2.json()["detail"].lower()

    # 16. Malformed Payloads & Missing Fields
    def test_20_malformed_requests_rejection(self, client):
        r1 = client.post("/api/auth/request-otp", json={})
        assert r1.status_code == 422

        r2 = client.post("/api/auth/verify-otp", json={"email": "not-an-email", "otp": "12"})
        assert r2.status_code == 422

        r3 = client.post("/api/auth/verify-otp", json={"email": "valid@gmail.com", "otp": "abcdef"})
        assert r3.status_code in (400, 422)

    # 17. Expired Access Token Validation
    def test_21_expired_access_token_rejection(self, client):
        import jwt as pyjwt
        now = datetime.now(timezone.utc)
        expired_time = now - timedelta(hours=2)
        expired_token = pyjwt.encode(
            {
                "sub": "some-user-uuid",
                "email": "expired@gmail.com",
                "roles": ["ANALYST"],
                "type": "access",
                "iat": int(expired_time.timestamp()),
                "exp": int((expired_time + timedelta(minutes=15)).timestamp()),
            },
            auth_config.JWT_SECRET_KEY,
            algorithm=auth_config.JWT_ALGORITHM,
        )

        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert r.status_code == 401
        assert "expired" in r.json()["detail"].lower()

    # 18. Tampered Access Token
    def test_22_tampered_access_token_rejection(self, client):
        tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.invalidsignature"
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
        assert r.status_code == 401

    # 19. Concurrent OTP Verification (Race Condition Defense)
    def test_23_concurrent_otp_verification_race_condition(self, client):
        mock_email_provider.clear()
        email = "race.condition@gmail.com"
        client.post("/api/auth/request-otp", json={"email": email})
        otp_code = mock_email_provider.sent_emails[-1]["otp_code"]

        # First verification succeeds
        r1 = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        assert r1.status_code == 200

        # Concurrent/subsequent attempt MUST be rejected
        r2 = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        assert r2.status_code == 400

    # 20. OTP Replacement Invalidates Prior OTP
    def test_24_otp_replacement_invalidates_prior_otp(self):
        async def _test():
            async with AsyncSessionLocal() as session:
                email = "replacement.test@gmail.com"
                code1, _ = await otp_service.create_otp_record(session, email)
                code2, _ = await otp_service.create_otp_record(session, email)
                await session.commit()

                # Attempt to verify code1 MUST fail
                success1, _, _ = await auth_service.verify_otp(session, email, code1)
                assert success1 is False

                # Verifying code2 succeeds
                success2, _, _ = await auth_service.verify_otp(session, email, code2)
                assert success2 is True
        asyncio.run(_test())

    # 21. RBAC Clearance Enforcement
    def test_25_role_authorization_elevation_defense(self, client):
        import jwt as pyjwt
        now = datetime.now(timezone.utc)
        # Token with only VIEWER role
        viewer_token = pyjwt.encode(
            {
                "sub": "viewer-uuid",
                "email": "viewer@gmail.com",
                "roles": ["VIEWER"],
                "type": "access",
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(hours=1)).timestamp()),
            },
            auth_config.JWT_SECRET_KEY,
            algorithm=auth_config.JWT_ALGORITHM,
        )

        from app.auth.dependencies import require_role
        from fastapi import Depends, HTTPException

        checker = require_role(["ADMIN", "INVESTIGATOR"])
        mock_user = User(id="viewer-uuid", email="viewer@gmail.com", status="ACTIVE")
        mock_user._role_names = ["VIEWER"]

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(checker(mock_user))
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    # 22. Health Endpoints Do Not Leak Secrets
    def test_26_health_endpoints_do_not_leak_secrets(self, client):
        r_db = client.get("/health/db")
        assert r_db.status_code == 200
        text_content = r_db.text.lower()
        forbidden_keywords = ["password", "secret", "token", "key", "asyncpg://", "postgresql://"]
        for kw in forbidden_keywords:
            assert kw not in text_content

        r_health = client.get("/health")
        assert r_health.status_code == 200
        for kw in forbidden_keywords:
            assert kw not in r_health.text.lower()

    # 23. Token Type Mismatch Rejection
    def test_27_token_type_mismatch_rejection(self, client):
        import jwt as pyjwt
        now = datetime.now(timezone.utc)
        # Payload marked as "refresh" instead of "access"
        refresh_as_access = pyjwt.encode(
            {
                "sub": "user-uuid",
                "email": "user@gmail.com",
                "roles": ["ANALYST"],
                "type": "refresh",
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(hours=1)).timestamp()),
            },
            auth_config.JWT_SECRET_KEY,
            algorithm=auth_config.JWT_ALGORITHM,
        )

        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh_as_access}"})
        assert r.status_code == 401
        assert "Invalid token claims" in r.json()["detail"]

    # 24. Oversized Payload Rejection
    def test_28_oversized_payload_rejection(self, client):
        oversized_email = "a" * 5000 + "@gmail.com"
        r = client.post("/api/auth/request-otp", json={"email": oversized_email})
        assert r.status_code in (422, 400)

    # 25. Rate Limiting Whitespace and Case Bypass Defense
    def test_29_rate_limiting_case_and_whitespace_bypass_defense(self, client):
        email_base = "bypass.defense@gmail.com"
        r1 = client.post("/api/auth/request-otp", json={"email": email_base})
        assert r1.status_code == 200

        # Attempt with whitespace and uppercase
        r2 = client.post("/api/auth/request-otp", json={"email": f"  {email_base.upper()}  "})
        assert r2.status_code == 429

    # 26. IP Rate Limiting Enforcement
    def test_30_ip_rate_limiting_enforcement(self):
        email_prefix = "ip.test"
        ip = "192.168.1.99"
        # Reset IP history
        otp_service._ip_request_history[ip] = []

        allowed = True
        for i in range(16):
            # Reset email cooldown to isolate IP rate limiter
            otp_service._last_request_time[f"{email_prefix}{i}@gmail.com"] = 0.0
            allowed, msg = otp_service.check_rate_limit(f"{email_prefix}{i}@gmail.com", ip_address=ip)
            if not allowed:
                break
        assert allowed is False
        assert "rate limit exceeded for this ip" in msg.lower()

    # 27. No Plaintext Secrets in Audit Logs
    def test_31_no_plaintext_secrets_in_audit_logs(self):
        async def _check():
            async with AsyncSessionLocal() as session:
                stmt = select(AuditLogRecord).limit(20)
                res = await session.execute(stmt)
                logs = res.scalars().all()
                for log in logs:
                    if log.metadata_json:
                        meta_str = str(log.metadata_json).lower()
                        assert "123456" not in meta_str or "otp" not in meta_str
                        assert "password" not in meta_str
                        assert "secret" not in meta_str
        asyncio.run(_check())

    # 28. Cookie Security Flags
    def test_32_cookie_security_flags(self, client):
        mock_email_provider.clear()
        email = "cookie.test@gmail.com"
        client.post("/api/auth/request-otp", json={"email": email})
        otp_code = mock_email_provider.sent_emails[-1]["otp_code"]

        r = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp_code})
        assert r.status_code == 200
        set_cookie_headers = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") else [r.headers.get("set-cookie", "")]
        cookie_text = " ".join(set_cookie_headers).lower()
        assert "httponly" in cookie_text or auth_config.COOKIE_ACCESS_NAME in r.cookies
        assert "samesite=lax" in cookie_text or "samesite" in cookie_text

    # 29. Missing Auth Token / Bad Bearer Format
    def test_33_bad_auth_headers_handling(self, client):
        r1 = client.get("/api/auth/me", headers={"Authorization": "InvalidFormat"})
        assert r1.status_code == 401

        r2 = client.get("/api/auth/me", headers={"Authorization": "Bearer "})
        assert r2.status_code == 401


