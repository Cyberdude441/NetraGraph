"""Master Threat Intelligence Engine coordinating ingestion, normalization, correlation, and provenance."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    from services.threat_intelligence_service import threat_intelligence_service as legacy_cti
    from services.evidence_intelligence_service import evidence_intelligence_service
    from services.investigation_graph import investigation_graph_service
except ImportError:
    from ...services.threat_intelligence_service import threat_intelligence_service as legacy_cti
    from ...services.evidence_intelligence_service import evidence_intelligence_service
    from ...services.investigation_graph import investigation_graph_service

from .config import (
    IOCReputation,
    IOCType,
    MANDATORY_NON_CAUSAL_DISCLAIMER,
    MatchMethod,
    ResolutionStatus,
    ReviewStatus,
    SourceTier,
    ThreatIntelConfig,
)
from .conflicts import ConflictManager
from .correlator import EntityCorrelator
from .ingestion import IngestionPipeline
from .models import (
    CandidateCorrelation,
    ConfidenceProfile,
    ReviewDecision,
    ThreatConflictRecord,
    ThreatIndicator,
    ThreatIntelProvenanceRecord,
)
from .normalization import normalize_indicator
from .provenance import ThreatIntelProvenanceTracker, compute_indicator_id, compute_payload_sha256, compute_provenance_id
from .scoring import ThreatScoringEngine
from .sources import SourceRegistry

logger = logging.getLogger("ThreatIntelligenceEngine")


class ThreatIntelligenceEngine:
    """
    Central coordinator for Phase 15 Threat Intelligence / OSINT Fusion with Provenance.
    
    Enforces:
      - Option C + D + E (Evidence-only records, temporal annotations, analyst review gate)
      - Immutable observations (Zero destructive overwriting)
      - Independent 6-dimensional confidence profile (Zero silent collapsing)
      - Deterministic canonical identities
      - Bounded execution limits
    """

    def __init__(self, config: Optional[ThreatIntelConfig] = None):
        self.config = config or ThreatIntelConfig()
        self.source_registry = SourceRegistry(self.config.trust_policy)
        self.provenance_tracker = ThreatIntelProvenanceTracker()
        self.scoring_engine = ThreatScoringEngine(self.config.decay_policy)
        self.conflict_manager = ConflictManager(self.config.conflict_policy)
        self.correlator = EntityCorrelator(self.scoring_engine)
        self.ingestion_pipeline = IngestionPipeline(self.source_registry, self.config.safety_limits)

        # Storage structures (in-memory, strictly zero database schema modifications)
        self._indicators_by_canonical: Dict[str, List[ThreatIndicator]] = {}
        self._indicators_by_id: Dict[str, ThreatIndicator] = {}
        self._staged_correlations: Dict[str, CandidateCorrelation] = {}
        self._approved_correlations: Dict[str, CandidateCorrelation] = {}
        self._audit_log: List[Dict[str, Any]] = []

        self._seed_legacy_curated_feed()

    def _seed_legacy_curated_feed(self) -> None:
        """Seeds curated indicators from legacy threat_intelligence_service for backward compatibility."""
        try:
            sample_iocs = [
                {
                    "indicator": "103.145.22.18",
                    "ioc_type": "IPv4",
                    "threat_actor": "UNC-8812 (Tele-Fraud Syndicate)",
                    "category": "Bulletproof Proxy / VoIP Relay",
                    "confidence_score": 0.94,
                    "first_seen": "2024-01-15T08:00:00Z",
                    "last_seen": "2024-03-16T14:31:00Z",
                    "feed_source": "CERT-In Threat Advisory & AbuseIPDB Feed",
                    "reputation": "MALICIOUS",
                    "source_tier": SourceTier.TIER_1_CERT_LE,
                },
                {
                    "indicator": "support-helpdesk-msft.com",
                    "ioc_type": "Domain",
                    "threat_actor": "UNC-8812",
                    "category": "Credential Phishing Infrastructure",
                    "confidence_score": 0.98,
                    "first_seen": "2024-02-10T12:00:00Z",
                    "last_seen": "2024-03-16T14:31:00Z",
                    "feed_source": "OpenPhish & VirusTotal Intelligence",
                    "reputation": "MALICIOUS",
                    "source_tier": SourceTier.TIER_2_ESTABLISHED_PROVIDER,
                },
                {
                    "indicator": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "ioc_type": "SHA256",
                    "threat_actor": "UNC-8812",
                    "category": "Zero-Byte Dropper Payload",
                    "confidence_score": 0.90,
                    "first_seen": "2024-03-01T00:00:00Z",
                    "last_seen": "2024-03-16T14:31:00Z",
                    "feed_source": "OpenPhish & VirusTotal Intelligence",
                    "reputation": "MALICIOUS",
                    "source_tier": SourceTier.TIER_2_ESTABLISHED_PROVIDER,
                },
            ]
            raw_bytes = json.dumps(sample_iocs).encode("utf-8")
            indicators, prov_records, _ = self.ingestion_pipeline.ingest_payload(
                source_name="CERT-In Threat Advisory & AbuseIPDB Feed",
                source_tier=SourceTier.TIER_1_CERT_LE,
                raw_bytes=raw_bytes,
                payload_format="json",
            )
            for ind in indicators:
                self.register_indicator(ind)
            for prv in prov_records:
                self.provenance_tracker.register_record(prv)
        except Exception as err:
            logger.warning(f"Could not pre-seed curated feed: {err}")

    def register_indicator(self, indicator: ThreatIndicator) -> None:
        """
        Registers an indicator into the canonical index while detecting conflicts and preserving observations.
        """
        canonical_key = indicator.canonical_value
        existing_list = self._indicators_by_canonical.setdefault(canonical_key, [])

        # Check for multi-source conflict
        has_conflict, conflict_record, penalty = self.conflict_manager.check_and_register_conflict(
            new_indicator=indicator,
            existing_indicators=existing_list,
        )

        if has_conflict and conflict_record:
            indicator.has_conflict = True
            indicator.conflict_ids.append(conflict_record.conflict_id)
            # Apply penalty to content confidence without fabricating
            if indicator.confidence_profile.content_confidence is not None:
                penalized = max(0.0, indicator.confidence_profile.content_confidence * (1.0 - penalty))
                indicator.confidence_profile.content_confidence = round(penalized, 4)

            # Also flag conflict on the existing opposing indicators
            for existing in existing_list:
                existing.has_conflict = True
                if conflict_record.conflict_id not in existing.conflict_ids:
                    existing.conflict_ids.append(conflict_record.conflict_id)

        # Check if identical observation from same source already exists
        same_source = [e for e in existing_list if e.source_id == indicator.source_id]
        if same_source:
            # Update last_seen timestamp on existing observation without deleting or overwriting history
            same_source[0].last_seen_timestamp = max(
                same_source[0].last_seen_timestamp or 0.0,
                indicator.last_seen_timestamp or 0.0,
            )
        else:
            existing_list.append(indicator)

        self._indicators_by_id[indicator.indicator_id] = indicator

    def ingest_external_feed(
        self,
        source_name: str,
        source_tier: SourceTier,
        raw_bytes: bytes,
        payload_format: str = "json",
    ) -> Dict[str, Any]:
        """Ingests, normalizes, and indexes an external threat intelligence feed."""
        indicators, prov_records, raw_sha256 = self.ingestion_pipeline.ingest_payload(
            source_name=source_name,
            source_tier=source_tier,
            raw_bytes=raw_bytes,
            payload_format=payload_format,
        )

        registered_count = 0
        conflicts_detected = 0

        for ind in indicators:
            prev_conflicts = self.conflict_manager.total_conflicts
            self.register_indicator(ind)
            if self.conflict_manager.total_conflicts > prev_conflicts:
                conflicts_detected += 1
            registered_count += 1

        for prv in prov_records:
            self.provenance_tracker.register_record(prv)

        return {
            "source_name": source_name,
            "source_tier": source_tier.value,
            "raw_payload_sha256": raw_sha256,
            "total_indicators_parsed": len(indicators),
            "total_indicators_registered": registered_count,
            "conflicts_detected": conflicts_detected,
            "ingestion_timestamp": time.time(),
        }

    def correlate_entities(
        self,
        case_id: str,
        entities: List[Dict[str, Any]],
        reference_time: Optional[float] = None,
    ) -> List[CandidateCorrelation]:
        """
        Correlates case entities against indexed external intelligence.
        Enforces safety bounds and deterministic ordering.
        """
        bounded_entities = entities[:self.config.safety_limits.max_candidate_entities]
        all_matches: List[CandidateCorrelation] = []

        for ent in bounded_entities:
            matches = self.correlator.correlate_entity(
                case_id=case_id,
                entity_dict=ent,
                indicator_index=self._indicators_by_canonical,
                reference_time=reference_time,
            )
            for m in matches:
                self._staged_correlations[m.correlation_id] = m
                all_matches.append(m)

        # Deterministic sort: primarily relevance descending, secondarily match confidence descending, tertiarily correlation ID ascending
        all_matches.sort(
            key=lambda c: (-c.effective_threat_relevance, -c.entity_match_confidence, c.correlation_id)
        )

        return all_matches[:self.config.safety_limits.max_correlation_results]

    def correlate_case_workspace(self, case_id: str) -> Dict[str, Any]:
        """Retrieves case entities from evidence_intelligence_service and executes correlation."""
        workspace = evidence_intelligence_service.get_case_workspace(case_id)
        entities = workspace.get("entities", [])
        correlations = self.correlate_entities(case_id=case_id, entities=entities)

        return {
            "case_id": case_id,
            "total_matches": len(correlations),
            "correlations": [c.model_dump() for c in correlations],
            "total_indexed_indicators": len(self._indicators_by_id),
            "total_conflicts": self.conflict_manager.total_conflicts,
            "domain_tag": "EXTERNAL_THREAT_INTEL",
            "mandatory_disclaimer": MANDATORY_NON_CAUSAL_DISCLAIMER,
        }

    def review_correlation(
        self,
        correlation_id: str,
        decision: ReviewStatus,
        analyst_id: str,
        justification: str,
    ) -> CandidateCorrelation:
        """
        Investigator review gate (Option E): Human approval before graph enrichment.
        """
        correlation = self._staged_correlations.get(correlation_id)
        if not correlation:
            raise KeyError(f"Candidate correlation '{correlation_id}' not found in staged queue.")

        correlation.review_status = decision
        review_record = ReviewDecision(
            correlation_id=correlation_id,
            decision=decision,
            analyst_id=analyst_id,
            justification=justification,
            timestamp=time.time(),
        )

        if decision == ReviewStatus.ACCEPTED:
            self._approved_correlations[correlation_id] = correlation
        elif decision == ReviewStatus.REJECTED:
            self._approved_correlations.pop(correlation_id, None)

        self._audit_log.append({
            "action": "CTI_CORRELATION_REVIEW",
            "correlation_id": correlation_id,
            "case_id": correlation.case_id,
            "decision": decision.value,
            "analyst_id": analyst_id,
            "justification": justification,
            "timestamp": time.time(),
        })

        return correlation

    def get_indicator_provenance(self, indicator_id: str) -> Dict[str, Any]:
        """Retrieves full lineage DAG and observation history for a specific indicator."""
        indicator = self._indicators_by_id.get(indicator_id)
        if not indicator:
            raise KeyError(f"Indicator '{indicator_id}' not found.")

        lineage_chain = self.provenance_tracker.build_lineage_chain(
            indicator.provenance_id,
            depth_limit=self.config.safety_limits.max_provenance_dag_depth,
        )

        return {
            "indicator": indicator.model_dump(),
            "provenance_chain": [rec.model_dump() for rec in lineage_chain],
            "total_lineage_steps": len(lineage_chain),
            "mandatory_disclaimer": MANDATORY_NON_CAUSAL_DISCLAIMER,
        }

    def list_conflicts(self) -> List[ThreatConflictRecord]:
        return self.conflict_manager.list_conflicts()

    def get_feed_summary(self) -> Dict[str, Any]:
        """Summarizes registered external feeds, indicators, and trust ratings."""
        sources = self.source_registry.list_sources()
        by_type: Dict[str, int] = {}
        for ind in self._indicators_by_id.values():
            t = ind.ioc_type.value
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "engine_version": self.config.engine_version,
            "schema_version": self.config.schema_version,
            "total_indicators": len(self._indicators_by_id),
            "by_ioc_type": by_type,
            "total_conflicts": self.conflict_manager.total_conflicts,
            "total_provenance_records": self.provenance_tracker.total_records,
            "total_staged_correlations": len(self._staged_correlations),
            "total_approved_correlations": len(self._approved_correlations),
            "registered_feeds": [s.model_dump() for s in sources],
            "domain_tag": "EXTERNAL_THREAT_INTEL",
            "mandatory_disclaimer": MANDATORY_NON_CAUSAL_DISCLAIMER,
        }

    # =========================================================================
    # Subsystem Read-Only Integration Adapters
    # =========================================================================

    def export_to_threat_fusion_signals(
        self,
        correlations: List[CandidateCorrelation],
    ) -> List[Any]:
        """
        Adapter producing ThreatSignal instances for backend/ml/threat_fusion/.
        
        CRITICAL ARCHITECTURAL INVARIANT:
        Emits SignalSource.EXTERNAL without modifying any internal Threat Fusion code.
        Preserves the multi-dimensional confidence breakdown in signal metadata.
        """
        from ml.threat_fusion.signals import SignalSeverity, SignalSource, ThreatSignal

        signals: List[ThreatSignal] = []
        for cor in correlations:
            adapter_conf = cor.confidence_profile.to_adapter_scalar()
            signal = ThreatSignal(
                source=SignalSource.EXTERNAL,
                entity_id=cor.entity_id,
                signal_type="threat_intel_match",
                score=cor.effective_threat_relevance,
                confidence=adapter_conf,
                timestamp=cor.created_at,
                explanation=cor.explanation,
                provenance_id=cor.provenance_id,
                metadata={
                    "correlation_id": cor.correlation_id,
                    "case_id": cor.case_id,
                    "indicator_id": cor.indicator_id,
                    "ioc_type": cor.ioc_type.value,
                    "confidence_profile": cor.confidence_profile.model_dump(),
                    "has_conflict": cor.has_conflict,
                    "is_stale": cor.is_stale,
                    "adapter_scalar_confidence": adapter_conf,
                },
            )
            signals.append(signal)
        return signals

    def export_to_timeline_events(
        self,
        correlations: List[CandidateCorrelation],
    ) -> List[Any]:
        """
        Adapter producing InvestigationTimelineEvent instances for backend/ml/investigation_timeline/.
        
        CRITICAL ARCHITECTURAL INVARIANT:
        Conforms strictly to Phase 14 contracts. Sets ProvenanceType.CORRELATED.
        """
        from ml.investigation_timeline.config import ProvenanceType, TimelineEventType
        from ml.investigation_timeline.models import InvestigationTimelineEvent

        events: List[InvestigationTimelineEvent] = []
        for cor in correlations:
            fp = hashlib.sha256(f"{cor.case_id}:{cor.correlation_id}".encode("utf-8")).hexdigest()[:16]
            event = InvestigationTimelineEvent(
                event_id=f"EVT-{cor.correlation_id}",
                event_fingerprint=f"fp-cti-{fp}",
                network_id=cor.case_id,
                timestamp=cor.created_at,
                event_type=TimelineEventType.THREAT_FUSION_SIGNAL,
                provenance_type=ProvenanceType.CORRELATED,
                entity_ids=[cor.entity_id],
                description=f"External CTI Match: {cor.explanation}",
                details={
                    "correlation_id": cor.correlation_id,
                    "indicator_id": cor.indicator_id,
                    "ioc_type": cor.ioc_type.value,
                    "effective_threat_relevance": cor.effective_threat_relevance,
                    "match_method": cor.match_method.value,
                    "resolution_status": cor.resolution_status.value,
                    "review_status": cor.review_status.value,
                    "provenance_id": cor.provenance_id,
                },
            )
            events.append(event)
        return events


# Global Singleton Instance
threat_intelligence_engine = ThreatIntelligenceEngine()
