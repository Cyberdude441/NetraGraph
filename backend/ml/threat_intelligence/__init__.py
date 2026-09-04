"""NetraGraph Phase 15: Threat Intelligence / OSINT Fusion with Provenance.

Provides multi-feed OSINT ingestion, deterministic canonicalization, multi-dimensional
confidence assessment, temporal decay, multi-source conflict auditing, and forensic
lineage tracking without modifying existing protected subsystems or database schemas.
"""
from .config import (
    ConflictPolicy,
    IOCReputation,
    IOCType,
    MANDATORY_NON_CAUSAL_DISCLAIMER,
    MatchMethod,
    ResolutionStatus,
    ReviewStatus,
    SafetyLimitsConfig,
    SOURCE_TRUST_POLICY_VERSION,
    SourceTier,
    SourceTrustPolicy,
    TemporalDecayPolicy,
    THREAT_INTEL_ENGINE_VERSION,
    THREAT_INTEL_SCHEMA_VERSION,
    ThreatIntelConfig,
)
from .conflicts import ConflictManager
from .correlator import EntityCorrelator
from .ingestion import IngestionPipeline, sanitize_text
from .models import (
    CandidateCorrelation,
    ConfidenceProfile,
    ReviewDecision,
    ThreatConflictRecord,
    ThreatIndicator,
    ThreatIntelProvenanceRecord,
)
from .normalization import (
    canonicalize_domain,
    canonicalize_hash,
    canonicalize_ipv4,
    canonicalize_ipv6,
    canonicalize_url,
    defang_text,
    mask_sensitive_identifier,
    normalize_indicator,
)
from .provenance import (
    compute_correlation_id,
    compute_indicator_id,
    compute_payload_sha256,
    compute_provenance_id,
    ThreatIntelProvenanceTracker,
)
from .scoring import ThreatScoringEngine
from .service import ThreatIntelligenceEngine, threat_intelligence_engine
from .sources import FeedSourceMetadata, SourceRegistry

__all__ = [
    "THREAT_INTEL_ENGINE_VERSION",
    "THREAT_INTEL_SCHEMA_VERSION",
    "SOURCE_TRUST_POLICY_VERSION",
    "MANDATORY_NON_CAUSAL_DISCLAIMER",
    "IOCType",
    "SourceTier",
    "IOCReputation",
    "MatchMethod",
    "ResolutionStatus",
    "ReviewStatus",
    "ThreatIntelConfig",
    "SourceTrustPolicy",
    "TemporalDecayPolicy",
    "SafetyLimitsConfig",
    "ConflictPolicy",
    "ConfidenceProfile",
    "ThreatIndicator",
    "CandidateCorrelation",
    "ThreatIntelProvenanceRecord",
    "ThreatConflictRecord",
    "ReviewDecision",
    "FeedSourceMetadata",
    "SourceRegistry",
    "ThreatScoringEngine",
    "ConflictManager",
    "EntityCorrelator",
    "IngestionPipeline",
    "ThreatIntelProvenanceTracker",
    "ThreatIntelligenceEngine",
    "threat_intelligence_engine",
    "normalize_indicator",
    "canonicalize_ipv4",
    "canonicalize_ipv6",
    "canonicalize_domain",
    "canonicalize_url",
    "canonicalize_hash",
    "mask_sensitive_identifier",
    "defang_text",
    "sanitize_text",
    "compute_payload_sha256",
    "compute_provenance_id",
    "compute_indicator_id",
    "compute_correlation_id",
]
