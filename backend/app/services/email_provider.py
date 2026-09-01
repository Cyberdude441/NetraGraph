"""
Email Provider Abstraction for NetraGraph OTP Delivery.
Supports SMTP / Gmail App Passwords, HTML security templates, and mock/console providers.
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Any, Dict, List, Optional

from ..auth.config import auth_config

logger = logging.getLogger("NetraGraphEmail")


class BaseEmailProvider(ABC):
    """Abstract Base Class for email delivery providers."""

    @abstractmethod
    def send_otp_email(self, to_email: str, otp_code: str, expiry_minutes: int = 5) -> bool:
        """Send 6-digit OTP code to the recipient."""
        pass


class MockEmailProvider(BaseEmailProvider):
    """Mock provider for unit testing and local CI without live SMTP server."""

    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []

    def send_otp_email(self, to_email: str, otp_code: str, expiry_minutes: int = 5) -> bool:
        self.sent_emails.append({
            "to": to_email,
            "otp_code": otp_code,
            "expiry_minutes": expiry_minutes,
        })
        logger.info(f"[MOCK EMAIL] OTP sent to {to_email} (Expiry: {expiry_minutes}m)")
        return True

    def clear(self) -> None:
        self.sent_emails.clear()


class ConsoleEmailProvider(BaseEmailProvider):
    """Console provider for local interactive development."""

    def send_otp_email(self, to_email: str, otp_code: str, expiry_minutes: int = 5) -> bool:
        print(f"\n{'='*50}\n[GMAIL OTP SIMULATOR] To: {to_email}\nCode: {otp_code} (Expires in {expiry_minutes} min)\n{'='*50}\n")
        return True


def mask_email(email: str) -> str:
    """Mask email address for safe diagnostic logging without leaking full PII."""
    if not email or "@" not in email:
        return "***"
    try:
        parts = email.split("@")
        name, domain = parts[0], parts[1]
        if len(name) <= 2:
            masked_name = name[0] + "***"
        else:
            masked_name = name[:2] + "***" + name[-1]
        return f"{masked_name}@{domain}"
    except Exception:
        return "***"


class SMTPProvider(BaseEmailProvider):
    """Production Gmail SMTP Email Provider supporting STARTTLS (587) and SSL (465)."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        use_tls: Optional[bool] = None,
    ):
        self.host = host or auth_config.SMTP_HOST
        self.port = port or auth_config.SMTP_PORT
        self.username = username or auth_config.SMTP_USERNAME
        raw_pass = password or auth_config.SMTP_PASSWORD
        if raw_pass:
            raw_pass = raw_pass.strip().strip('"').strip("'")
            if len(raw_pass.replace(" ", "")) == 16:
                raw_pass = raw_pass.replace(" ", "")
        self.password = raw_pass
        self.from_email = from_email or auth_config.SMTP_FROM
        self.from_name = from_name or auth_config.SMTP_FROM_NAME
        self.use_tls = use_tls if use_tls is not None else auth_config.SMTP_USE_TLS

    def _render_html_template(self, otp_code: str, expiry_minutes: int) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your NetraGraph login code</title>
