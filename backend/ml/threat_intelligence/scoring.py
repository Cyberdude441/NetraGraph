"""Independent multi-dimensional confidence assessment and temporal decay evaluation."""
from __future__ import annotations

import time
from typing import Optional, Tuple

from .config import IOCReputation, MatchMethod, SourceTier, TemporalDecayPolicy
from .models import ConfidenceProfile


class ThreatScoringEngine:
    """Computes independent confidence dimensions and temporal decay."""

    def __init__(self, decay_policy: Optional[TemporalDecayPolicy] = None):
        self.decay_policy = decay_policy or TemporalDecayPolicy()

    def map_reputation_to_base_threat(self, reputation: IOCReputation) -> float:
        """Deterministically maps reputation tier into a baseline threat relevance score [0, 1]."""
        if reputation == IOCReputation.MALICIOUS:
            return 0.92
        elif reputation == IOCReputation.SUSPICIOUS:
            return 0.60
        elif reputation == IOCReputation.BENIGN:
            return 0.05
        return 0.35  # UNKNOWN baseline

    def compute_match_confidence(self, match_method: MatchMethod) -> float:
        """Assigns deterministic match confidence based on algorithm fidelity."""
        if match_method in (MatchMethod.EXACT, MatchMethod.HASH_EXACT):
            return 1.0
        elif match_method == MatchMethod.DOMAIN_HIERARCHY:
            return 0.90
        elif match_method in (MatchMethod.CIDR_SUBNET, MatchMethod.PHONE_E164, MatchMethod.BANK_EXACT):
            return 0.85
        elif match_method == MatchMethod.FUZZY_ALIAS:
            return 0.65
        return 0.50

    def compute_extraction_confidence(self, method: str) -> float:
        """Assigns confidence to the technical extraction methodology."""
        m_upper = method.upper()
        if "REGEX" in m_upper or "PARSER" in m_upper or "STIX" in m_upper:
            return 0.98
        elif "HEURISTIC" in m_upper:
            return 0.80
        elif "NLP" in m_upper or "LLM" in m_upper:
            return 0.70
        return 0.85

    def evaluate_profile(
        self,
        source_reliability: Optional[float],
        content_confidence: Optional[float],
        extraction_method: str,
        match_method: MatchMethod,
        last_seen_timestamp: Optional[float],
        reputation: IOCReputation,
        reference_time: Optional[float] = None,
    ) -> Tuple[ConfidenceProfile, float, bool, Optional[str]]:
        """
        Builds the 6-dimensional ConfidenceProfile and computes effective decayed threat relevance.
        
        CRITICAL ARCHITECTURAL INVARIANT:
        Dimensions remain independent. Missing timestamps or unrated confidences are NOT fabricated.
        
        Returns:
          (confidence_profile, effective_threat_relevance, is_stale, stale_warning)
        """
        now = reference_time if reference_time is not None else time.time()
        ext_conf = self.compute_extraction_confidence(extraction_method)
        match_conf = self.compute_match_confidence(match_method)
        base_threat = self.map_reputation_to_base_threat(reputation)

        temp_conf: Optional[float] = None
        is_stale: bool = False
        stale_warning: Optional[str] = None
        decay_factor: float = 1.0

        if last_seen_timestamp is not None and last_seen_timestamp > 0.0:
            elapsed = max(0.0, now - last_seen_timestamp)
            decay_factor = self.decay_policy.calculate_decay(elapsed)
            temp_conf = decay_factor

            days_elapsed = elapsed / 86400.0
            if days_elapsed > self.decay_policy.max_stale_days:
                is_stale = True
                stale_warning = (
                    f"Intelligence is stale: last observed {days_elapsed:.1f} days ago "
                    f"(exceeds {self.decay_policy.max_stale_days:.0f}-day policy threshold)."
                )
        else:
            # Timestamp absent — DO NOT fabricate temporal confidence
            temp_conf = None

        effective_threat = round(base_threat * decay_factor, 4)

        profile = ConfidenceProfile(
            source_reliability=source_reliability,
            content_confidence=content_confidence,
            extraction_confidence=ext_conf,
            entity_match_confidence=match_conf,
            temporal_confidence=temp_conf,
            threat_relevance=effective_threat,
        )

        return profile, effective_threat, is_stale, stale_warning
