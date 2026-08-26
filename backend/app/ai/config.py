"""
NetraGraph AI - AI Configuration Module
Securely manages AI provider settings and credentials.
"""

import os
from pathlib import Path
from typing import Any, Dict


def load_env_files():
    """Loads .env from backend directory and root directory."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        for env_path in [
            Path(__file__).resolve().parent.parent.parent / ".env",
            Path(__file__).resolve().parent.parent.parent.parent / ".env",
            Path.cwd() / ".env",
            Path.cwd() / "backend" / ".env",
        ]:
            if env_path.exists():
                try:
                    for line in env_path.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("\"'")
                            if k and v and k not in os.environ:
                                os.environ[k] = v
                except Exception:
                    pass
        return

    for env_path in [
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
        Path.cwd() / ".env",
        Path.cwd() / "backend" / ".env",
    ]:
        if env_path.exists():
            load_dotenv(env_path, override=True)


load_env_files()


class AIConfig:
    """Central AI Configuration Settings."""

    @property
    def NVIDIA_API_KEY(self) -> str:
        load_env_files()
        return os.getenv("NVIDIA_NEMOTRON_API_KEY", "")

    @property
    def NVIDIA_BASE_URL(self) -> str:
        return os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    @property
    def NVIDIA_MODEL(self) -> str:
        return os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")

    @property
    def GEMINI_API_KEY(self) -> str:
        load_env_files()
        return os.getenv("GOOGLE_GEMINI_API_KEY", "")

    @property
    def GEMINI_BASE_URL(self) -> str:
        return os.getenv(
            "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
        )

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    _default_provider: str = "nemotron"

    @property
    def DEFAULT_PROVIDER(self) -> str:
        env_val = os.getenv("DEFAULT_AI_PROVIDER")
        if env_val:
            return env_val.lower().strip()
        return self._default_provider

    def is_nemotron_configured(self) -> bool:
        """Returns True if Nemotron API key is present."""
        key = self.NVIDIA_API_KEY
        return bool(key and len(key.strip()) > 5)

    def is_gemini_configured(self) -> bool:
        """Returns True if Gemini API key is present."""
        key = self.GEMINI_API_KEY
        return bool(key and len(key.strip()) > 5)

    def get_provider_status(self) -> Dict[str, Any]:
        """Returns safe provider connection statuses without revealing credentials."""
        return {
            "default_provider": self.DEFAULT_PROVIDER,
            "providers": {
                "nemotron": {
                    "name": "NVIDIA Nemotron",
                    "status": "connected" if self.is_nemotron_configured() else "not_connected",
                    "model": self.NVIDIA_MODEL,
                    "capabilities": [
                        "entity_extraction",
                        "relationship_analysis",
                        "risk_assessment",
                        "investigation_summary",
                    ],
                },
                "gemini": {
                    "name": "Google Gemini",
                    "status": "connected" if self.is_gemini_configured() else "not_connected",
                    "model": self.GEMINI_MODEL,
                    "capabilities": [
                        "summarize_report",
                        "analyze_document",
                        "generate_report",
                    ],
                },
            },
        }

    def set_default_provider(self, provider: str) -> str:
        """Sets the active default provider."""
        p = provider.lower().strip()
        if p in ["nemotron", "gemini"]:
            self._default_provider = p
            os.environ["DEFAULT_AI_PROVIDER"] = p
            return self._default_provider
        return self.DEFAULT_PROVIDER


config = AIConfig()
