"""
Authentication and Database Configuration for NetraGraph.
Loads all secrets, tokens, rates, and email settings strictly from environment variables.
"""
from __future__ import annotations

import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Search for .env file across project hierarchy
_file_path = Path(__file__).resolve()
_backend_dir = _file_path.parents[2]  # backend/
_root_dir = _file_path.parents[3]     # workspace root

if (_root_dir / ".env").exists():
    load_dotenv(dotenv_path=_root_dir / ".env", override=True)
if (_backend_dir / ".env").exists():
    load_dotenv(dotenv_path=_backend_dir / ".env", override=True)
load_dotenv(override=False)


import urllib.parse

def _normalize_db_url(raw_url: str) -> str:
    """Normalize database connection string, URL-encoding special characters in password."""
    if not raw_url:
        return raw_url
    try:
        if "://" in raw_url and "@" in raw_url:
            scheme, rest = raw_url.split("://", 1)
            creds, host_db = rest.rsplit("@", 1)
            if ":" in creds:
                user, password = creds.split(":", 1)
                unquoted_pw = urllib.parse.unquote_plus(password)
                encoded_pw = urllib.parse.quote_plus(unquoted_pw)
                return f"{scheme}://{user}:{encoded_pw}@{host_db}"
    except Exception:
        pass
    return raw_url


class AuthConfig:
    # Database Settings
    DATABASE_URL: str = _normalize_db_url(os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/netragraph"
    ))
    # Synchronous DB URL for Alembic and sync health checks
    DATABASE_SYNC_URL: str = _normalize_db_url(os.getenv(
        "DATABASE_SYNC_URL",
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/netragraph").replace("+asyncpg", "")
    ))
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    # JWT & Session Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "netragraph-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

    # OTP Security Settings
    OTP_EXPIRY_SECONDS: int = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))  # 5 minutes
    OTP_COOLDOWN_SECONDS: int = int(os.getenv("OTP_COOLDOWN_SECONDS", "60"))  # 1 minute between requests
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    OTP_MAX_REQUESTS_PER_HOUR: int = int(os.getenv("OTP_MAX_REQUESTS_PER_HOUR", "5"))
    OTP_DIGITS: int = 6

    # Allowed Email Domains (Gmail & Configurable Google Workspace Domains)
    _raw_domains: str = os.getenv("ALLOWED_EMAIL_DOMAINS", "gmail.com,googlemail.com")
    ALLOWED_EMAIL_DOMAINS: List[str] = [d.strip().lower() for d in _raw_domains.split(",") if d.strip()]

    # Email Delivery Settings (SMTP / Gmail App Password)
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "smtp")  # smtp, mock, console
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or os.getenv("GMAIL_USER") or ""
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS") or os.getenv("GMAIL_APP_PASSWORD") or ""
    SMTP_FROM: str = os.getenv("SMTP_FROM") or os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or "netragraph-security@gmail.com"
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "NetraGraph Security Division")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "t")

    # Cookie Protection Settings
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "False").lower() in ("true", "1", "t")
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")
    COOKIE_HTTPONLY: bool = True
    COOKIE_ACCESS_NAME: str = "netragraph_access_token"
    COOKIE_REFRESH_NAME: str = "netragraph_refresh_token"


auth_config = AuthConfig()
