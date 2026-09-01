"""
FastAPI Authentication, JWT Extraction, and Role-Based Access Control (RBAC) Dependencies.
"""
from __future__ import annotations

import logging
from typing import Callable, List, Optional
from fastapi import Cookie, Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .config import auth_config
from ..database.models import User
from ..database.postgres import get_async_db

logger = logging.getLogger("NetraGraphAuthDep")
security_bearer = HTTPBearer(auto_error=False)


async def get_token_from_request(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[str]:
    """
    Extract JWT token from Authorization header (Bearer) or HttpOnly secure cookie.
    """
    if auth_header and auth_header.credentials:
        return auth_header.credentials
    # Fallback to cookie
    cookie_token = request.cookies.get(auth_config.COOKIE_ACCESS_NAME)
    if cookie_token:
        return cookie_token
    return None


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Validate JWT access token and retrieve current authenticated user.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please sign in via Gmail OTP.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            auth_config.JWT_SECRET_KEY,
            algorithms=[auth_config.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if not user_id or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please refresh session.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user.status.lower()}.",
        )

    # Cache roles on user instance before session closes
    user._role_names = [r.name for r in user.roles] if user.roles else ["ANALYST"]
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency verifying that the authenticated user is currently active."""
    if current_user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive officer account.")
    return current_user


def require_role(allowed_roles: List[str]) -> Callable:
    """
    RBAC dependency factory checking if user possesses any of the required roles.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_names = [r.upper() for r in getattr(current_user, "_role_names", ["ANALYST"])]
        allowed_upper = [r.upper() for r in allowed_roles]

        # ADMIN always has full clearance
        if "ADMIN" in user_role_names:
            return current_user

        if not any(r in allowed_upper for r in user_role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of the following clearance roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
