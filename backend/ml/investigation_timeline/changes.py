"""Deterministic graph structural and attribute change detection between consecutive states."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from .config import ProvenanceType, TimelineEventType
from .models import (
    GraphChangeSet,
    InvestigationTimelineEvent,
    ReconstructedGraphState,
)
from .provenance import compute_timeline_event_identity


class GraphChangeDetector:
    """
    Detects additions, removals, attribute shifts, and topological deltas between two graph states.
    All detected changes are classified as DERIVED rather than raw evidence facts.
    """

    @staticmethod
    def _canonical_edge_tuple(u: str, v: str, rel_type: str) -> Tuple[str, str, str]:
        src, dst = (u, v) if u <= v else (v, u)
        return (src, dst, rel_type)

    @classmethod
    def detect_changes(
        cls,
        prior_state: ReconstructedGraphState,
        curr_state: ReconstructedGraphState,
    ) -> GraphChangeSet:
        """Compute detailed node, edge, and topological differences between two graph states."""
        # Node diffs
        prior_nodes = set(prior_state.nodes.keys())
        curr_nodes = set(curr_state.nodes.keys())

        added_nodes = sorted(list(curr_nodes - prior_nodes))
        removed_nodes = sorted(list(prior_nodes - curr_nodes))

        # Node attribute diffs
        node_attr_changes: Dict[str, Dict[str, Any]] = {}
        for nid in sorted(prior_nodes & curr_nodes):
            p_node = prior_state.nodes[nid]
            c_node = curr_state.nodes[nid]
            diffs: Dict[str, Any] = {}

            # Check risk score delta
            if p_node.risk_score != c_node.risk_score:
                diffs["risk_score"] = {"old": p_node.risk_score, "new": c_node.risk_score}

            # Check attribute dict differences
            p_attrs = p_node.attributes or {}
            c_attrs = c_node.attributes or {}
            for k in set(p_attrs.keys()) | set(c_attrs.keys()):
                v_old = p_attrs.get(k)
                v_new = c_attrs.get(k)
                if v_old != v_new:
                    diffs[k] = {"old": v_old, "new": v_new}

            if diffs:
                node_attr_changes[nid] = diffs

        # Edge diffs
        prior_edges_map: Dict[Tuple[str, str, str], Any] = {
            cls._canonical_edge_tuple(e.source_id, e.target_id, e.rel_type): e
            for e in prior_state.edges
        }
        curr_edges_map: Dict[Tuple[str, str, str], Any] = {
            cls._canonical_edge_tuple(e.source_id, e.target_id, e.rel_type): e
            for e in curr_state.edges
        }

        prior_edge_keys = set(prior_edges_map.keys())
        curr_edge_keys = set(curr_edges_map.keys())

        added_edges = sorted(list(curr_edge_keys - prior_edge_keys))
        removed_edges = sorted(list(prior_edge_keys - curr_edge_keys))

        # Edge attribute diffs
        edge_attr_changes: Dict[str, Dict[str, Any]] = {}
        for edge_key in sorted(prior_edge_keys & curr_edge_keys):
            p_edge = prior_edges_map[edge_key]
            c_edge = curr_edges_map[edge_key]
            e_diffs: Dict[str, Any] = {}

            if p_edge.weight != c_edge.weight:
                e_diffs["weight"] = {"old": p_edge.weight, "new": c_edge.weight}

            p_attrs = p_edge.attributes or {}
            c_attrs = c_edge.attributes or {}
            for k in set(p_attrs.keys()) | set(c_attrs.keys()):
                v_old = p_attrs.get(k)
                v_new = c_attrs.get(k)
                if v_old != v_new:
                    e_diffs[k] = {"old": v_old, "new": v_new}

            if e_diffs:
                key_str = f"{edge_key[0]}--{edge_key[1]}--{edge_key[2]}"
                edge_attr_changes[key_str] = e_diffs

        # Structural metrics
        node_delta = len(curr_nodes) - len(prior_nodes)
        edge_delta = len(curr_edge_keys) - len(prior_edge_keys)

        # Graph density and component calculations via NetworkX
        def _build_nx(state: ReconstructedGraphState) -> nx.Graph:
            g = nx.Graph()
            for nid in state.nodes.keys():
                g.add_node(nid)
            for e in state.edges:
                g.add_edge(e.source_id, e.target_id)
            return g

        g_prior = _build_nx(prior_state)
        g_curr = _build_nx(curr_state)

        d_prior = nx.density(g_prior) if len(g_prior) > 1 else 0.0
        d_curr = nx.density(g_curr) if len(g_curr) > 1 else 0.0
        density_delta = round(d_curr - d_prior, 6)

        c_prior = nx.number_connected_components(g_prior) if len(g_prior) > 0 else 0
        c_curr = nx.number_connected_components(g_curr) if len(g_curr) > 0 else 0
        component_delta = c_curr - c_prior

        is_empty = (len(curr_nodes) == 0 and len(prior_nodes) == 0)

        return GraphChangeSet(
            from_timestamp=prior_state.timestamp,
            to_timestamp=curr_state.timestamp,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            node_attribute_changes=node_attr_changes,
            added_edges=added_edges,
            removed_edges=removed_edges,
            edge_attribute_changes=edge_attr_changes,
            node_count_delta=node_delta,
            edge_count_delta=edge_delta,
            density_delta=density_delta,
            component_count_delta=component_delta,
            is_empty=is_empty,
        )

    @classmethod
    def generate_change_events(
        cls,
        network_id: str,
        changes: GraphChangeSet,
    ) -> List[InvestigationTimelineEvent]:
        """Convert detected structural and attribute changes into discrete chronological timeline events."""
        events: List[InvestigationTimelineEvent] = []
        ts = changes.to_timestamp

        # 1. Node Additions
        if changes.added_nodes:
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.NODE_ADDED.value,
                timestamp=ts,
                entity_ids=changes.added_nodes,
                edge_ids=[],
                source_reference="GraphChangeDetector",
                details={"count": len(changes.added_nodes), "nodes": changes.added_nodes},
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.NODE_ADDED,
                    timestamp=ts,
                    network_id=network_id,
                    entity_ids=changes.added_nodes,
                    edge_ids=[],
                    provenance_type=ProvenanceType.DERIVED,
                    source_reference="GraphChangeDetector",
                    description=f"{len(changes.added_nodes)} node(s) added to network structure.",
                    details={"added_nodes": changes.added_nodes},
                )
            )

        # 2. Node Removals
        if changes.removed_nodes:
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.NODE_REMOVED.value,
                timestamp=ts,
                entity_ids=changes.removed_nodes,
                edge_ids=[],
                source_reference="GraphChangeDetector",
                details={"count": len(changes.removed_nodes), "nodes": changes.removed_nodes},
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.NODE_REMOVED,
                    timestamp=ts,
                    network_id=network_id,
                    entity_ids=changes.removed_nodes,
                    edge_ids=[],
                    provenance_type=ProvenanceType.DERIVED,
                    source_reference="GraphChangeDetector",
                    description=f"{len(changes.removed_nodes)} node(s) removed from network structure.",
                    details={"removed_nodes": changes.removed_nodes},
                )
            )

        # 3. Edge Additions
        if changes.added_edges:
            edge_strs = [f"{e[0]}--{e[1]} ({e[2]})" for e in changes.added_edges]
            affected_entities = sorted(list({e[0] for e in changes.added_edges} | {e[1] for e in changes.added_edges}))
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.EDGE_ADDED.value,
                timestamp=ts,
                entity_ids=affected_entities,
                edge_ids=edge_strs,
                source_reference="GraphChangeDetector",
                details={"count": len(changes.added_edges)},
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.EDGE_ADDED,
                    timestamp=ts,
                    network_id=network_id,
                    entity_ids=affected_entities,
                    edge_ids=edge_strs,
                    provenance_type=ProvenanceType.DERIVED,
                    source_reference="GraphChangeDetector",
                    description=f"{len(changes.added_edges)} relationship(s) introduced.",
                    details={"added_edges": changes.added_edges},
                )
            )

        # 4. Edge Removals
        if changes.removed_edges:
            edge_strs = [f"{e[0]}--{e[1]} ({e[2]})" for e in changes.removed_edges]
            affected_entities = sorted(list({e[0] for e in changes.removed_edges} | {e[1] for e in changes.removed_edges}))
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.EDGE_REMOVED.value,
                timestamp=ts,
                entity_ids=affected_entities,
                edge_ids=edge_strs,
                source_reference="GraphChangeDetector",
                details={"count": len(changes.removed_edges)},
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.EDGE_REMOVED,
                    timestamp=ts,
                    network_id=network_id,
                    entity_ids=affected_entities,
                    edge_ids=edge_strs,
                    provenance_type=ProvenanceType.DERIVED,
                    source_reference="GraphChangeDetector",
                    description=f"{len(changes.removed_edges)} relationship(s) severed or removed.",
                    details={"removed_edges": changes.removed_edges},
                )
            )

        # 5. Node Attribute Changes
        if changes.node_attribute_changes:
            affected_nids = sorted(list(changes.node_attribute_changes.keys()))
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.NODE_ATTRIBUTE_CHANGED.value,
                timestamp=ts,
                entity_ids=affected_nids,
                edge_ids=[],
                source_reference="GraphChangeDetector",
                details={"count": len(affected_nids)},
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.NODE_ATTRIBUTE_CHANGED,
                    timestamp=ts,
                    network_id=network_id,
                    entity_ids=affected_nids,
                    edge_ids=[],
                    provenance_type=ProvenanceType.DERIVED,
                    source_reference="GraphChangeDetector",
                    description=f"Attribute shifts detected across {len(affected_nids)} entity node(s).",
                    details={"changes": changes.node_attribute_changes},
                )
            )

        # 6. Edge Attribute Changes
        if changes.edge_attribute_changes:
            ev_id, fp = compute_timeline_event_identity(
                network_id=network_id,
                event_type=TimelineEventType.EDGE_ATTRIBUTE_CHANGED.value,
                timestamp=ts,
                entity_ids=[],
                edge_ids=sorted(list(changes.edge_attribute_changes.keys())),
                source_reference="GraphChangeDetector",
                details={"count": len(changes.edge_attribute_changes)},
            )
            events.append(
                InvestigationTimelineEvent(
                    event_id=ev_id,
                    event_fingerprint=fp,
                    event_type=TimelineEventType.EDGE_ATTRIBUTE_CHANGED,
                    timestamp=ts,
                    network_id=network_id,
                    entity_ids=[],
                    edge_ids=sorted(list(changes.edge_attribute_changes.keys())),
                    provenance_type=ProvenanceType.DERIVED,
                    source_reference="GraphChangeDetector",
                    description=f"Attribute shifts detected across {len(changes.edge_attribute_changes)} relationship edge(s).",
                    details={"changes": changes.edge_attribute_changes},
                )
            )

        return events
