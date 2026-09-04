"""Provenance lineage tracking, canonical serialization, and deterministic hashing utilities."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple


def canonical_json_dumps(obj: Any) -> str:
    """
    Produce canonical, deterministic JSON string with sorted keys and normalized representations.
    Prevents formatting variations from changing cryptographic digests.
    """
    def _normalize(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: _normalize(v) for k, v in sorted(val.items(), key=lambda item: str(item[0]))}
        elif isinstance(val, (list, tuple)):
            return [_normalize(item) for item in val]
        elif isinstance(val, float):
            # Round floats to 6 decimal places to prevent float precision divergences across environments
            return round(val, 6)
        elif isinstance(val, (int, str, bool)) or val is None:
            return val
        else:
            return str(val)

    normalized = _normalize(obj)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def compute_canonical_hash(payload: Any) -> str:
    """Compute 64-character SHA-256 digest over canonical JSON representation."""
    canonical_str = canonical_json_dumps(payload)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def compute_graph_state_hash(
    nodes: Dict[str, Any],
    edges: List[Any],
) -> str:
    """
    Compute a deterministic canonical state hash for an entire graph topology and attribute state.
    
    Nodes are sorted by ID.
    Edges are canonicalized as undirected/directed pairs (min(u,v), max(u,v), rel_type) and sorted.
    """
    canonical_nodes = []
    for node_id in sorted(nodes.keys()):
        node = nodes[node_id]
        if hasattr(node, "entity_type"):
            entity_type = getattr(node, "entity_type", "UNKNOWN")
            risk_score = getattr(node, "risk_score", None)
            attrs = getattr(node, "attributes", {}) or {}
        elif isinstance(node, dict):
            entity_type = node.get("entity_type", "UNKNOWN")
            risk_score = node.get("risk_score")
            attrs = node.get("attributes", {}) or {}
        else:
            entity_type = "UNKNOWN"
            risk_score = None
            attrs = {}
        canonical_nodes.append({
            "id": str(node_id),
            "entity_type": str(entity_type),
            "risk_score": round(float(risk_score), 6) if risk_score is not None else None,
            "attributes": attrs,
        })

    canonical_edges = []
    for edge in edges:
        if hasattr(edge, "source_id"):
            u = getattr(edge, "source_id")
            v = getattr(edge, "target_id")
            rel_type = getattr(edge, "rel_type", "RELATED_TO")
            attrs = getattr(edge, "attributes", {}) or {}
        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
            u, v = edge[0], edge[1]
            rel_type = edge[2] if len(edge) > 2 else "RELATED_TO"
            attrs = {}
        elif isinstance(edge, dict):
            u = edge.get("source_id") or edge.get("source")
            v = edge.get("target_id") or edge.get("target")
            rel_type = edge.get("rel_type") or edge.get("type", "RELATED_TO")
            attrs = edge.get("attributes", {}) or {}
        else:
            continue

        # Sort undirected endpoints to ensure canonical representation
        u_str, v_str = str(u), str(v)
        src, dst = (u_str, v_str) if u_str <= v_str else (v_str, u_str)
        canonical_edges.append({
            "source": src,
            "target": dst,
            "rel_type": str(rel_type),
            "attributes": attrs,
        })

    canonical_edges.sort(key=lambda e: (e["source"], e["target"], e["rel_type"]))

    state_payload = {
        "nodes": canonical_nodes,
        "edges": canonical_edges,
    }
    return compute_canonical_hash(state_payload)


def compute_timeline_event_identity(
    network_id: str,
    event_type: str,
    timestamp: float,
    entity_ids: List[str],
    edge_ids: List[str],
    source_reference: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Generate deterministic (event_id, event_fingerprint) tuple.
    
    Uses canonical JSON hashing over all discriminating fields to guarantee:
    Identical inputs -> Identical canonical digest -> Identical event ID and fingerprint.
    """
    identity_payload = {
        "network_id": str(network_id),
        "event_type": str(event_type),
        "timestamp": round(float(timestamp), 6),
        "entity_ids": sorted(str(e) for e in entity_ids),
        "edge_ids": sorted(str(ed) for ed in edge_ids),
        "source_reference": str(source_reference or ""),
        "details": details or {},
    }
    fingerprint = compute_canonical_hash(identity_payload)
    event_id = f"EVT-{fingerprint[:12].upper()}"
    return event_id, fingerprint


def compute_replay_frame_identity(
    network_id: str,
    frame_index: int,
    timestamp: float,
    state_hash: str,
) -> str:
    """Generate deterministic frame_id from index, network, timestamp, and graph state hash."""
    frame_payload = {
        "network_id": str(network_id),
        "frame_index": int(frame_index),
        "timestamp": round(float(timestamp), 6),
        "state_hash": str(state_hash),
    }
    frame_hash = compute_canonical_hash(frame_payload)
    return f"FRAME-{frame_hash[:12].upper()}"
