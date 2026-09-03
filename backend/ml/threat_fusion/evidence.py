"""Structured evidence representations and bidirectional evidence chains."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .signals import SignalSource, ThreatSignal


class EvidenceOrientation(str, Enum):
    SUPPORTING = "SUPPORTING"        # Evidence concurring with the elevated risk assessment
    CONTRADICTING = "CONTRADICTING"  # Evidence indicating low risk or opposing elevated risk
    NEUTRAL = "NEUTRAL"              # Inconclusive or baseline background signal


@dataclass
class EvidenceItem:
    """Individual evidence artifact linking an analytical signal to human-understandable findings."""
    evidence_id: str = field(default_factory=lambda: f"EVD-{uuid.uuid4().hex[:10].upper()}")
    signal_id: str = ""
    provenance_id: str = ""
    source: SignalSource = SignalSource.MODEL_A_E
    orientation: EvidenceOrientation = EvidenceOrientation.NEUTRAL
    weight: float = 1.0              # Final decayed effective weight in fusion
    raw_score: float = 0.50          # Original normalized signal score
    confidence: float = 0.80
    narrative_fact: str = ""         # Pure analytical fact (non-causal)
    timestamp: float = 0.0


@dataclass
class EvidenceChain:
    """Bidirectional evidence chain answering 'What caused this score?' and 'What contradicts it?'."""
    target_id: str
    supporting_evidence: List[EvidenceItem] = field(default_factory=list)
    contradicting_evidence: List[EvidenceItem] = field(default_factory=list)
    neutral_evidence: List[EvidenceItem] = field(default_factory=list)

    @property
    def total_evidence_count(self) -> int:
        return (
            len(self.supporting_evidence)
            + len(self.contradicting_evidence)
            + len(self.neutral_evidence)
        )

    @property
    def supporting_count(self) -> int:
        return len(self.supporting_evidence)

    @property
    def contradicting_count(self) -> int:
        return len(self.contradicting_evidence)

    def get_top_supporting(self, k: int = 5) -> List[EvidenceItem]:
        """Returns top-k supporting evidence sorted by effective contribution weight descending."""
        return sorted(self.supporting_evidence, key=lambda e: e.weight * e.raw_score, reverse=True)[:k]

    def get_top_contradicting(self, k: int = 5) -> List[EvidenceItem]:
        """Returns top-k contradicting evidence sorted by effective contribution weight descending."""
        # For contradicting evidence, lower score = stronger contradiction against elevated risk
        return sorted(self.contradicting_evidence, key=lambda e: e.weight * (1.0 - e.raw_score), reverse=True)[:k]
