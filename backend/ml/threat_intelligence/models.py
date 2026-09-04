"""Pydantic contracts and immutable data representations for Threat Intelligence & OSINT Fusion."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .config import (
    MANDATORY_NON_CAUSAL_DISCLAIMER,
    IOCReputation,
    IOCType,
    MatchMethod,
    ResolutionStatus,
    ReviewStatus,
    SourceTier,
    THREAT_INTEL_ENGINE_VERSION,
    THREAT_INTEL_SCHEMA_VERSION,
)


class ConfidenceProfile(BaseModel):
    """
    Multi-dimensional, uncollapsed confidence model for intelligence evidence.
    
    CRITICAL ARCHITECTURAL INVARIANT:
    These 6 dimensions represent distinct epistemological properties of evidence and
    MUST NEVER be silently collapsed into a single lossy scalar in storage or analysis.
    """
    source_reliability: Optional[float] = Field(
        default=None,
        description="Institutional trustworthiness of the reporting source [0.0, 1.0]. None if unrated."
    )
    content_confidence: Optional[float] = Field(
        default=None,
        description="Source's asserted confidence in the indicator's malice/association [0.0, 1.0]."
    )
    extraction_confidence: Optional[float] = Field(
        default=None,
        description="Fidelity of the parsing/extraction pipeline (e.g. 1.0 for regex, 0.70 for NLP) [0.0, 1.0]."
    )
    entity_match_confidence: Optional[float] = Field(
        default=None,
        description="Correlation match strength between case entity and external indicator [0.0, 1.0]."
    )
    temporal_confidence: Optional[float] = Field(
        default=None,
        description="Confidence accounting for time elapsed since last verified observation [0.0, 1.0]."
    )
    threat_relevance: Optional[float] = Field(
        default=None,
        description="Current operational risk relevance after temporal decay [0.0, 1.0]."
    )

    def to_adapter_scalar(self) -> float:
        """
        Explicit adapter method for downstream consumers (e.g. ThreatSignal) that strictly require a single scalar.
        
        ADAPTER SEMANTICS DOCUMENTATION:
        Computes the weighted geometric product of available non-None dimensions.
        This scalar is strictly an interoperability projection; it DOES NOT replace the full multi-dimensional profile.
        """
        factors: List[float] = []
        if self.source_reliability is not None:
            factors.append(max(0.01, min(1.0, self.source_reliability)))
        if self.content_confidence is not None:
            factors.append(max(0.01, min(1.0, self.content_confidence)))
        if self.entity_match_confidence is not None:
            factors.append(max(0.01, min(1.0, self.entity_match_confidence)))
        if self.temporal_confidence is not None:
            factors.append(max(0.01, min(1.0, self.temporal_confidence)))

        if not factors:
            return 0.50  # Neutral baseline if all dimensions are unrated

        # Geometric mean
        prod = 1.0
        for f in factors:
            prod *= f
        return round(prod ** (1.0 / len(factors)), 4)


class ThreatIndicator(BaseModel):
    """An external threat intelligence indicator with immutable observation lineage."""
    indicator_id: str = Field(..., description="Deterministic canonical ID (e.g. ioc:ipv4:103.145.22.18)")
    indicator_value: str = Field(..., description="Original raw indicator representation")
    canonical_value: str = Field(..., description="Normalized canonical indicator representation")
    ioc_type: IOCType = Field(..., description="Categorized indicator type")
    threat_actor: Optional[str] = Field(default=None, description="Reported attributing syndicate/actor")
    category: str = Field(default="Unspecified Threat Indicator", description="Threat category")
    reputation: IOCReputation = Field(default=IOCReputation.SUSPICIOUS, description="Threat reputation tier")
    confidence_profile: ConfidenceProfile = Field(default_factory=ConfidenceProfile)
    first_seen_timestamp: Optional[float] = Field(default=None, description="Earliest reported observation epoch")
    last_seen_timestamp: Optional[float] = Field(default=None, description="Most recent reported observation epoch")
    publication_timestamp: Optional[float] = Field(default=None, description="External report publication epoch")
    ingestion_timestamp: float = Field(default_factory=lambda: time.time(), description="NetraGraph ingest epoch")
    source_id: str = Field(..., description="Deterministic ID of originating source")
    source_name: str = Field(..., description="Human-readable feed/source name")
    source_tier: SourceTier = Field(default=SourceTier.TIER_4_COMMUNITY_OSINT)
    source_record_id: Optional[str] = Field(default=None, description="Upstream reference ID in source database")
    raw_payload_sha256: str = Field(..., description="Cryptographic SHA-256 of raw source payload")
    provenance_id: str = Field(..., description="Deterministic provenance identity")
    associated_malware: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    has_conflict: bool = Field(default=False, description="Flagged if contradictory intelligence exists across feeds")
    conflict_ids: List[str] = Field(default_factory=list)


class CandidateCorrelation(BaseModel):
    """Correlation finding linking a case entity to an external threat indicator."""
    correlation_id: str = Field(..., description="Deterministic correlation identifier")
    case_id: str = Field(..., description="Target investigation case ID")
    entity_id: str = Field(..., description="Target case entity ID")
    entity_type: str = Field(..., description="Case entity type")
    entity_value: str = Field(..., description="Case entity raw value (masked if PII)")
    indicator_id: str = Field(..., description="Correlated threat indicator ID")
    indicator_value: str = Field(..., description="Correlated threat indicator value")
    ioc_type: IOCType = Field(..., description="Indicator type")
    match_method: MatchMethod = Field(..., description="Algorithm employed for match")
    entity_match_confidence: float = Field(..., ge=0.0, le=1.0)
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.PROBABLE)
    confidence_profile: ConfidenceProfile = Field(default_factory=ConfidenceProfile)
    effective_threat_relevance: float = Field(..., ge=0.0, le=1.0)
    provenance_id: str = Field(...)
    explanation: str = Field(...)
    review_status: ReviewStatus = Field(default=ReviewStatus.REVIEW_REQUIRED)
    is_stale: bool = Field(default=False)
    stale_warning: Optional[str] = Field(default=None)
    created_at: float = Field(default_factory=lambda: time.time())
    has_conflict: bool = Field(default=False)
    mandatory_disclaimer: str = Field(default=MANDATORY_NON_CAUSAL_DISCLAIMER)


class ThreatIntelProvenanceRecord(BaseModel):
    """Immutable forensic provenance record tracking the lineage of external intelligence."""
    provenance_id: str = Field(..., description="Deterministic provenance ID")
    source_id: str = Field(...)
    source_name: str = Field(...)
    source_type: str = Field(default="external_cti_feed")
    source_record_id: Optional[str] = Field(default=None)
    raw_payload_sha256: str = Field(..., description="Cryptographic SHA-256 bitstream checksum")
    observation_timestamp: Optional[float] = Field(default=None)
    publication_timestamp: Optional[float] = Field(default=None)
    ingestion_timestamp: float = Field(default_factory=lambda: time.time())
    transformation_history: List[str] = Field(default_factory=list)
    parent_provenance_ids: List[str] = Field(default_factory=list)
    parser_version: str = Field(default=THREAT_INTEL_SCHEMA_VERSION)
    engine_version: str = Field(default=THREAT_INTEL_ENGINE_VERSION)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ThreatConflictRecord(BaseModel):
    """Audit record capturing contradictory assessments between external sources."""
    conflict_id: str = Field(..., description="Deterministic conflict identifier")
    indicator_id: str = Field(...)
    canonical_value: str = Field(...)
    ioc_type: IOCType = Field(...)
    supporting_observation: Dict[str, Any] = Field(..., description="Details of malicious/threat observation")
    contradicting_observation: Dict[str, Any] = Field(..., description="Details of clean/benign observation")
    conflict_status: str = Field(default="UNRESOLVED_DISCREPANCY")
    explanation: str = Field(...)
    penalty_applied: float = Field(default=0.0)
    timestamp: float = Field(default_factory=lambda: time.time())


class ReviewDecision(BaseModel):
    """Investigator review gate action on a candidate CTI correlation."""
    correlation_id: str = Field(...)
    decision: ReviewStatus = Field(..., description="ACCEPTED or REJECTED")
    analyst_id: str = Field(..., description="Reviewing officer identifier")
    justification: str = Field(..., description="Forensic rationale for decision")
    timestamp: float = Field(default_factory=lambda: time.time())
    mandatory_disclaimer: str = Field(default=MANDATORY_NON_CAUSAL_DISCLAIMER)
