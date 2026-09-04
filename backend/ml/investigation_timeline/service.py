"""Singleton orchestrator service for Investigation Timeline, Graph Replay, and Telemetry."""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional
from prometheus_client import Counter, Histogram

from ..emerging_threat.snapshots import (
    EntitySnapshot,
    GraphSnapshot,
    RelationshipSnapshot,
    TemporalSnapshotSequence,
)
from .config import TimelineConfig
from .markers import investigator_marker_registry
from .models import (
    InvestigationTimelineEvent,
    InvestigatorMarkerRequest,
    ReconstructedGraphState,
    ReplayManifest,
)
from .replay import GraphReplayEngine
from .snapshots import GraphSnapshotReconstructor
from .timeline import InvestigationTimelineBuilder

logger = logging.getLogger("InvestigationTimelineService")

# ============================================================
# Low-Cardinality Prometheus Operational Telemetry
# ============================================================
try:
    from prometheus_client import REGISTRY, Counter, Histogram
    # Check if already registered
    registered_names = set()
    for collector in REGISTRY._collector_to_names.keys():
        for name in REGISTRY._collector_to_names[collector]:
            registered_names.add(name)

    if "netragraph_investigation_timeline_requests_total" not in registered_names:
        TIMELINE_REQUESTS_TOTAL = Counter(
            "netragraph_investigation_timeline_requests_total",
            "Total Investigation Timeline and Replay requests processed",
            ["status"],
        )
    else:
        TIMELINE_REQUESTS_TOTAL = REGISTRY._names_to_collectors.get("netragraph_investigation_timeline_requests_total")

    if "netragraph_investigation_timeline_failures_total" not in registered_names:
        TIMELINE_FAILURES_TOTAL = Counter(
            "netragraph_investigation_timeline_failures_total",
            "Total Investigation Timeline and Replay failures",
            ["reason"],
        )
    else:
        TIMELINE_FAILURES_TOTAL = REGISTRY._names_to_collectors.get("netragraph_investigation_timeline_failures_total")

    if "netragraph_investigation_timeline_duration_seconds" not in registered_names:
        TIMELINE_DURATION_SECONDS = Histogram(
            "netragraph_investigation_timeline_duration_seconds",
            "Latency of Investigation Timeline and Replay operations in seconds",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
    else:
        TIMELINE_DURATION_SECONDS = REGISTRY._names_to_collectors.get("netragraph_investigation_timeline_duration_seconds")

    if "netragraph_investigation_replay_frames_total" not in registered_names:
        REPLAY_FRAMES_TOTAL = Counter(
            "netragraph_investigation_replay_frames_total",
            "Total replay frames generated across investigation networks",
            ["operation"],
        )
    else:
        REPLAY_FRAMES_TOTAL = REGISTRY._names_to_collectors.get("netragraph_investigation_replay_frames_total")

    METRICS_AVAILABLE = True
except Exception:
    METRICS_AVAILABLE = False
    class _DummyMetric:
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def observe(self, *args, **kwargs): pass
    TIMELINE_REQUESTS_TOTAL = _DummyMetric()
    TIMELINE_FAILURES_TOTAL = _DummyMetric()
    TIMELINE_DURATION_SECONDS = _DummyMetric()
    REPLAY_FRAMES_TOTAL = _DummyMetric()


class InvestigationTimelineService:
    """
    Thread-safe singleton orchestration engine for dynamic forensic graph replay
    and investigation timeline synthesis.
    """

    def __init__(self, config: Optional[TimelineConfig] = None):
        self.config = config or TimelineConfig()
        self._lock = threading.RLock()
        self.timeline_builder = InvestigationTimelineBuilder(
            correlation_window_seconds=self.config.correlation_window_seconds
        )
        self.replay_engine = GraphReplayEngine(timeline_builder=self.timeline_builder)

        # In-memory storage for active network sequences and timeline events
        self._network_sequences: Dict[str, TemporalSnapshotSequence] = {}
        self._timeline_events: Dict[str, List[InvestigationTimelineEvent]] = {}
        self._cached_replays: Dict[str, ReplayManifest] = {}

    def validate_safety_limits(
        self,
        sequence: TemporalSnapshotSequence,
    ) -> None:
        """Enforce request bounds to prevent CPU/memory denial-of-service."""
        limits = self.config.safety_limits

        if sequence.count > limits.max_snapshots:
            TIMELINE_FAILURES_TOTAL.labels(reason="snapshot_count_exceeded").inc()
            raise ValueError(
                f"Snapshot count ({sequence.count}) exceeds safety limit ({limits.max_snapshots})."
            )

        total_nodes = sum(len(s.nodes) for s in sequence.snapshots)
        if total_nodes > limits.max_nodes:
            TIMELINE_FAILURES_TOTAL.labels(reason="node_count_exceeded").inc()
            raise ValueError(
                f"Total cumulative node count ({total_nodes}) exceeds safety limit ({limits.max_nodes})."
            )

        total_edges = sum(len(s.edges) for s in sequence.snapshots)
        if total_edges > limits.max_edges:
            TIMELINE_FAILURES_TOTAL.labels(reason="edge_count_exceeded").inc()
            raise ValueError(
                f"Total cumulative edge count ({total_edges}) exceeds safety limit ({limits.max_edges})."
            )

        duration = sequence.get_window_duration_seconds()
        if duration > limits.max_window_duration_seconds:
            TIMELINE_FAILURES_TOTAL.labels(reason="window_duration_exceeded").inc()
            raise ValueError(
                f"Temporal window duration ({duration:.1f}s) exceeds safety limit ({limits.max_window_duration_seconds:.1f}s)."
            )

    def analyze_network_timeline(
        self,
        network_id: str,
        sequence: TemporalSnapshotSequence,
        external_phase13_events: Optional[List[Any]] = None,
        external_dt_gnn_signals: Optional[List[Dict[str, Any]]] = None,
        external_fusion_signals: Optional[List[Dict[str, Any]]] = None,
    ) -> List[InvestigationTimelineEvent]:
        """
        Synthesize chronological timeline events from a snapshot sequence,
        validating safety limits and emitting telemetry.
        """
        start_time = time.perf_counter()
        try:
            self.validate_safety_limits(sequence)

            with self._lock:
                # Store active sequence
                self._network_sequences[network_id] = sequence

                # Build timeline
                events = self.timeline_builder.build_timeline(
                    network_id=network_id,
                    sequence=sequence,
                    external_phase13_events=external_phase13_events,
                    external_dt_gnn_signals=external_dt_gnn_signals,
                    external_fusion_signals=external_fusion_signals,
                )
                self._timeline_events[network_id] = events

            TIMELINE_REQUESTS_TOTAL.labels(status="success").inc()
            return events

        except Exception as e:
            logger.error(f"Error analyzing network timeline for {network_id}: {e}", exc_info=True)
            TIMELINE_REQUESTS_TOTAL.labels(status="error").inc()
            raise
        finally:
            TIMELINE_DURATION_SECONDS.observe(time.perf_counter() - start_time)

    def generate_replay(
        self,
        network_id: str,
        sequence: Optional[TemporalSnapshotSequence] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        external_phase13_events: Optional[List[Any]] = None,
        external_dt_gnn_signals: Optional[List[Dict[str, Any]]] = None,
        external_fusion_signals: Optional[List[Dict[str, Any]]] = None,
    ) -> ReplayManifest:
        """
        Generate a ReplayManifest for the specified network across a time window.
        Uses supplied sequence or retrieves cached sequence for network_id.
        """
        start_perf = time.perf_counter()
        try:
            with self._lock:
                seq = sequence or self._network_sequences.get(network_id)
                if seq is None:
                    seq = TemporalSnapshotSequence([])

                self.validate_safety_limits(seq)

                manifest = self.replay_engine.generate_replay(
                    network_id=network_id,
                    sequence=seq,
                    start_time=start_time,
                    end_time=end_time,
                    external_phase13_events=external_phase13_events,
                    external_dt_gnn_signals=external_dt_gnn_signals,
                    external_fusion_signals=external_fusion_signals,
                )

                if manifest.total_frames > self.config.safety_limits.max_replay_frames:
                    TIMELINE_FAILURES_TOTAL.labels(reason="max_replay_frames_exceeded").inc()
                    raise ValueError(
                        f"Generated replay frames ({manifest.total_frames}) exceeds limit "
                        f"({self.config.safety_limits.max_replay_frames})."
                    )

                self._cached_replays[network_id] = manifest
                self._timeline_events[network_id] = manifest.summary_timeline

            REPLAY_FRAMES_TOTAL.labels(operation="generate_replay").inc(manifest.total_frames)
            TIMELINE_REQUESTS_TOTAL.labels(status="success").inc()
            return manifest

        except Exception as e:
            logger.error(f"Error generating replay for {network_id}: {e}", exc_info=True)
            TIMELINE_REQUESTS_TOTAL.labels(status="error").inc()
            raise
        finally:
            TIMELINE_DURATION_SECONDS.observe(time.perf_counter() - start_perf)

    def reconstruct_snapshot(
        self,
        network_id: str,
        target_timestamp: float,
        sequence: Optional[TemporalSnapshotSequence] = None,
    ) -> ReconstructedGraphState:
        """Reconstruct graph state at target_timestamp from active or provided sequence."""
        with self._lock:
            seq = sequence or self._network_sequences.get(network_id)
            if seq is None:
                seq = TemporalSnapshotSequence([])
            return GraphSnapshotReconstructor.reconstruct_at_timestamp(
                sequence=seq,
                target_timestamp=target_timestamp,
            )

    def get_events(
        self,
        network_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_types: Optional[List[Any]] = None,
        entity_ids: Optional[List[str]] = None,
        provenance_types: Optional[List[Any]] = None,
    ) -> List[InvestigationTimelineEvent]:
        """Retrieve and filter chronological events for a network."""
        with self._lock:
            events = self._timeline_events.get(network_id, [])
            return InvestigationTimelineBuilder.filter_events(
                events=events,
                start_time=start_time,
                end_time=end_time,
                event_types=event_types,
                entity_ids=entity_ids,
                provenance_types=provenance_types,
            )

    def add_marker(
        self,
        network_id: str,
        request: InvestigatorMarkerRequest,
    ) -> InvestigationTimelineEvent:
        """Add an investigator annotation marker to the network timeline."""
        with self._lock:
            marker_event = investigator_marker_registry.add_marker(
                network_id=network_id,
                request=request,
            )
            # Append to timeline if active
            if network_id not in self._timeline_events:
                self._timeline_events[network_id] = []
            self._timeline_events[network_id].append(marker_event)
            self._timeline_events[network_id].sort(
                key=lambda e: (round(e.timestamp, 6), e.event_type.value, e.event_id)
            )
            return marker_event

    def clear(self, network_id: Optional[str] = None) -> None:
        """Clear memory cache (for testing/cleanup)."""
        with self._lock:
            if network_id:
                self._network_sequences.pop(network_id, None)
                self._timeline_events.pop(network_id, None)
                self._cached_replays.pop(network_id, None)
                investigator_marker_registry.clear(network_id)
            else:
                self._network_sequences.clear()
                self._timeline_events.clear()
                self._cached_replays.clear()
                investigator_marker_registry.clear()


investigation_timeline_service = InvestigationTimelineService()
