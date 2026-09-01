"""
FastAPI Authentication API Endpoints for NetraGraph.
Supports OTP Request, Verification, Token Refresh, Logout, and User Profile (RBAC).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.config import auth_config
from app.auth.dependencies import get_current_user
from app.database.models import User
from app.database.postgres import get_async_db
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


# ============================================================
# Pydantic Request & Response Schemas
# ============================================================

class RequestOtpRequest(BaseModel):
    email: EmailStr = Field(..., description="Authorized officer Gmail address", examples=["officer@gmail.com"])


class RequestOtpResponse(BaseModel):
    success: bool
    message: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr = Field(..., description="Officer Gmail address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit cryptographic verification code", examples=["123456"])


class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    email_verified: bool = False
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


class VerifyOtpResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse
    message: str


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Optional refresh token string if not stored in HttpOnly cookie")


class RefreshTokenResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse
    message: str


class LogoutResponse(BaseModel):
    success: bool
    message: str


def extract_client_ip(request: Request) -> str:
    """Extract real client IP address, properly handling reverse proxies (X-Forwarded-For, X-Real-IP)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        client_ip = real_ip.strip()
        if client_ip:
            return client_ip
    return request.client.host if request.client else "127.0.0.1"


# ============================================================
# API Endpoints
# ============================================================

@router.post(
    "/request-otp",
    response_model=RequestOtpResponse,
    summary="Request Single-Use Gmail OTP",
    description="Validates email, checks rate limits, generates cryptographic OTP, and sends via email provider.",
)
async def request_otp_endpoint(
    payload: RequestOtpRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    client_ip = extract_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")

    success, message = await auth_service.request_otp(
        db=db,
        email=str(payload.email),
        ip_address=client_ip,
        user_agent=user_agent,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)

    return RequestOtpResponse(success=True, message=message)


@router.post(
    "/verify-otp",
    response_model=VerifyOtpResponse,
    summary="Verify OTP & Sign In",
    description="Verifies 6-digit OTP, creates authenticated session, issues JWT access token and rotating refresh token.",
)
async def verify_otp_endpoint(
    payload: VerifyOtpRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
):
    client_ip = extract_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")

    success, auth_data, message = await auth_service.verify_otp(
        db=db,
        email=str(payload.email),
        otp=payload.otp,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    if not success or not auth_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Set secure HttpOnly cookies for web client sessions
    response.set_cookie(
        key=auth_config.COOKIE_ACCESS_NAME,
        value=auth_data["access_token"],
        httponly=auth_config.COOKIE_HTTPONLY,
        secure=auth_config.COOKIE_SECURE,
        samesite=auth_config.COOKIE_SAMESITE,
        max_age=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key=auth_config.COOKIE_REFRESH_NAME,
        value=auth_data["refresh_token"],
        httponly=auth_config.COOKIE_HTTPONLY,
        secure=auth_config.COOKIE_SECURE,
        samesite=auth_config.COOKIE_SAMESITE,
        max_age=auth_config.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return VerifyOtpResponse(
        success=True,
        access_token=auth_data["access_token"],
        refresh_token=auth_data["refresh_token"],
        token_type=auth_data["token_type"],
        expires_in=auth_data["expires_in"],
        user=UserProfileResponse(**auth_data["user"]),
        message=message,
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Rotate Refresh Token & Issue Access Token",
)
async def refresh_token_endpoint(
    payload: Optional[RefreshTokenRequest],
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")

    # Extract refresh token from payload or cookie
    raw_token = None
    if payload and payload.refresh_token:
        raw_token = payload.refresh_token
    else:
        raw_token = request.cookies.get(auth_config.COOKIE_REFRESH_NAME)

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required in body or cookie.",
        )

    success, auth_data, message = await auth_service.refresh_tokens(
        db=db,
        raw_refresh_token=raw_token,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    if not success or not auth_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

    # Update cookies
    response.set_cookie(
        key=auth_config.COOKIE_ACCESS_NAME,
        value=auth_data["access_token"],
        httponly=auth_config.COOKIE_HTTPONLY,
        secure=auth_config.COOKIE_SECURE,
        samesite=auth_config.COOKIE_SAMESITE,
        max_age=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key=auth_config.COOKIE_REFRESH_NAME,
        value=auth_data["refresh_token"],
        httponly=auth_config.COOKIE_HTTPONLY,
        secure=auth_config.COOKIE_SECURE,
        samesite=auth_config.COOKIE_SAMESITE,
        max_age=auth_config.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return RefreshTokenResponse(
        success=True,
        access_token=auth_data["access_token"],
        refresh_token=auth_data["refresh_token"],
        token_type=auth_data["token_type"],
        expires_in=auth_data["expires_in"],
        user=UserProfileResponse(**auth_data["user"]),
        message=message,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Revoke Session & Logout",
)
async def logout_endpoint(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")

    await auth_service.logout(
        db=db,
        user_id=str(current_user.id),
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Delete cookies
    response.delete_cookie(key=auth_config.COOKIE_ACCESS_NAME)
    response.delete_cookie(key=auth_config.COOKIE_REFRESH_NAME)

    return LogoutResponse(success=True, message="Successfully logged out.")


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get Current Authenticated Officer Profile",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    role_names = getattr(current_user, "_role_names", [r.name for r in current_user.roles] if current_user.roles else ["INVESTIGATOR"])
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        roles=role_names,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    )
