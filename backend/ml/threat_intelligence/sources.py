"""External Threat Intelligence source registry and trust tier management."""
from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .config import SourceTier, SourceTrustPolicy


class FeedSourceMetadata(BaseModel):
    """Metadata tracking configuration and health of an external intelligence feed."""
    source_id: str = Field(..., description="Deterministic source ID: src:{sha256[:12]}")
    source_name: str = Field(...)
    source_tier: SourceTier = Field(default=SourceTier.TIER_4_COMMUNITY_OSINT)
    default_reliability: float = Field(default=0.65, ge=0.0, le=1.0)
    description: str = Field(default="")
    is_active: bool = Field(default=True)
    last_sync_timestamp: Optional[float] = Field(default=None)
    total_indicators_ingested: int = Field(default=0)


class SourceRegistry:
    """Manages registered threat intelligence feeds and delegates trust scoring to policy."""

    def __init__(self, trust_policy: Optional[SourceTrustPolicy] = None):
        self.trust_policy = trust_policy or SourceTrustPolicy()
        self._sources: Dict[str, FeedSourceMetadata] = {}
        self._initialize_curated_sources()

    def generate_source_id(self, source_name: str) -> str:
        """Generates deterministic source identifier from source name."""
        norm = source_name.strip().lower()
        digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]
        return f"src:{digest}"

    def _initialize_curated_sources(self) -> None:
        """Seeds curated feeds matching NetraGraph CTI baseline."""
        curated = [
            FeedSourceMetadata(
                source_id=self.generate_source_id("CERT-In Threat Advisory & AbuseIPDB Feed"),
                source_name="CERT-In Threat Advisory & AbuseIPDB Feed",
                source_tier=SourceTier.TIER_1_CERT_LE,
                default_reliability=0.95,
                description="Indian Computer Emergency Response Team verified alerts and AbuseIPDB telemetry",
            ),
            FeedSourceMetadata(
                source_id=self.generate_source_id("National Cyber Crime Threat Exchange (NCTX)"),
                source_name="National Cyber Crime Threat Exchange (NCTX)",
                source_tier=SourceTier.TIER_1_CERT_LE,
                default_reliability=0.95,
                description="MHA I4C official tele-fraud and mule infrastructure registry",
            ),
            FeedSourceMetadata(
                source_id=self.generate_source_id("OpenPhish & VirusTotal Intelligence"),
                source_name="OpenPhish & VirusTotal Intelligence",
                source_tier=SourceTier.TIER_2_ESTABLISHED_PROVIDER,
                default_reliability=0.85,
                description="Phishing URLs, spoof kits, and malware file hash telemetry",
            ),
            FeedSourceMetadata(
                source_id=self.generate_source_id("AlienVault OTX Community Pulse"),
                source_name="AlienVault OTX Community Pulse",
                source_tier=SourceTier.TIER_4_COMMUNITY_OSINT,
                default_reliability=0.65,
                description="Open-source crowdsourced threat intelligence pulses",
            ),
        ]
        for src in curated:
            self._sources[src.source_id] = src

    def register_source(
        self,
        source_name: str,
        source_tier: SourceTier,
        description: str = "",
        default_reliability: Optional[float] = None,
    ) -> FeedSourceMetadata:
        """Registers or updates a threat intelligence source."""
        source_id = self.generate_source_id(source_name)
        if default_reliability is None:
            default_reliability = self.trust_policy.tier_defaults.get(source_tier, 0.50)

        meta = FeedSourceMetadata(
            source_id=source_id,
            source_name=source_name,
            source_tier=source_tier,
            default_reliability=default_reliability,
            description=description,
            is_active=True,
            last_sync_timestamp=time.time(),
        )
        self._sources[source_id] = meta
        return meta

    def get_source(self, source_id: str) -> Optional[FeedSourceMetadata]:
        return self._sources.get(source_id)

    def get_source_by_name(self, source_name: str) -> Optional[FeedSourceMetadata]:
        source_id = self.generate_source_id(source_name)
        return self._sources.get(source_id)

    def get_reliability(self, source_name: str, tier: SourceTier) -> float:
        """Queries the source trust policy for the active reliability rating."""
        return self.trust_policy.get_reliability(source_name, tier)

    def list_sources(self) -> List[FeedSourceMetadata]:
        return sorted(list(self._sources.values()), key=lambda s: s.source_name)
