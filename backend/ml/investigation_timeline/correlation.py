"""Read-only correlation engine integrating Phase 13, Threat Fusion, and DT-GNN intelligence signals."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..emerging_threat.events import EmergingThreatEvent
from ..emerging_threat.service import emerging_threat_service
from .config import ProvenanceType, TimelineEventType
from .models import InvestigationTimelineEvent
from .provenance import compute_timeline_event_identity


class SignalCorrelationEngine:
    """
    Correlates external ML and rule-based intelligence signals with chronological graph events.
    Strictly preserves missing signal state (never backfills zero) and enforces non-causal language.
    """

    def __init__(self, correlation_window_seconds: float = 300.0):
        self.correlation_window = correlation_window_seconds

    def correlate_phase13_events(
        self,
        network_id: str,
        start_time: float,
        end_time: float,
        external_events: Optional[List[EmergingThreatEvent]] = None,
    ) -> List[InvestigationTimelineEvent]:
        """
        Query Phase 13 early-warning events and map them into the chronological investigation timeline.
        Does not mutate Phase 13 event state.
        """
        if external_events is not None:
            source_events = external_events
        else:
            try:
                source_events = emerging_threat_service.list_events(network_id=network_id)
            except Exception:
                source_events = []

        timeline_events: List[InvestigationTimelineEvent] = []
        for ev in source_events:
            ev_time = float(ev.detected_at)
            # Check if within window (with tolerance)
            if start_time - self.correlation_window <= ev_time <= end_time + self.correlation_window:
                ev_type_str = ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type)
                severity_str = ev.severity.value if hasattr(ev.severity, "value") else str(ev.severity)
                desc = (
                    f"Emerging threat early-warning alert '{ev_type_str}' observed "
                    f"during the observation window (score: {ev.early_warning_score:.3f}, "
                    f"severity: {severity_str}). Temporal correlation only; does not establish causality."
                )
                ev_id, fp = compute_timeline_event_identity(
                    network_id=network_id,
                    event_type=TimelineEventType.EMERGING_THREAT.value,
                    timestamp=ev_time,
                    entity_ids=ev.entity_ids,
                    edge_ids=[],
                    source_reference=f"Phase13:{ev.event_id}",
                    details={
                        "phase13_event_id": ev.event_id,
                        "early_warning_score": ev.early_warning_score,
                        "severity": severity_str,
                        "trajectory_type": (
                            ev.trajectory.type.value if hasattr(ev.trajectory, "type") and hasattr(ev.trajectory.type, "value")
                            else getattr(ev.trajectory, "type", None)
                        ) if hasattr(ev, "trajectory") else None,
                    },
                )
                timeline_events.append(
                    InvestigationTimelineEvent(
                        event_id=ev_id,
                        event_fingerprint=fp,
                        event_type=TimelineEventType.EMERGING_THREAT,
                        timestamp=ev_time,
                        network_id=network_id,
                        entity_ids=ev.entity_ids,
                        edge_ids=[],
                        provenance_type=ProvenanceType.CORRELATED,
                        source_reference=f"Phase13:{ev.event_id}",
                        confidence=ev.confidence_score,
                        linked_intelligence_ids=[ev.event_id],
                        description=desc,
                        details={
                            "phase13_fingerprint": ev.event_fingerprint,
                            "severity": severity_str,
                            "early_warning_score": ev.early_warning_score,
                        },
                    )
                )

        return timeline_events

    def correlate_dt_gnn_signals(
        self,
        network_id: str,
        dt_gnn_signals: Optional[List[Dict[str, Any]]],
    ) -> List[InvestigationTimelineEvent]:
        """
        Ingest and correlate DT-GNN signals.
        If signals are None or missing, records them explicitly as missing without zero-fabrication.
        """
        if not dt_gnn_signals:
            return []

        events: List[InvestigationTimelineEvent] = []
        for sig in dt_gnn_signals:
            ts = float(sig.get("timestamp", 0.0))
            anomaly_score = sig.get("anomaly_score")
            if anomaly_score is None:
                # Explicit missing signal: do NOT fabricate 0.0
                desc = "DT-GNN neural signal recorded as unavailable for this temporal slice."
                is_missing = True
            else:
                desc = (
                    f"Dynamic Temporal GNN neural signal observed during this temporal slice "
                    f"(anomaly score: {float(anomaly_score):.3f})."
                )
                is_missing = False

            entity_ids = sig.get("entity_ids", [])
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.DT_GNN_SIGNAL.value,
                timestamp=ts,
                entity_ids=entity_ids,
                edge_ids=[],
                source_reference="DT-GNN-Inference",
                details={"is_missing": is_missing, "anomaly_score": anomaly_score},
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.DT_GNN_SIGNAL,
                    timestamp=ts,
                    network_id=network_id,
                    entity_ids=entity_ids,
                    edge_ids=[],
                    provenance_type=ProvenanceType.CORRELATED,
                    source_reference="DT-GNN-Inference",
                    confidence=sig.get("confidence"),
                    linked_intelligence_ids=sig.get("linked_ids", []),
                    description=desc,
                    details={"is_missing": is_missing, "anomaly_score": anomaly_score},
                )
            )

        return events

    def correlate_threat_fusion_signals(
        self,
        network_id: str,
        fusion_signals: Optional[List[Dict[str, Any]]],
    ) -> List[InvestigationTimelineEvent]:
        """
        Ingest and correlate Threat Fusion signals.
        Preserves missing values without zero-fabrication.
        """
        if not fusion_signals:
            return []

        events: List[InvestigationTimelineEvent] = []
        for sig in fusion_signals:
            ts = float(sig.get("timestamp", 0.0))
            risk_score = sig.get("risk_score")
            if risk_score is None:
                desc = "Threat Fusion signal recorded as unavailable for this observation slice."
                is_missing = True
            else:
                desc = (
                    f"Neuro-symbolic Threat Fusion assessment observed during this observation slice "
                    f"(risk score: {float(risk_score):.3f}, severity: {sig.get('severity', 'UNKNOWN')})."
                )
                is_missing = False

            entity_ids = sig.get("entity_ids", [])
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.THREAT_FUSION_SIGNAL.value,
                timestamp=ts,
                entity_ids=entity_ids,
                edge_ids=[],
                source_reference="ThreatFusionService",
                details={"is_missing": is_missing, "risk_score": risk_score},
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.THREAT_FUSION_SIGNAL,
                    timestamp=ts,
                    network_id=network_id,
                    entity_ids=entity_ids,
                    edge_ids=[],
                    provenance_type=ProvenanceType.CORRELATED,
                    source_reference="ThreatFusionService",
                    confidence=sig.get("confidence"),
                    linked_intelligence_ids=sig.get("linked_ids", []),
                    description=desc,
                    details={"is_missing": is_missing, "risk_score": risk_score},
                )
            )

        return events
