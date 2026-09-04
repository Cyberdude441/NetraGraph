"""Configuration, constants, enumerations, and safety limits for Threat Intelligence & OSINT Fusion."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

THREAT_INTEL_ENGINE_VERSION: str = "1.0.0"
THREAT_INTEL_SCHEMA_VERSION: str = "1.0.0"
SOURCE_TRUST_POLICY_VERSION: str = "1.0.0"

MANDATORY_NON_CAUSAL_DISCLAIMER: str = (
    "External threat intelligence and OSINT are analytical decision-support inputs. "
    "They do not constitute definitive proof of culpability, criminal intent, or guilt under law."
)


class IOCType(str, Enum):
    """Supported technical indicator types."""
    IPV4 = "IPv4"
    IPV6 = "IPv6"
    DOMAIN = "Domain"
    URL = "URL"
    SHA256 = "SHA256"
    MD5 = "MD5"
    PHONE = "Phone"
    BANK_ACCOUNT = "BankAccount"
    OTHER = "Other"


class SourceTier(str, Enum):
    """Institutional credibility classification tiers for external intelligence feeds."""
    TIER_1_CERT_LE = "TIER_1_CERT_LE"                      # National CERT / Law Enforcement (e.g. CERT-In, NCTX)
    TIER_2_ESTABLISHED_PROVIDER = "TIER_2_ESTABLISHED"      # Established security vendors (e.g. VirusTotal, AbuseIPDB, OpenPhish)
    TIER_3_COMMERCIAL_FEED = "TIER_3_COMMERCIAL"            # Commercial CTI telemetry
    TIER_4_COMMUNITY_OSINT = "TIER_4_COMMUNITY"            # Community / Crowdsourced OSINT (e.g. AlienVault OTX, URLhaus)
    TIER_5_UNVERIFIED = "TIER_5_UNVERIFIED"                # Unverified / scrape / darknet dump


class IOCReputation(str, Enum):
    """Assessed threat posture of an external indicator."""
    MALICIOUS = "MALICIOUS"
    SUSPICIOUS = "SUSPICIOUS"
    BENIGN = "BENIGN"
    UNKNOWN = "UNKNOWN"


class MatchMethod(str, Enum):
    """Deterministic algorithm used to link a case entity to an external indicator."""
    EXACT = "EXACT"
    CIDR_SUBNET = "CIDR_SUBNET"
    DOMAIN_HIERARCHY = "DOMAIN_HIERARCHY"
    HASH_EXACT = "HASH_EXACT"
    PHONE_E164 = "PHONE_E164"
    BANK_EXACT = "BANK_EXACT"
    FUZZY_ALIAS = "FUZZY_ALIAS"


class ResolutionStatus(str, Enum):
    """Entity-resolution confidence state aligned with investigation_graph_service."""
    VERIFIED = "VERIFIED"
    PROBABLE = "PROBABLE"
    UNRESOLVED = "UNRESOLVED"


class ReviewStatus(str, Enum):
    """Human-in-the-loop investigator gate status."""
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    STAGED = "STAGED"


@dataclass
class SourceTrustPolicy:
    """Configurable administrative policy for source reliability ratings."""
    policy_version: str = SOURCE_TRUST_POLICY_VERSION
    tier_defaults: Dict[SourceTier, float] = field(
        default_factory=lambda: {
            SourceTier.TIER_1_CERT_LE: 0.95,
            SourceTier.TIER_2_ESTABLISHED_PROVIDER: 0.85,
            SourceTier.TIER_3_COMMERCIAL_FEED: 0.80,
            SourceTier.TIER_4_COMMUNITY_OSINT: 0.65,
            SourceTier.TIER_5_UNVERIFIED: 0.30,
        }
    )
    source_overrides: Dict[str, float] = field(default_factory=dict)
    override_audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def get_reliability(self, source_name: str, tier: SourceTier) -> float:
        """Returns effective reliability, checking administrative overrides first."""
        norm_name = source_name.strip().lower()
        if norm_name in self.source_overrides:
            return max(0.0, min(1.0, self.source_overrides[norm_name]))
        return self.tier_defaults.get(tier, 0.50)

    def set_override(self, source_name: str, score: float, admin_user: str, reason: str) -> None:
        """Registers an audited administrative reliability override."""
        norm_name = source_name.strip().lower()
        bounded_score = max(0.0, min(1.0, float(score)))
        self.source_overrides[norm_name] = bounded_score
        self.override_audit_trail.append({
            "source_name": source_name,
            "score": bounded_score,
            "admin_user": admin_user,
            "reason": reason,
        })


@dataclass
class TemporalDecayPolicy:
    """Policy governing temporal decay of indicators based on time elapsed since last observed."""
    half_life_days: float = 30.0
    decay_lambda: float = field(init=False)
    max_stale_days: float = 90.0
    temporal_decay_enabled: bool = True

    def __post_init__(self):
        # lambda = ln(2) / (half_life in seconds)
        self.decay_lambda = math.log(2.0) / (self.half_life_days * 86400.0)

    def calculate_decay(self, elapsed_seconds: float) -> float:
        """Calculates exponential decay multiplier e^(-lambda * dt) bounded to [0.05, 1.0]."""
        if not self.temporal_decay_enabled or elapsed_seconds <= 0.0:
            return 1.0
        decay = math.exp(-self.decay_lambda * elapsed_seconds)
        return max(0.05, min(1.0, decay))


@dataclass
class ConflictPolicy:
    """Policy for handling contradictory multi-source intelligence."""
    conflict_confidence_penalty: float = 0.50
    flag_conflicts_prominently: bool = True


@dataclass
class SafetyLimitsConfig:
    """Strict resource bounds guarding against DoS, memory bloat, and compute exhaustion."""
    max_payload_bytes: int = 10 * 1024 * 1024       # 10 MB
    max_indicators_per_batch: int = 5000            # Max items in single ingest batch
    max_candidate_entities: int = 1000              # Max case entities correlated per request
    max_correlation_results: int = 200              # Max returned correlation matches
    max_conflict_records: int = 500                 # Max stored conflict history items
    max_provenance_dag_depth: int = 10              # Max lineage traversal depth
    max_timeout_seconds: float = 5.0                # Max synchronous execution timeout


@dataclass
class ThreatIntelConfig:
    """Master configuration for the Threat Intelligence / OSINT Engine."""
    engine_version: str = THREAT_INTEL_ENGINE_VERSION
    schema_version: str = THREAT_INTEL_SCHEMA_VERSION
    trust_policy: SourceTrustPolicy = field(default_factory=SourceTrustPolicy)
    decay_policy: TemporalDecayPolicy = field(default_factory=TemporalDecayPolicy)
    conflict_policy: ConflictPolicy = field(default_factory=ConflictPolicy)
    safety_limits: SafetyLimitsConfig = field(default_factory=SafetyLimitsConfig)