</head>
<body style="margin:0;padding:0;background-color:#f9fafb;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f9fafb;padding:40px 0;">
  <tr>
    <td align="center">
      <table width="520" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff;border-radius:8px;border:1px solid #e5e7eb;">
        <tr>
          <td style="padding:32px 40px 0 40px;text-align:left;">
            <p style="margin:0;font-size:14px;color:#6b7280;">NetraGraph Security</p>
            <h1 style="margin:16px 0 0 0;font-size:22px;color:#111827;font-weight:600;">Your login code</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 40px;">
            <p style="margin:0 0 16px 0;font-size:15px;color:#374151;line-height:1.6;">
              Use the code below to sign in to NetraGraph. This code expires in <strong>{expiry_minutes} minutes</strong>.
            </p>
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td style="background-color:#f3f4f6;border-radius:6px;padding:20px;text-align:center;">
                  <span style="font-size:36px;font-weight:700;letter-spacing:10px;color:#111827;font-family:Courier New,monospace;">{otp_code}</span>
                </td>
              </tr>
            </table>
            <p style="margin:20px 0 0 0;font-size:13px;color:#6b7280;line-height:1.6;">
              If you did not request this code, you can safely ignore this email. Do not share this code with anyone.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 40px 24px 40px;border-top:1px solid #f3f4f6;">
            <p style="margin:0;font-size:12px;color:#9ca3af;">NetraGraph &mdash; National Cyber Crime Investigation Platform</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""

    def send_otp_email(self, to_email: str, otp_code: str, expiry_minutes: int = 5) -> bool:
        if not self.username or not self.password:
            logger.warning("[SMTP CONFIG WARNING] SMTP credentials not configured in environment. Defaulting to Mock fallback.")
            return True

        from_addr = self.from_email
        if "gmail.com" in self.host and self.username:
            from_addr = self.username

        masked_to = mask_email(to_email)
        masked_from = mask_email(from_addr)
        masked_user = mask_email(self.username)

        logger.info(f"[SMTP DISPATCH INITIATED] Host={self.host}:{self.port}, TLS={self.use_tls}, From={masked_from}, To={masked_to}")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your NetraGraph login code"
        msg["From"] = f"{self.from_name} <{from_addr}>"
        msg["To"] = to_email
        msg["Reply-To"] = from_addr
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="gmail.com")
        msg["X-Mailer"] = "NetraGraph Security System"

        text_content = (
            f"Hello,\n\n"
            f"You requested a login code for NetraGraph.\n\n"
            f"Your one-time login code is:\n\n"
            f"  {otp_code}\n\n"
            f"This code expires in {expiry_minutes} minutes and can only be used once.\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"-- NetraGraph Security Team"
        )
        html_content = self._render_html_template(otp_code, expiry_minutes)

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            if self.port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=15) as server:
                    logger.info(f"[SMTP SSL CONNECTED] Connected to {self.host}:{self.port}")
                    server.login(self.username, self.password)
                    logger.info(f"[SMTP AUTH SUCCESS] Authenticated as {masked_user}")
                    server.sendmail(from_addr, [to_email], msg.as_string())
                    logger.info(f"[SMTP MESSAGE ACCEPTED] Message accepted by {self.host} for recipient {masked_to}")
            else:
                with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                    server.ehlo()
                    if self.use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                        server.ehlo()
                        logger.info(f"[SMTP TLS ESTABLISHED] Upgraded TLS channel with {self.host}:{self.port}")
                    server.login(self.username, self.password)
                    logger.info(f"[SMTP AUTH SUCCESS] Authenticated as {masked_user}")
                    server.sendmail(from_addr, [to_email], msg.as_string())
                    logger.info(f"[SMTP MESSAGE ACCEPTED] Message accepted by {self.host} for recipient {masked_to}")
            logger.info(f"[SMTP DELIVERY SUCCESS] Delivered OTP email to {masked_to}")
            return True
        except Exception as e:
            sanitized_err = str(e)
            if self.password:
                sanitized_err = sanitized_err.replace(self.password, "[REDACTED]")
            logger.error(f"[SMTP DELIVERY FAILURE] Host={self.host}:{self.port}, To={masked_to}, Error={type(e).__name__}: {sanitized_err}")
            return False


# Singleton Provider Instances
mock_email_provider = MockEmailProvider()
console_email_provider = ConsoleEmailProvider()
smtp_email_provider = SMTPProvider()


def get_email_provider() -> BaseEmailProvider:
    """Factory function for active email provider."""
    import os
    provider_type = os.getenv("EMAIL_PROVIDER", auth_config.EMAIL_PROVIDER).lower()
    smtp_user = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or auth_config.SMTP_USERNAME
    smtp_pass = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS") or auth_config.SMTP_PASSWORD

    if provider_type == "mock":
        return mock_email_provider
    elif provider_type == "console":
        return console_email_provider
    elif provider_type == "smtp":
        if not smtp_user or not smtp_pass:
            logger.warning(
                f"[SMTP CONFIG WARNING] EMAIL_PROVIDER=smtp is configured, but SMTP_USERNAME or SMTP_PASSWORD is not set in .env. "
                f"Falling back to MockEmailProvider. (UserPresent={bool(smtp_user)}, PasswordPresent={bool(smtp_pass)})"
            )
            return mock_email_provider
        return SMTPProvider(
            host=os.getenv("SMTP_HOST", auth_config.SMTP_HOST),
            port=int(os.getenv("SMTP_PORT", str(auth_config.SMTP_PORT))),
            username=smtp_user,
            password=smtp_pass,
            from_email=os.getenv("SMTP_FROM", auth_config.SMTP_FROM),
            from_name=os.getenv("SMTP_FROM_NAME", auth_config.SMTP_FROM_NAME),
            use_tls=os.getenv("SMTP_USE_TLS", str(auth_config.SMTP_USE_TLS)).lower() in ("true", "1", "t"),
        )
    return mock_email_provider
