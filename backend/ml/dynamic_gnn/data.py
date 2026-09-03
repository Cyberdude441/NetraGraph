"""Graph data abstractions for Dynamic Temporal Graph Neural Networks.

Decouples the neural message passing layer from database (Neo4j/SQL) internals.
Provides clean snapshot-based and continuous-time graph representations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import torch

# Standard NetraGraph vocabulary
ENTITY_TYPE_VOCAB: Dict[str, int] = {
    "Person": 0,
    "Phone": 1,
    "BankAccount": 2,
    "Location": 3,
    "Device": 4,
    "IPAddress": 5,
    "Domain": 6,
    "Organization": 7,
    "Vehicle": 8,
    "Unknown": 9,
}

RELATIONSHIP_TYPE_VOCAB: Dict[str, int] = {
    "CALL": 0,
    "TRANSACTION": 1,
    "LOGIN": 2,
    "OWNS": 3,
    "LOCATED_AT": 4,
    "ASSOCIATED_WITH": 5,
    "COMMUNICATED_WITH": 6,
    "CALLS": 0,
    "TRANSACTS": 1,
    "MEETS": 6,
    "Unknown": 7,
}


def parse_iso_timestamp(ts: Any) -> float:
    """Safely converts ISO-8601 string, numeric timestamp, or datetime to float Unix epoch seconds."""
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
            clean_ts = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except (ValueError, TypeError):
            try:
                return float(ts)
            except ValueError:
                return 0.0
    return 0.0


@dataclass
class TemporalNode:
    """Individual entity representation within a temporal snapshot."""
    id: str
    entity_type: str = "Unknown"
    risk_score: float = 50.0            # 0-100 baseline heuristic or prior risk
    confidence: float = 0.95            # Entity resolution confidence 0-1
    continuous_features: List[float] = field(default_factory=list)
    model_predictions: Dict[str, float] = field(default_factory=dict)  # Models A-E outputs
    timestamp: float = 0.0              # Unix epoch seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

    def type_idx(self) -> int:
        return ENTITY_TYPE_VOCAB.get(self.entity_type, ENTITY_TYPE_VOCAB["Unknown"])


@dataclass
class TemporalEdge:
    """Directed interaction or linkage between two entities with a timestamp."""
    source_id: str
    target_id: str
    rel_type: str = "ASSOCIATED_WITH"
    weight: float = 1.0                 # Link strength
    confidence: float = 0.90            # Link confidence
    continuous_features: List[float] = field(default_factory=list)
    timestamp: float = 0.0              # Interaction epoch seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

    def type_idx(self) -> int:
        return RELATIONSHIP_TYPE_VOCAB.get(self.rel_type, RELATIONSHIP_TYPE_VOCAB["Unknown"])


@dataclass
class TemporalGraphSnapshot:
    """Static graph topology at a discrete time slice t_i or aggregated window."""
    snapshot_idx: int
    timestamp_start: float
    timestamp_end: float
    nodes: Dict[str, TemporalNode] = field(default_factory=dict)
    edges: List[TemporalEdge] = field(default_factory=list)

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    def to_tensors(self, node_id_to_idx: Dict[str, int]) -> Dict[str, torch.Tensor]:
        """Converts snapshot topology and features into PyTorch tensors."""
        num_nodes = len(node_id_to_idx)
        if num_nodes == 0:
            return {
                "edge_index": torch.zeros((2, 0), dtype=torch.long),
                "edge_attr": torch.zeros((0, 4), dtype=torch.float32),
                "edge_type": torch.zeros((0,), dtype=torch.long),
                "edge_time": torch.zeros((0,), dtype=torch.float32),
            }

        edge_list: List[Tuple[int, int]] = []
        edge_attrs: List[List[float]] = []
        edge_types: List[int] = []
        edge_times: List[float] = []

        ref_time = self.timestamp_end if self.timestamp_end > 0 else self.timestamp_start

        for e in self.edges:
            if e.source_id in node_id_to_idx and e.target_id in node_id_to_idx:
                s_idx = node_id_to_idx[e.source_id]
                t_idx = node_id_to_idx[e.target_id]
                edge_list.append((s_idx, t_idx))

                # Edge features: [weight, confidence, duration/extra, amount/extra]
                duration = float(e.metadata.get("duration", 0.0) or 0.0) / 3600.0  # Normalized hours
                amount = float(e.metadata.get("amount", 0.0) or 0.0) / 10000.0     # Normalized scale
                base_attr = [e.weight / 10.0, e.confidence, min(duration, 10.0), min(amount, 10.0)]
                edge_attrs.append(base_attr)
                edge_types.append(e.type_idx())
                
                # Delta time relative to snapshot window
                rel_time = max(0.0, ref_time - e.timestamp) if ref_time > 0 else 0.0
                edge_times.append(rel_time)

        if edge_list:
            edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
            edge_attr = torch.tensor(edge_attrs, dtype=torch.float32)
            edge_type = torch.tensor(edge_types, dtype=torch.long)
            edge_time = torch.tensor(edge_times, dtype=torch.float32)
        else:
            edge_index = torch.zeros((2, 0), dtype=torch.long)
            edge_attr = torch.zeros((0, 4), dtype=torch.float32)
            edge_type = torch.zeros((0,), dtype=torch.long)
            edge_time = torch.zeros((0,), dtype=torch.float32)

        return {
            "edge_index": edge_index,
            "edge_attr": edge_attr,
            "edge_type": edge_type,
            "edge_time": edge_time,
        }


@dataclass
class DynamicGraphSequence:
    """Sequential progression of temporal graph snapshots G(t_0), G(t_1), ..., G(t_T-1)."""
    case_id: str
    snapshots: List[TemporalGraphSnapshot] = field(default_factory=list)
    all_node_ids: List[str] = field(default_factory=list)
    all_nodes: Dict[str, TemporalNode] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def sequence_length(self) -> int:
        return len(self.snapshots)

    @property
    def total_nodes(self) -> int:
        return len(self.all_node_ids)

    def node_id_map(self) -> Dict[str, int]:
        """Returns stable global mapping from entity ID to contiguous index [0..N-1]."""
        return {nid: idx for idx, nid in enumerate(self.all_node_ids)}

    @classmethod
    def from_networkx(
        cls,
        graph: Any,
        case_id: str = "CASE-DEFAULT",
        num_snapshots: int = 3,
    ) -> DynamicGraphSequence:
        """Converts an in-memory NetworkX MultiDiGraph into a DynamicGraphSequence."""
        import networkx as nx

        all_nodes: Dict[str, TemporalNode] = {}
        edges_with_time: List[TemporalEdge] = []

        for nid, data in graph.nodes(data=True):
            ent_type = data.get("type") or data.get("label") or "Unknown"
            risk = float(data.get("riskScore", 50.0) or 50.0)
            conf = float(data.get("confidence", 0.95) or 0.95)
            ts = parse_iso_timestamp(data.get("createdAt") or data.get("timestamp"))
            
            # Extract optional Models A-E predictions if attached to node
            model_preds = data.get("model_predictions") or {}
            
            all_nodes[str(nid)] = TemporalNode(
                id=str(nid),
                entity_type=str(ent_type),
                risk_score=risk,
                confidence=conf,
                model_predictions=model_preds,
                timestamp=ts,
                metadata=dict(data),
            )

        for u, v, k, data in graph.edges(keys=True, data=True):
            rel_type = data.get("type") or "ASSOCIATED_WITH"
            weight = float(data.get("weight", 1.0) or 1.0)
            conf = float(data.get("confidence", 0.90) or 0.90)
            ts = parse_iso_timestamp(data.get("createdAt") or data.get("timestamp"))

            edges_with_time.append(TemporalEdge(
                source_id=str(u),
                target_id=str(v),
                rel_type=str(rel_type),
                weight=weight,
                confidence=conf,
                timestamp=ts,
                metadata=dict(data),
            ))

        return cls.from_elements(
            all_nodes=all_nodes,
            all_edges=edges_with_time,
            case_id=case_id,
            num_snapshots=num_snapshots,
        )

    @classmethod
    def from_elements(
        cls,
        all_nodes: Dict[str, TemporalNode],
        all_edges: List[TemporalEdge],
        case_id: str = "CASE-DEFAULT",
        num_snapshots: int = 3,
    ) -> DynamicGraphSequence:
        """Constructs a chronological snapshot sequence from raw node and edge collections."""
        node_ids = sorted(all_nodes.keys())
        if not node_ids:
            # Empty sequence handling
            return cls(case_id=case_id, snapshots=[], all_node_ids=[], all_nodes={})

        if not all_edges:
            # Graph with nodes but zero edges
            single_snapshot = TemporalGraphSnapshot(
                snapshot_idx=0,
                timestamp_start=0.0,
                timestamp_end=0.0,
                nodes=all_nodes,
                edges=[],
            )
            return cls(
                case_id=case_id,
                snapshots=[single_snapshot],
                all_node_ids=node_ids,
                all_nodes=all_nodes,
            )

        # Sort edges chronologically
        sorted_edges = sorted(all_edges, key=lambda e: e.timestamp)
        t_min = sorted_edges[0].timestamp
        t_max = sorted_edges[-1].timestamp

        num_snapshots = max(1, min(num_snapshots, 10))

        if t_max <= t_min or num_snapshots == 1:
            # Single window
            snap = TemporalGraphSnapshot(
                snapshot_idx=0,
                timestamp_start=t_min,
                timestamp_end=t_max,
                nodes=all_nodes,
                edges=sorted_edges,
            )
            return cls(
                case_id=case_id,
                snapshots=[snap],
                all_node_ids=node_ids,
                all_nodes=all_nodes,
            )

        # Discretize temporal intervals
        window_size = (t_max - t_min) / num_snapshots
        snapshots: List[TemporalGraphSnapshot] = []

        for i in range(num_snapshots):
            w_start = t_min + i * window_size
            w_end = t_min + (i + 1) * window_size if i < num_snapshots - 1 else t_max + 1e-4

            # Cumulative historical network growth representation
            # (Past relationships remain active or decay in weight)
            w_edges = [e for e in sorted_edges if e.timestamp <= w_end]

            snapshots.append(TemporalGraphSnapshot(
                snapshot_idx=i,
                timestamp_start=w_start,
                timestamp_end=w_end,
                nodes=all_nodes,
                edges=w_edges,
            ))

        return cls(
            case_id=case_id,
            snapshots=snapshots,
            all_node_ids=node_ids,
            all_nodes=all_nodes,
        )
