"""Thread-safe in-memory registry for investigator-created timeline markers."""
from __future__ import annotations

import threading
from typing import Dict, List, Optional
from .config import ProvenanceType, TimelineEventType
from .models import (
    InvestigationTimelineEvent,
    InvestigatorMarkerRequest,
)
from .provenance import compute_timeline_event_identity


class InvestigatorMarkerRegistry:
    """
    Thread-safe storage for human investigator timeline markers.
    Preserves user notes and annotations without implying automated algorithmic detection.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._markers: Dict[str, List[InvestigationTimelineEvent]] = {}  # network_id -> events

    def add_marker(
        self,
        network_id: str,
        request: InvestigatorMarkerRequest,
    ) -> InvestigationTimelineEvent:
        """Create and register an investigator timeline marker."""
        with self._lock:
            details = {
                "title": request.title,
                "note": request.note,
                "actor_id": request.actor_id,
                "is_investigator_created": True,
            }
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.INVESTIGATION_MARKER.value,
                timestamp=request.timestamp,
                entity_ids=request.linked_entities,
                edge_ids=request.linked_edges,
                source_reference=f"Analyst:{request.actor_id}",
                details=details,
            )
            event = InvestigationTimelineEvent(
                event_id=ev_id,
                event_fingerprint=fp,
                event_type=TimelineEventType.INVESTIGATION_MARKER,
                timestamp=request.timestamp,
                network_id=network_id,
                entity_ids=request.linked_entities,
                edge_ids=request.linked_edges,
                provenance_type=ProvenanceType.SOURCE,
                source_reference=f"Analyst:{request.actor_id}",
                confidence=1.0,
                description=f"Investigator Marker: {request.title} — {request.note}",
                details=details,
            )

            if network_id not in self._markers:
                self._markers[network_id] = []
            self._markers[network_id].append(event)
            return event

    def get_markers(self, network_id: str) -> List[InvestigationTimelineEvent]:
        """Retrieve all registered markers for a network."""
        with self._lock:
            return list(self._markers.get(network_id, []))

    def clear(self, network_id: Optional[str] = None) -> None:
        """Clear markers for a specific network or all networks (useful for testing)."""
        with self._lock:
            if network_id:
                self._markers.pop(network_id, None)
            else:
                self._markers.clear()


investigator_marker_registry = InvestigatorMarkerRegistry()
