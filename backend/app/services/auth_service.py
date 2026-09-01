"""
Core Authentication and Session Management Service for NetraGraph.
Handles OTP workflows, JWT issuance, refresh token rotation, RBAC role assignment, and audit logs.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import jwt
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth.config import auth_config
from ..database.models import (
    AuditLogRecord,
    AuthSession,
    LoginAttempt,
    OtpVerification,
    RefreshToken,
    Role,
    User,
    user_roles,
)
from .email_provider import get_email_provider
from .otp_service import otp_service

logger = logging.getLogger("NetraGraphAuthService")


class AuthService:
    """Authentication and session lifecycle manager."""

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Hash a raw token string for secure database storage."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def create_access_token(
        self, user: User, session_id: str, role_names: Optional[List[str]] = None
    ) -> Tuple[str, datetime]:
        """Generate short-lived JWT access token."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        if role_names is None:
            try:
                role_names = [r.name for r in user.roles] if user.roles else ["ANALYST"]
            except Exception:
                role_names = ["ANALYST"]

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "roles": role_names,
            "session_id": session_id,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        token = jwt.encode(payload, auth_config.JWT_SECRET_KEY, algorithm=auth_config.JWT_ALGORITHM)
        return token, expires_at

    def generate_refresh_token(self) -> Tuple[str, str, datetime]:
        """Generate high-entropy refresh token, its hash, and expiry."""
        raw_token = secrets.token_urlsafe(48)
        token_hash = self.hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS)
        return raw_token, token_hash, expires_at

    async def request_otp(
        self,
        db: AsyncSession,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Request passwordless Gmail OTP code. Response is generic to prevent email enumeration.
        """
        norm_email = email.strip().lower()

        # 1. Validate email format and domain restriction
        if not otp_service.is_email_domain_allowed(norm_email):
            logger.info(f"OTP request rejected for non-whitelisted domain: {norm_email}")
            # Return generic message to prevent user enumeration
            return True, "If eligible, an authentication OTP has been dispatched to your email."

        # 2. Check rate limit & cooldown
        allowed, rate_msg = otp_service.check_rate_limit(norm_email, ip_address)
        if not allowed:
            return False, rate_msg or "Rate limit exceeded. Please wait before retrying."

        # 3. Create fresh OTP in database
        otp_code, _ = await otp_service.create_otp_record(db, norm_email, ip_address)

        # 4. Dispatch email via EmailProvider
        email_provider = get_email_provider()
        delivered = email_provider.send_otp_email(
            to_email=norm_email,
            otp_code=otp_code,
            expiry_minutes=auth_config.OTP_EXPIRY_SECONDS // 60,
        )

        # 5. Record Audit Log
        audit = AuditLogRecord(
            user_id=None,
            event_type="OTP_REQUESTED",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json={"email": norm_email, "delivered": delivered},
        )
        db.add(audit)
        await db.commit()

        return True, "If eligible, an authentication OTP has been dispatched to your email."

    async def verify_otp(
        self,
        db: AsyncSession,
        email: str,
        otp: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Verify single-use OTP, authenticate or register user, and create session tokens.
        """
        norm_email = email.strip().lower()
        now_dt = datetime.now(timezone.utc)

        # 1. Fetch latest active OTP for this email
        stmt = (
            select(OtpVerification)
            .where(
                OtpVerification.email == norm_email,
                OtpVerification.is_used == False,
            )
            .order_by(OtpVerification.created_at.desc())
        )
        res = await db.execute(stmt)
        otp_record = res.scalars().first()

        if not otp_record:
            db.add(LoginAttempt(email=norm_email, ip_address=ip_address, success=False))
            db.add(AuditLogRecord(event_type="OTP_FAILED", ip_address=ip_address, user_agent=user_agent, metadata_json={"reason": "NO_ACTIVE_OTP"}))
            await db.commit()
            return False, None, "Invalid or expired OTP code."

        # 2. Check Expiry
        rec_exp = otp_record.expires_at
        if rec_exp.tzinfo is None:
            rec_exp = rec_exp.replace(tzinfo=timezone.utc)
        if now_dt > rec_exp:
            otp_record.is_used = True
            db.add(LoginAttempt(email=norm_email, ip_address=ip_address, success=False))
            db.add(AuditLogRecord(event_type="OTP_FAILED", ip_address=ip_address, user_agent=user_agent, metadata_json={"reason": "EXPIRED"}))
            await db.commit()
            return False, None, "OTP code has expired. Please request a fresh code."

        # 3. Check Attempt Limit
        if otp_record.attempts_count >= otp_record.max_attempts:
            otp_record.is_used = True
            db.add(LoginAttempt(email=norm_email, ip_address=ip_address, success=False))
            db.add(AuditLogRecord(event_type="ACCOUNT_LOCKED", ip_address=ip_address, user_agent=user_agent, metadata_json={"reason": "MAX_ATTEMPTS_EXCEEDED"}))
            await db.commit()
            return False, None, "Maximum verification attempts exceeded. Please request a fresh OTP."

        # 4. Verify Cryptographic Hash
        is_valid = otp_service.verify_otp_hash(otp.strip(), otp_record.salt, otp_record.otp_hash)
        if not is_valid:
            otp_record.attempts_count += 1
            db.add(LoginAttempt(email=norm_email, ip_address=ip_address, success=False))
            db.add(AuditLogRecord(event_type="OTP_FAILED", ip_address=ip_address, user_agent=user_agent, metadata_json={"attempts": otp_record.attempts_count}))
            await db.commit()
            return False, None, f"Incorrect OTP code. {otp_record.max_attempts - otp_record.attempts_count} attempts remaining."

        # 5. Mark OTP as Used
        otp_record.is_used = True

        # 6. Find or Create User
        user_stmt = select(User).where(User.email == norm_email).options(selectinload(User.roles))
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            # Assign display name from email prefix
            display_name = norm_email.split("@")[0].replace(".", " ").title()
            user = User(
                email=norm_email,
                email_verified=True,
                display_name=display_name,
                status="ACTIVE",
                last_login_at=now_dt,
            )
            db.add(user)
            await db.flush()

            # Assign default INVESTIGATOR role directly in user_roles
            role_stmt = select(Role).where(Role.name == "INVESTIGATOR")
            role_res = await db.execute(role_stmt)
            default_role = role_res.scalar_one_or_none()
            if default_role:
                await db.execute(user_roles.insert().values(user_id=user.id, role_id=default_role.id))
                await db.flush()
        else:
            user.email_verified = True
            user.last_login_at = now_dt

        # Query assigned roles explicitly and safely
        role_query = (
            select(Role.name)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(user_roles.c.user_id == user.id)
        )
        role_rows = await db.execute(role_query)
        role_list = list(role_rows.scalars().all()) or ["INVESTIGATOR"]

        # 7. Create Session & Rotating Refresh Token
        session_token = secrets.token_urlsafe(32)
        session_token_hash = self.hash_token(session_token)
        session_exp = now_dt + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS)

        auth_session = AuthSession(
            user_id=user.id,
            session_token_hash=session_token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=session_exp,
            is_revoked=False,
        )
        db.add(auth_session)
        await db.flush()

        raw_refresh, refresh_hash, refresh_exp = self.generate_refresh_token()
        refresh_token_rec = RefreshToken(
            user_id=user.id,
            session_id=auth_session.id,
            token_hash=refresh_hash,
            expires_at=refresh_exp,
            is_revoked=False,
        )
        db.add(refresh_token_rec)

        # 8. Issue JWT Access Token
        access_token, access_exp = self.create_access_token(user, auth_session.id, role_names=role_list)
        user_id = str(user.id)
        user_email = user.email
        user_display = user.display_name
        user_verified = user.email_verified
        user_created = user.created_at.isoformat() if user.created_at else None
        user_login = user.last_login_at.isoformat() if user.last_login_at else None

        # 9. Record Success Audit Log & Login Attempt
        db.add(LoginAttempt(email=norm_email, ip_address=ip_address, success=True))
        db.add(AuditLogRecord(
            user_id=user.id,
            event_type="LOGIN_SUCCESS",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json={"session_id": auth_session.id, "email": norm_email},
        ))
        await db.commit()

        auth_data = {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
            "expires_in": auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user_id,
                "email": user_email,
                "display_name": user_display,
                "roles": role_list,
                "email_verified": user_verified,
                "created_at": user_created,
                "last_login_at": user_login,
            },
        }

        return True, auth_data, "Authentication successful."

    async def refresh_tokens(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Rotate refresh token and issue new short-lived access token.
        """
        token_hash = self.hash_token(raw_refresh_token)
        now_dt = datetime.now(timezone.utc)

        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .options(selectinload(RefreshToken.user).selectinload(User.roles))
        )
        res = await db.execute(stmt)
        token_rec = res.scalar_one_or_none()

        if not token_rec or token_rec.is_revoked:
            return False, None, "Invalid or revoked refresh token."

        rec_exp = token_rec.expires_at
        if rec_exp.tzinfo is None:
            rec_exp = rec_exp.replace(tzinfo=timezone.utc)
        if now_dt > rec_exp:
            token_rec.is_revoked = True
            await db.commit()
            return False, None, "Refresh token has expired."

        user = token_rec.user
        if not user or user.status != "ACTIVE":
            return False, None, "User account is suspended or inactive."

        # Token Rotation: Revoke old refresh token
        token_rec.is_revoked = True
        new_raw_refresh, new_refresh_hash, new_refresh_exp = self.generate_refresh_token()
        token_rec.replaced_by_token_hash = new_refresh_hash

        new_refresh_rec = RefreshToken(
            user_id=user.id,
            session_id=token_rec.session_id,
            token_hash=new_refresh_hash,
            expires_at=new_refresh_exp,
            is_revoked=False,
        )
        # Query assigned roles explicitly and safely
        role_query = (
            select(Role.name)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .where(user_roles.c.user_id == user.id)
        )
        role_rows = await db.execute(role_query)
        role_list = list(role_rows.scalars().all()) or ["INVESTIGATOR"]

        access_token, _ = self.create_access_token(user, token_rec.session_id or str(user.id), role_names=role_list)
        user_id = str(user.id)
        user_email = user.email
        user_display = user.display_name
        user_verified = user.email_verified

        db.add(AuditLogRecord(
            user_id=user.id,
            event_type="TOKEN_REFRESH",
            ip_address=ip_address,
            user_agent=user_agent,
        ))
        await db.commit()

        return True, {
            "access_token": access_token,
            "refresh_token": new_raw_refresh,
            "token_type": "bearer",
            "expires_in": auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user_id,
                "email": user_email,
                "display_name": user_display,
                "roles": role_list,
                "email_verified": user_verified,
            },
        }, "Token refreshed successfully."

    async def logout(
        self,
        db: AsyncSession,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Revoke active session and refresh tokens upon officer logout.
        """
        if session_id:
            await db.execute(
                update(AuthSession).where(AuthSession.id == session_id).values(is_revoked=True)
            )
            await db.execute(
                update(RefreshToken).where(RefreshToken.session_id == session_id).values(is_revoked=True)
            )
        elif user_id:
            await db.execute(
                update(AuthSession).where(AuthSession.user_id == user_id).values(is_revoked=True)
            )
            await db.execute(
                update(RefreshToken).where(RefreshToken.user_id == user_id).values(is_revoked=True)
            )

        db.add(AuditLogRecord(
            user_id=user_id,
            event_type="LOGOUT",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json={"session_id": session_id},
        ))
        await db.commit()
        return True


auth_service = AuthService()
