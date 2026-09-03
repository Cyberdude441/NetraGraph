"""Deterministic, auditable threat fusion engine with conflict detection and temporal decay."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .config import ThreatFusionConfig
from .evidence import EvidenceChain, EvidenceItem, EvidenceOrientation
from .provenance import ProvenanceTracker
from .signals import SignalSeverity, SignalSource, ThreatSignal, calculate_severity


class ThreatFusionEngine:
    """Combines heterogeneous intelligence signals into an auditable threat assessment."""

    def __init__(self, config: Optional[ThreatFusionConfig] = None):
        self.config = config or ThreatFusionConfig()

    def calculate_temporal_weight(
        self,
        base_weight: float,
        signal_timestamp: float,
        ref_timestamp: float,
    ) -> float:
        """Applies recency decay to signal weights while maintaining an auditable minimum floor."""
        decay_cfg = self.config.temporal_decay
        if not decay_cfg.enabled or signal_timestamp <= 0 or ref_timestamp <= 0:
            return max(0.01, base_weight)

        elapsed_seconds = max(0.0, ref_timestamp - signal_timestamp)
        half_life = max(1.0, decay_cfg.half_life_seconds)

        # Decay factor = (1/2) ** (elapsed / half_life)
        decay_factor = math.pow(0.5, elapsed_seconds / half_life)
        effective_factor = max(decay_cfg.min_weight_floor, decay_factor)

        return max(0.001, base_weight * effective_factor)

    def get_source_base_weight(self, source: SignalSource) -> float:
        """Looks up configured source category weight."""
        sw = self.config.source_weights
        weights_map = {
            SignalSource.MODEL_A_E: sw.model_a_e,
            SignalSource.DT_GNN: sw.dt_gnn,
            SignalSource.GRAPH_CENTRALITY: sw.graph_centrality,
            SignalSource.GRAPH_ANOMALY: sw.graph_anomaly,
            SignalSource.COMMUNITY: sw.community,
            SignalSource.TEMPORAL_BEHAVIOR: sw.temporal_behavior,
            SignalSource.SYMBOLIC_RULE: sw.symbolic_rule,
            SignalSource.EXTERNAL: 0.7,
        }
        return weights_map.get(source, 1.0)

    def fuse_signals(
        self,
        signals: List[ThreatSignal],
        target_id: str,
        evaluation_timestamp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Fuses a collection of threat signals into an auditable assessment dictionary."""
        valid_signals = [s for s in signals if not s.is_missing and s.score is not None]
        missing_signals = [s for s in signals if s.is_missing or s.score is None]

        # Reference timestamp for temporal decay
        if evaluation_timestamp is not None and evaluation_timestamp > 0:
            ref_time = evaluation_timestamp
        elif valid_signals:
            ref_time = max(s.timestamp for s in valid_signals)
        else:
            ref_time = 0.0

        if not valid_signals:
            # Handle empty / purely missing signal set safely
            return {
                "risk_score": 0.0,
                "confidence_score": 0.0,
                "disagreement_score": 0.0,
                "severity": SignalSeverity.LOW,
                "supporting_signals": [],
                "contradicting_signals": [],
                "missing_signals": missing_signals,
                "evidence_chain": EvidenceChain(target_id=target_id),
                "weights_used": {},
            }

        # 1. Compute effective decayed weights per signal
        decayed_weights: List[float] = []
        scores: List[float] = []
        confidences: List[float] = []

        for s in valid_signals:
            base_w = self.get_source_base_weight(s.source)
            eff_w = self.calculate_temporal_weight(base_w, s.timestamp, ref_time)
            decayed_weights.append(eff_w)
            scores.append(s.score)
            confidences.append(s.confidence)

        total_weight = sum(decayed_weights)
        if total_weight <= 0:
            total_weight = 1.0

        # 2. Weighted Fused Risk Score
        weighted_score_sum = sum(w * s for w, s in zip(decayed_weights, scores))
        fused_risk = max(0.0, min(1.0, weighted_score_sum / total_weight))

        # 3. Conflict / Disagreement Metric
        # Weighted standard deviation of signal scores
        weighted_variance = sum(
            w * ((s - fused_risk) ** 2) for w, s in zip(decayed_weights, scores)
        ) / total_weight
        disagreement_score = max(0.0, min(1.0, math.sqrt(weighted_variance)))

        # 4. Independent Confidence Modeling
        # Weighted base confidence
        base_confidence = sum(w * c for w, c in zip(decayed_weights, confidences)) / total_weight

        # Penalize confidence if signals exhibit severe contradiction
        penalty_slope = self.config.disagreement.confidence_penalty_slope
        conflict_penalty = min(0.60, penalty_slope * disagreement_score)

        # Completeness multiplier (more distinct sources = higher trust)
        distinct_sources = len({s.source for s in valid_signals})
        completeness = min(1.0, 0.70 + 0.10 * distinct_sources)

        final_confidence = base_confidence * (1.0 - conflict_penalty) * completeness
        final_confidence = max(
            self.config.disagreement.min_confidence_floor,
            min(1.0, final_confidence),
        )

        # 5. Partition Supporting vs Contradicting Signals & Build Evidence Chain
        sup_thresh = self.config.supporting_signal_threshold
        supporting_signals: List[ThreatSignal] = []
        contradicting_signals: List[ThreatSignal] = []
        evidence_chain = EvidenceChain(target_id=target_id)

        for s, eff_w in zip(valid_signals, decayed_weights):
            if s.score >= sup_thresh:
                supporting_signals.append(s)
                orientation = EvidenceOrientation.SUPPORTING
                evidence_chain.supporting_evidence.append(
                    EvidenceItem(
                        signal_id=s.signal_id,
                        provenance_id=s.provenance_id or "",
                        source=s.source,
                        orientation=orientation,
                        weight=round(eff_w, 4),
                        raw_score=s.score,
                        confidence=s.confidence,
                        narrative_fact=s.explanation,
                        timestamp=s.timestamp,
                    )
                )
            else:
                contradicting_signals.append(s)
                orientation = EvidenceOrientation.CONTRADICTING
                evidence_chain.contradicting_evidence.append(
                    EvidenceItem(
                        signal_id=s.signal_id,
                        provenance_id=s.provenance_id or "",
                        source=s.source,
                        orientation=orientation,
                        weight=round(eff_w, 4),
                        raw_score=s.score,
                        confidence=s.confidence,
                        narrative_fact=s.explanation,
                        timestamp=s.timestamp,
                    )
                )

        # 6. Severity Mapping
        severity = calculate_severity(fused_risk)

        return {
            "risk_score": round(fused_risk, 4),
            "confidence_score": round(final_confidence, 4),
            "disagreement_score": round(disagreement_score, 4),
            "severity": severity,
            "supporting_signals": supporting_signals,
            "contradicting_signals": contradicting_signals,
            "missing_signals": missing_signals,
            "evidence_chain": evidence_chain,
            "weights_used": {s.signal_id: round(w, 4) for s, w in zip(valid_signals, decayed_weights)},
        }
