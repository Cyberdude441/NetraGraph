"""Deterministic investigation timeline construction, aggregation, and filtering engine."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from ..emerging_threat.snapshots import TemporalSnapshotSequence
from .changes import GraphChangeDetector
from .config import ProvenanceType, TimelineEventType
from .correlation import SignalCorrelationEngine
from .markers import investigator_marker_registry
from .models import InvestigationTimelineEvent, ReconstructedGraphState
from .provenance import compute_timeline_event_identity
from .snapshots import GraphSnapshotReconstructor


class InvestigationTimelineBuilder:
    """
    Constructs a deterministic, chronological forensic timeline of all network changes,
    correlated intelligence alerts, and human investigator annotations.
    """

    def __init__(self, correlation_window_seconds: float = 300.0):
        self.correlator = SignalCorrelationEngine(correlation_window_seconds=correlation_window_seconds)

    def build_timeline(
        self,
        network_id: str,
        sequence: TemporalSnapshotSequence,
        external_phase13_events: Optional[List[Any]] = None,
        external_dt_gnn_signals: Optional[List[Dict[str, Any]]] = None,
        external_fusion_signals: Optional[List[Dict[str, Any]]] = None,
    ) -> List[InvestigationTimelineEvent]:
        """
        Synthesize all raw snapshots, derived structural changes, correlated intelligence signals,
        and user markers into a deterministically ordered timeline.
        """
        events: List[InvestigationTimelineEvent] = []

        if sequence.is_empty():
            return events

        snapshots = sequence.snapshots
        reconstructed_states: List[ReconstructedGraphState] = []

        # 1. Base Graph Snapshot Events
        for s in snapshots:
            state = GraphSnapshotReconstructor.reconstruct_from_snapshot(s)
            reconstructed_states.append(state)

            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.GRAPH_SNAPSHOT.value,
                timestamp=s.timestamp,
                entity_ids=sorted(list(s.nodes.keys())),
                edge_ids=[],
                source_reference=f"Snapshot:{s.snapshot_id}",
                details={
                    "snapshot_id": s.snapshot_id,
                    "node_count": len(s.nodes),
                    "edge_count": len(s.edges),
                    "state_hash": state.state_hash,
                },
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.GRAPH_SNAPSHOT,
                    timestamp=s.timestamp,
                    network_id=network_id,
                    entity_ids=sorted(list(s.nodes.keys())),
                    edge_ids=[],
                    provenance_type=ProvenanceType.SOURCE,
                    source_reference=f"Snapshot:{s.snapshot_id}",
                    confidence=1.0,
                    description=(
                        f"Graph snapshot '{s.snapshot_id}' recorded with "
                        f"{len(s.nodes)} node(s) and {len(s.edges)} edge(s)."
                    ),
                    details={
                        "snapshot_id": s.snapshot_id,
                        "state_hash": state.state_hash,
                        "node_count": len(s.nodes),
                        "edge_count": len(s.edges),
                    },
                )
            )

        # 2. Derived Change Events Between Consecutive Snapshots
        for i in range(len(reconstructed_states) - 1):
            prior = reconstructed_states[i]
            curr = reconstructed_states[i + 1]
            changes = GraphChangeDetector.detect_changes(prior, curr)
            change_events = GraphChangeDetector.generate_change_events(network_id, changes)
            events.extend(change_events)

        # 3. Correlated Intelligence Signals (Read-Only)
        t_start = snapshots[0].timestamp
        t_end = snapshots[-1].timestamp

        phase13_events = self.correlator.correlate_phase13_events(
            network_id=network_id,
            start_time=t_start,
            end_time=t_end,
            external_events=external_phase13_events,
        )
        events.extend(phase13_events)

        dt_gnn_events = self.correlator.correlate_dt_gnn_signals(
            network_id=network_id,
            dt_gnn_signals=external_dt_gnn_signals,
        )
        events.extend(dt_gnn_events)

        fusion_events = self.correlator.correlate_threat_fusion_signals(
            network_id=network_id,
            fusion_signals=external_fusion_signals,
        )
        events.extend(fusion_events)

        # 4. Human Investigator Markers
        markers = investigator_marker_registry.get_markers(network_id)
        for m in markers:
            if t_start - 3600.0 <= m.timestamp <= t_end + 3600.0:
                events.append(m)

        # 5. Deterministic Chronological Sorting
        # Invariant: identical inputs produce identical timeline ordering!
        events.sort(key=lambda e: (round(e.timestamp, 6), e.event_type.value, e.event_id))

        return events

    @staticmethod
    def filter_events(
        events: List[InvestigationTimelineEvent],
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: Optional[List[TimelineEventType]] = None,
        entity_ids: Optional[List[str]] = None,
        provenance_types: Optional[List[ProvenanceType]] = None,
    ) -> List[InvestigationTimelineEvent]:
        """Deterministic filtering across timeline events without mutating underlying source data."""
        filtered = list(events)

        if start_time is not None:
            filtered = [e for e in filtered if e.timestamp >= start_time]

        if end_time is not None:
            filtered = [e for e in filtered if e.timestamp <= end_time]

        if event_types:
            type_set = set(event_types)
            filtered = [e for e in filtered if e.event_type in type_set]

        if entity_ids:
            ent_set = set(entity_ids)
            filtered = [e for e in filtered if any(ent in ent_set for ent in e.entity_ids)]

        if provenance_types:
            prov_set = set(provenance_types)
            filtered = [e for e in filtered if e.provenance_type in prov_set]

        return filtered
