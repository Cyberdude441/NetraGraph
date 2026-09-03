"""Temporal graph snapshot representations and sequence normalization primitives."""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from ml.dynamic_gnn.data import parse_iso_timestamp
except ImportError:
    def parse_iso_timestamp(ts: Any) -> float:
        if ts is None:
            return 0.0
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts.timestamp()
        if isinstance(ts, str):
            try:
                clean = ts.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except Exception:
                try:
                    return float(ts)
                except ValueError:
                    return 0.0
        return 0.0


@dataclass
class EntitySnapshot:
    """Individual entity state at a specific snapshot point in time."""
    id: str
    entity_type: str = "Unknown"
    risk_score: Optional[float] = None       # Continuous risk in [0, 1] or None if missing
    confidence: float = 0.80
    timestamp: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipSnapshot:
    """Observed interaction or edge between two entities within a snapshot."""
    source_id: str
    target_id: str
    rel_type: str = "ASSOCIATED_WITH"
    weight: float = 1.0
    timestamp: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def edge_key(self) -> Tuple[str, str, str]:
        return (self.source_id, self.target_id, self.rel_type)


@dataclass
class GraphSnapshot:
    """Compact representation of network topology and node states at timestamp t."""
    snapshot_id: str = field(default_factory=lambda: f"SNP-{uuid.uuid4().hex[:10].upper()}")
    timestamp: float = 0.0
    nodes: Dict[str, EntitySnapshot] = field(default_factory=dict)
    edges: List[RelationshipSnapshot] = field(default_factory=list)
    dt_gnn_anomaly_score: Optional[float] = None
    fusion_risk_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def node_ids(self) -> Set[str]:
        return set(self.nodes.keys())

    def edge_set(self) -> Set[Tuple[str, str, str]]:
        return {e.edge_key for e in self.edges}


class TemporalSnapshotSequence:
    """Maintains a verified, chronological sequence of graph snapshots."""

    def __init__(self, snapshots: Optional[List[GraphSnapshot]] = None):
        self.snapshots: List[GraphSnapshot] = []
        if snapshots:
            for s in snapshots:
                self.add_snapshot(s)

    def add_snapshot(self, snapshot: GraphSnapshot) -> None:
        """Adds and normalizes a snapshot, preserving chronological order."""
        # Sanitize timestamp
        if snapshot.timestamp is None or math.isnan(snapshot.timestamp):
            snapshot.timestamp = 0.0
        self.snapshots.append(snapshot)
        self._normalize_and_sort()

    def _normalize_and_sort(self) -> None:
        """Sorts chronologically and disambiguates duplicate timestamps."""
        # Sort by timestamp ascending
        self.snapshots.sort(key=lambda s: s.timestamp)

        # Micro-offset duplicate timestamps by 1ms to maintain strict ordering
        for i in range(1, len(self.snapshots)):
            if self.snapshots[i].timestamp <= self.snapshots[i - 1].timestamp:
                self.snapshots[i].timestamp = self.snapshots[i - 1].timestamp + 0.001

    @property
    def count(self) -> int:
        return len(self.snapshots)

    def is_empty(self) -> bool:
        return len(self.snapshots) == 0

    def get_window_duration_seconds(self) -> float:
        if len(self.snapshots) < 2:
            return 0.0
        return max(0.0, self.snapshots[-1].timestamp - self.snapshots[0].timestamp)

    def get_pairwise_deltas(self) -> List[Tuple[GraphSnapshot, GraphSnapshot, float]]:
        """Yields sequential (prior, current, delta_seconds) tuples."""
        deltas = []
        for i in range(1, len(self.snapshots)):
            prior = self.snapshots[i - 1]
            curr = self.snapshots[i]
            dt = max(0.001, curr.timestamp - prior.timestamp)
            deltas.append((prior, curr, dt))
        return deltas
