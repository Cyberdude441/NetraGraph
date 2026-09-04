"""Multi-source conflict detection, discrepancy auditing, and confidence penalty logic."""
from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple

from .config import ConflictPolicy, IOCReputation, IOCType
from .models import ThreatConflictRecord, ThreatIndicator


class ConflictManager:
    """Detects and audits contradictory intelligence without overwriting observations."""

    def __init__(self, conflict_policy: Optional[ConflictPolicy] = None):
        self.policy = conflict_policy or ConflictPolicy()
        self._conflicts: Dict[str, ThreatConflictRecord] = {}

    def compute_conflict_id(self, indicator_id: str, source_a: str, source_b: str) -> str:
        """Computes deterministic conflict identifier."""
        sorted_sources = sorted([source_a, source_b])
        composite = f"{indicator_id}|{sorted_sources[0]}|{sorted_sources[1]}"
        digest = hashlib.sha256(composite.encode("utf-8")).hexdigest()[:16]
        return f"cnf:{digest}"

    def check_and_register_conflict(
        self,
        new_indicator: ThreatIndicator,
        existing_indicators: List[ThreatIndicator],
    ) -> Tuple[bool, Optional[ThreatConflictRecord], float]:
        """
        Compares incoming indicator against existing indicators sharing the same canonical value.
        
        CRITICAL ARCHITECTURAL INVARIANT:
        Neither observation is overwritten. If a conflict is discovered (e.g. MALICIOUS vs BENIGN),
        both records are preserved and linked to a ThreatConflictRecord.
        
        Returns:
          (has_conflict, conflict_record, penalty_factor)
        """
        for existing in existing_indicators:
            # Check for direct reputation opposition
            is_new_malicious = new_indicator.reputation in (IOCReputation.MALICIOUS, IOCReputation.SUSPICIOUS)
            is_exist_clean = existing.reputation == IOCReputation.BENIGN

            is_new_clean = new_indicator.reputation == IOCReputation.BENIGN
            is_exist_malicious = existing.reputation in (IOCReputation.MALICIOUS, IOCReputation.SUSPICIOUS)

            if (is_new_malicious and is_exist_clean) or (is_new_clean and is_exist_malicious):
                conflict_id = self.compute_conflict_id(
                    new_indicator.indicator_id,
                    new_indicator.source_id,
                    existing.source_id,
                )

                supporting = new_indicator if is_new_malicious else existing
                contradicting = existing if is_new_malicious else new_indicator

                explanation = (
                    f"Reputation discrepancy: Source '{supporting.source_name}' asserts {supporting.reputation.value} "
                    f"while Source '{contradicting.source_name}' asserts {contradicting.reputation.value}."
                )

                conflict_record = ThreatConflictRecord(
                    conflict_id=conflict_id,
                    indicator_id=new_indicator.indicator_id,
                    canonical_value=new_indicator.canonical_value,
                    ioc_type=new_indicator.ioc_type,
                    supporting_observation={
                        "source_id": supporting.source_id,
                        "source_name": supporting.source_name,
                        "reputation": supporting.reputation.value,
                        "confidence": supporting.confidence_profile.content_confidence,
                        "timestamp": supporting.ingestion_timestamp,
                        "provenance_id": supporting.provenance_id,
                    },
                    contradicting_observation={
                        "source_id": contradicting.source_id,
                        "source_name": contradicting.source_name,
                        "reputation": contradicting.reputation.value,
                        "confidence": contradicting.confidence_profile.content_confidence,
                        "timestamp": contradicting.ingestion_timestamp,
                        "provenance_id": contradicting.provenance_id,
                    },
                    conflict_status="UNRESOLVED_DISCREPANCY",
                    explanation=explanation,
                    penalty_applied=self.policy.conflict_confidence_penalty,
                )

                self._conflicts[conflict_id] = conflict_record
                return True, conflict_record, self.policy.conflict_confidence_penalty

        return False, None, 0.0

    def get_conflict(self, conflict_id: str) -> Optional[ThreatConflictRecord]:
        return self._conflicts.get(conflict_id)

    def list_conflicts(self) -> List[ThreatConflictRecord]:
        return sorted(list(self._conflicts.values()), key=lambda c: c.timestamp, reverse=True)

    @property
    def total_conflicts(self) -> int:
        return len(self._conflicts)
