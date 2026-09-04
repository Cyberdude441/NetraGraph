"""Point-in-time graph state reconstruction engine with exact and approximate interpolation semantics."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..emerging_threat.snapshots import GraphSnapshot, TemporalSnapshotSequence
from .config import ReconstructionAccuracy
from .models import (
    GraphEntityState,
    GraphRelationshipState,
    ReconstructedGraphState,
)
from .provenance import compute_graph_state_hash


class GraphSnapshotReconstructor:
    """
    Reconstructs network state at any requested timestamp Tk from available snapshot data.
    Guarantees explicit transparency: never claims exact state when only an approximation is available.
    """

    @classmethod
    def reconstruct_from_snapshot(
        cls,
        snapshot: GraphSnapshot,
        accuracy: ReconstructionAccuracy = ReconstructionAccuracy.EXACT,
        custom_timestamp: Optional[float] = None,
        extra_warnings: Optional[List[str]] = None,
    ) -> ReconstructedGraphState:
        """Convert a GraphSnapshot into a canonical ReconstructedGraphState."""
        warnings = list(extra_warnings or [])
        ts = custom_timestamp if custom_timestamp is not None else snapshot.timestamp

        entity_states: Dict[str, GraphEntityState] = {}
        for node_id, node in snapshot.nodes.items():
            entity_states[node_id] = GraphEntityState(
                id=node.id,
                entity_type=node.entity_type,
                risk_score=node.risk_score,
                attributes=dict(node.attributes or {}),
            )

        rel_states: List[GraphRelationshipState] = []
        for rel in snapshot.edges:
            rel_states.append(
                GraphRelationshipState(
                    source_id=rel.source_id,
                    target_id=rel.target_id,
                    rel_type=rel.rel_type,
                    weight=rel.weight,
                    attributes=dict(rel.attributes or {}),
                )
            )

        state_hash = compute_graph_state_hash(entity_states, rel_states)

        return ReconstructedGraphState(
            timestamp=ts,
            state_hash=state_hash,
            accuracy=accuracy,
            reference_snapshot_id=snapshot.snapshot_id,
            nodes=entity_states,
            edges=rel_states,
            node_count=len(entity_states),
            edge_count=len(rel_states),
            data_quality_warnings=warnings,
        )

    @classmethod
    def reconstruct_at_timestamp(
        cls,
        sequence: TemporalSnapshotSequence,
        target_timestamp: float,
        exact_epsilon: float = 1e-6,
    ) -> ReconstructedGraphState:
        """
        Reconstruct graph state at target_timestamp from a temporal sequence.
        
        If an exact match exists within exact_epsilon, returns exact state.
        Otherwise finds the nearest valid snapshot, records the approximation delta,
        and returns the state with accuracy = APPROXIMATED.
        """
        if sequence.is_empty():
            state_hash = compute_graph_state_hash({}, [])
            return ReconstructedGraphState(
                timestamp=target_timestamp,
                state_hash=state_hash,
                accuracy=ReconstructionAccuracy.EMPTY_INTERPOLATED,
                reference_snapshot_id=None,
                nodes={},
                edges=[],
                node_count=0,
                edge_count=0,
                data_quality_warnings=["Empty snapshot sequence provided; returned empty graph state."],
            )

        snapshots = sequence.snapshots

        # 1. Check for exact match
        for s in snapshots:
            if abs(s.timestamp - target_timestamp) <= exact_epsilon:
                return cls.reconstruct_from_snapshot(
                    s,
                    accuracy=ReconstructionAccuracy.EXACT,
                    custom_timestamp=target_timestamp,
                )

        # 2. Find nearest snapshot
        nearest = min(snapshots, key=lambda s: abs(s.timestamp - target_timestamp))
        delta = abs(nearest.timestamp - target_timestamp)
        warning_msg = (
            f"State approximated from snapshot '{nearest.snapshot_id}' at t={nearest.timestamp:.3f} "
            f"(target t={target_timestamp:.3f}, delta: {delta:.3f}s)."
        )

        return cls.reconstruct_from_snapshot(
            nearest,
            accuracy=ReconstructionAccuracy.APPROXIMATED,
            custom_timestamp=target_timestamp,
            extra_warnings=[warning_msg],
        )
