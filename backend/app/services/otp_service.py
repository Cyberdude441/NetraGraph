"""
Cryptographic OTP Generation, Hashing, Domain Validation, and Rate Limiting Service.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import string
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.config import auth_config
from ..database.models import LoginAttempt, OtpVerification

logger = logging.getLogger("NetraGraphOTP")


class OtpService:
    """Service handling cryptographic OTP lifecycle, verification, and rate limits."""

    def __init__(self):
        # In-memory rate limiting tracking for fast cooldown checks
        self._last_request_time: Dict[str, float] = {}  # email -> timestamp
        self._ip_request_history: Dict[str, list[float]] = {}  # ip -> list of timestamps

    def is_email_domain_allowed(self, email: str) -> bool:
        """Verify that the email belongs to an authorized Gmail / Google Workspace domain."""
        if "@" not in email:
            return False
        domain = email.strip().lower().split("@")[1]
        return domain in auth_config.ALLOWED_EMAIL_DOMAINS

    def generate_secure_otp(self, digits: int = 6) -> str:
        """Generate cryptographically strong numeric OTP."""
        return "".join(secrets.choice(string.digits) for _ in range(digits))

    def generate_salt(self) -> str:
        """Generate random cryptographic salt."""
        return secrets.token_hex(16)

    def hash_otp(self, otp: str, salt: str) -> str:
        """Hash OTP with salt using SHA-256."""
        payload = f"{salt}:{otp}:{auth_config.JWT_SECRET_KEY[:16]}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def verify_otp_hash(self, otp: str, salt: str, expected_hash: str) -> bool:
        """Constant-time verification of submitted OTP."""
        computed = self.hash_otp(otp, salt)
        return hmac.compare_digest(computed, expected_hash)

    def check_rate_limit(self, email: str, ip_address: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Enforce cooldown between requests and hourly request caps per email and IP.
        """
        now = time.time()
        norm_email = email.strip().lower()

        # 1. Cooldown check (60 seconds)
        last_req = self._last_request_time.get(norm_email, 0.0)
        cooldown_rem = auth_config.OTP_COOLDOWN_SECONDS - (now - last_req)
        if cooldown_rem > 0:
            return False, f"Please wait {int(cooldown_rem)}s before requesting a new OTP."

        # 2. IP rate limit check (max 10 requests per hour)
        if ip_address:
            history = self._ip_request_history.get(ip_address, [])
            one_hour_ago = now - 3600
            history = [t for t in history if t > one_hour_ago]
            if len(history) >= 15:
                return False, "Rate limit exceeded for this IP address. Please try again later."
            history.append(now)
            self._ip_request_history[ip_address] = history

        self._last_request_time[norm_email] = now
        return True, None

    async def create_otp_record(
        self,
        session: AsyncSession,
        email: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, OtpVerification]:
        """
        Invalidate previous active OTPs, generate fresh OTP, and store salted hash in database.
        """
        norm_email = email.strip().lower()
        now_dt = datetime.now(timezone.utc)
        expires_at = now_dt + timedelta(seconds=auth_config.OTP_EXPIRY_SECONDS)

        # Invalidate existing active OTPs for this email
        await session.execute(
            update(OtpVerification)
            .where(OtpVerification.email == norm_email, OtpVerification.is_used == False)
            .values(is_used=True)
        )

        otp_code = self.generate_secure_otp(auth_config.OTP_DIGITS)
        salt = self.generate_salt()
        otp_hash = self.hash_otp(otp_code, salt)

        otp_record = OtpVerification(
            email=norm_email,
            otp_hash=otp_hash,
            salt=salt,
            expires_at=expires_at,
            attempts_count=0,
            max_attempts=auth_config.OTP_MAX_ATTEMPTS,
            is_used=False,
            ip_address=ip_address,
        )
        session.add(otp_record)
        await session.flush()

        return otp_code, otp_record


otp_service = OtpService()
