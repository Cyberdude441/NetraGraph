"""Deterministic frame-by-frame graph replay engine across selected investigation time windows."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..emerging_threat.snapshots import TemporalSnapshotSequence
from .changes import GraphChangeDetector
from .config import ProvenanceType, ReconstructionAccuracy
from .models import (
    GraphChangeSet,
    InvestigationTimelineEvent,
    ReconstructedGraphState,
    ReplayFrame,
    ReplayManifest,
)
from .provenance import (
    compute_canonical_hash,
    compute_replay_frame_identity,
)
from .snapshots import GraphSnapshotReconstructor
from .timeline import InvestigationTimelineBuilder


class GraphReplayEngine:
    """
    Generates an ordered series of discrete replay frames representing historical network evolution.
    Backend guarantees deterministic state hashes and explicit change sets between consecutive frames.
    """

    def __init__(self, timeline_builder: Optional[InvestigationTimelineBuilder] = None):
        self.timeline_builder = timeline_builder or InvestigationTimelineBuilder()

    def generate_replay(
        self,
        network_id: str,
        sequence: TemporalSnapshotSequence,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        external_phase13_events: Optional[List[Any]] = None,
        external_dt_gnn_signals: Optional[List[Dict[str, Any]]] = None,
        external_fusion_signals: Optional[List[Dict[str, Any]]] = None,
    ) -> ReplayManifest:
        """
        Construct a full ReplayManifest across the specified time window.
        If start_time or end_time are omitted, defaults to the sequence boundaries.
        """
        warnings: List[str] = []

        if sequence.is_empty():
            empty_state = GraphSnapshotReconstructor.reconstruct_at_timestamp(sequence, 0.0)
            replay_payload = {"network_id": network_id, "start_time": 0.0, "end_time": 0.0, "frames": 0}
            replay_id = f"RPL-{compute_canonical_hash(replay_payload)[:12].upper()}"
            return ReplayManifest(
                replay_id=replay_id,
                network_id=network_id,
                start_time=0.0,
                end_time=0.0,
                total_frames=0,
                frames=[],
                summary_timeline=[],
                data_quality_warnings=["Replay requested on empty snapshot sequence."],
            )

        # 1. Build complete timeline of events
        full_timeline = self.timeline_builder.build_timeline(
            network_id=network_id,
            sequence=sequence,
            external_phase13_events=external_phase13_events,
            external_dt_gnn_signals=external_dt_gnn_signals,
            external_fusion_signals=external_fusion_signals,
        )

        # 2. Determine time boundaries
        snapshots = sequence.snapshots
        actual_start = start_time if start_time is not None else snapshots[0].timestamp
        actual_end = end_time if end_time is not None else snapshots[-1].timestamp

        if actual_start > actual_end:
            warnings.append(
                f"Requested start_time ({actual_start:.3f}) > end_time ({actual_end:.3f}). Swapped boundaries."
            )
            actual_start, actual_end = actual_end, actual_start

        # 3. Filter snapshots relevant to the window
        relevant_snapshots = [
            s for s in snapshots if actual_start <= s.timestamp <= actual_end
        ]

        if not relevant_snapshots:
            # Reconstruct boundary approximations
            start_state = GraphSnapshotReconstructor.reconstruct_at_timestamp(sequence, actual_start)
            end_state = GraphSnapshotReconstructor.reconstruct_at_timestamp(sequence, actual_end)
            relevant_states = [start_state]
            if abs(start_state.timestamp - end_state.timestamp) > 1e-6:
                relevant_states.append(end_state)
            warnings.append("No exact snapshots found within window; reconstructed boundary approximations.")
        else:
            relevant_states = [
                GraphSnapshotReconstructor.reconstruct_from_snapshot(s)
                for s in relevant_snapshots
            ]

        # 4. Generate Replay Frames
        frames: List[ReplayFrame] = []
        for idx, state in enumerate(relevant_states):
            frame_id = compute_replay_frame_identity(
                network_id=network_id,
                frame_index=idx,
                timestamp=state.timestamp,
                state_hash=state.state_hash,
            )

            # Compute change set from previous frame
            if idx > 0:
                change_set = GraphChangeDetector.detect_changes(relevant_states[idx - 1], state)
            else:
                change_set = None

            # Collect active timeline events at or up to this state's timestamp
            frame_ts = state.timestamp
            prior_ts = relevant_states[idx - 1].timestamp if idx > 0 else (frame_ts - 0.001)
            frame_events = [
                e for e in full_timeline if prior_ts < e.timestamp <= frame_ts
            ]

            frames.append(
                ReplayFrame(
                    frame_index=idx,
                    frame_id=frame_id,
                    timestamp=frame_ts,
                    state_hash=state.state_hash,
                    accuracy=state.accuracy,
                    graph_state=state,
                    change_from_previous=change_set,
                    active_events=frame_events,
                    provenance_type=ProvenanceType.DERIVED,
                )
            )

        # Filter timeline events strictly within the replay window for summary
        summary_timeline = [
            e for e in full_timeline if actual_start <= e.timestamp <= actual_end
        ]

        manifest_payload = {
            "network_id": network_id,
            "start_time": actual_start,
            "end_time": actual_end,
            "frame_hashes": [f.state_hash for f in frames],
        }
        replay_id = f"RPL-{compute_canonical_hash(manifest_payload)[:12].upper()}"

        return ReplayManifest(
            replay_id=replay_id,
            network_id=network_id,
            start_time=actual_start,
            end_time=actual_end,
            total_frames=len(frames),
            frames=frames,
            summary_timeline=summary_timeline,
            data_quality_warnings=warnings,
        )
