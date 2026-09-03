"""Temporal event density and interaction burst detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .config import TemporalBurstConfig
from .snapshots import GraphSnapshot


@dataclass
class TemporalBurstResult:
    """Outcome of interaction frequency and burst clustering evaluation."""
    target_id: str
    burst_detected: bool = False
    burst_score: float = 0.0                 # Bounded [0, 1] burst intensity
    max_event_count_in_window: int = 0
    window_duration_seconds: float = 300.0
    participating_entity_count: int = 0
    participating_entities: List[str] = field(default_factory=list)
    narrative: str = ""


class TemporalBurstDetector:
    """Detects high-velocity interaction bursts and synchronized entity activity."""

    def __init__(self, config: Optional[TemporalBurstConfig] = None):
        self.config = config or TemporalBurstConfig()

    def analyze_bursts(
        self,
        target_id: str,
        snapshots: List[GraphSnapshot],
    ) -> TemporalBurstResult:
        """Evaluates interaction timestamps across snapshots to identify burst density."""
        # Collect all edge events with positive timestamps
        events: List[Tuple[float, str, str]] = []
        for s in snapshots:
            for e in s.edges:
                if e.timestamp > 0:
                    events.append((e.timestamp, e.source_id, e.target_id))

        if not events:
            return TemporalBurstResult(
                target_id=target_id,
                narrative="Insufficient timestamped interactions to detect temporal bursts.",
            )

        events.sort(key=lambda x: x[0])
        win_sec = self.config.burst_window_seconds
        min_events = self.config.min_events_for_burst

        max_count = 0
        burst_entities: Set[str] = set()

        # Sliding window over events
        n = len(events)
        for i in range(n):
            start_t = events[i][0]
            current_window_entities: Set[str] = set()
            count = 0
            for j in range(i, n):
                if events[j][0] - start_t <= win_sec:
                    count += 1
                    current_window_entities.add(events[j][1])
                    current_window_entities.add(events[j][2])
                else:
                    break
            if count > max_count:
                max_count = count
                burst_entities = current_window_entities

        burst_detected = bool(max_count >= min_events)
        burst_score = 0.0
        if burst_detected:
            # Scaled burst score
            raw_score = 0.50 + 0.50 * min(1.0, (max_count - min_events) / float(min_events * 2))
            burst_score = round(max(0.0, min(1.0, raw_score)), 4)
            narrative = (
                f"High-frequency burst detected: {max_count} interactions involving "
                f"{len(burst_entities)} entities occurred within a {win_sec:.0f}-second window."
            )
        else:
            burst_score = round(min(0.35, max_count / float(min_events * 2)), 4)
            narrative = f"Interaction frequency remained below burst threshold (max {max_count} events/window)."

        return TemporalBurstResult(
            target_id=target_id,
            burst_detected=burst_detected,
            burst_score=burst_score,
            max_event_count_in_window=max_count,
            window_duration_seconds=win_sec,
            participating_entity_count=len(burst_entities),
            participating_entities=sorted(list(burst_entities)),
            narrative=narrative,
        )
