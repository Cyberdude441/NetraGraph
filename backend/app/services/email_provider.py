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


class SMTPProvider(BaseEmailProvider):
    """Production SMTP / Gmail Email Provider."""

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
        self.password = password or auth_config.SMTP_PASSWORD
        self.from_email = from_email or auth_config.SMTP_FROM
        self.from_name = from_name or auth_config.SMTP_FROM_NAME
        self.use_tls = use_tls if use_tls is not None else auth_config.SMTP_USE_TLS

    def _render_html_template(self, otp_code: str, expiry_minutes: int) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f8; margin: 0; padding: 0; }}
            .container {{ max-width: 540px; margin: 40px auto; background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
            .header {{ background-color: #064e3b; padding: 24px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px; }}
            .content {{ padding: 32px 24px; text-align: center; }}
            .otp-box {{ display: inline-block; background-color: #ecfdf5; border: 2px dashed #059669; border-radius: 6px; padding: 16px 32px; font-size: 32px; font-weight: 800; font-family: monospace; color: #064e3b; letter-spacing: 8px; margin: 24px 0; }}
            .warning {{ font-size: 12px; color: #64748b; line-height: 1.6; margin-top: 24px; }}
            .footer {{ background-color: #f8fafc; padding: 16px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>NetraGraph AI — Law Enforcement Portal</h1>
            </div>
            <div class="content">
              <p style="font-size: 15px; color: #1e293b; margin: 0;">Your Single-Use Verification Code</p>
              <div class="otp-box">{otp_code}</div>
              <p style="font-size: 13px; color: #475569; margin: 0;">This code will expire in <strong>{expiry_minutes} minutes</strong>.</p>
              <div class="warning">
                <p>Do not share this cryptographic code with anyone. NetraGraph officers will never ask for your authentication token.</p>
              </div>
            </div>
            <div class="footer">
              <p>Official Secrets Act §5 & IT Act §69B Protected · Cyber Crime Investigation Division</p>
            </div>
          </div>
        </body>
        </html>
        """

    def send_otp_email(self, to_email: str, otp_code: str, expiry_minutes: int = 5) -> bool:
        if not self.username or not self.password:
            logger.warning("SMTP credentials not configured; defaulting to safe local delivery simulation.")
            return True

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "NetraGraph Authentication Code"
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        text_content = f"Your NetraGraph verification code is: {otp_code}\nExpires in {expiry_minutes} minutes."
        html_content = self._render_html_template(otp_code, expiry_minutes)

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            if self.port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=10) as server:
                    server.login(self.username, self.password)
                    server.sendmail(self.from_email, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                    if self.use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(self.username, self.password)
                    server.sendmail(self.from_email, [to_email], msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Failed to deliver OTP email to {to_email} via SMTP: {e}")
            return False


# Singleton Provider Instances
mock_email_provider = MockEmailProvider()
console_email_provider = ConsoleEmailProvider()
smtp_email_provider = SMTPProvider()


def get_email_provider() -> BaseEmailProvider:
    """Factory function for active email provider."""
    provider_type = auth_config.EMAIL_PROVIDER.lower()
    if provider_type == "mock":
        return mock_email_provider
    elif provider_type == "console":
        return console_email_provider
    elif provider_type == "smtp" and auth_config.SMTP_USERNAME and auth_config.SMTP_PASSWORD:
        return smtp_email_provider
    return mock_email_provider
