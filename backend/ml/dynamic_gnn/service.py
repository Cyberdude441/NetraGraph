"""Operational Service layer bridging NetraGraph investigation graphs and the DT-GNN model."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from .config import DTGNNConfig, InferenceConfig
from .data import DynamicGraphSequence, TemporalEdge, TemporalNode
from .inference import DTGNNInferenceEngine
from .model import DynamicTemporalGNN

logger = logging.getLogger("DTGNNService")


class DTGNNService:
    """Thread-safe singleton service managing the DT-GNN inference lifecycle."""

    _instance: Optional[DTGNNService] = None

    def __init__(self, config: Optional[DTGNNConfig] = None):
        self.config = config or DTGNNConfig()
        self.inference_config = InferenceConfig()
        self.engine = DTGNNInferenceEngine(
            config=self.config,
            inference_config=self.inference_config,
        )

    @classmethod
    def get_instance(cls) -> DTGNNService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def validate_graph_payload(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> None:
        """Protects against pathological request payloads and resource exhaustion."""
        if len(nodes) > self.config.max_nodes_per_snapshot:
            raise HTTPException(
                status_code=413,
                detail=f"Graph node count ({len(nodes)}) exceeds maximum permitted limit ({self.config.max_nodes_per_snapshot})",
            )
        if len(edges) > self.config.max_edges_per_snapshot:
            raise HTTPException(
                status_code=413,
                detail=f"Graph edge count ({len(edges)}) exceeds maximum permitted limit ({self.config.max_edges_per_snapshot})",
            )

    def analyze_graph_data(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        case_id: str = "CASE-DEFAULT",
        num_snapshots: int = 3,
        models_predictions: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        """Ingests raw graph dictionary payloads, parses temporal snapshots, and executes DT-GNN analysis."""
        self.validate_graph_payload(nodes, edges)

        all_nodes: Dict[str, TemporalNode] = {}
        models_preds = models_predictions or {}

        for n in nodes:
            nid = str(n.get("id", ""))
            if not nid:
                continue
            ent_type = n.get("type") or n.get("label") or "Unknown"
            risk = float(n.get("riskScore", 50.0) or 50.0)
            conf = float(n.get("confidence", 0.95) or 0.95)
            ts = float(n.get("timestamp", 0.0) or 0.0)

            node_preds = models_preds.get(nid) or n.get("model_predictions") or {}

            all_nodes[nid] = TemporalNode(
                id=nid,
                entity_type=str(ent_type),
                risk_score=risk,
                confidence=conf,
                model_predictions=node_preds,
                timestamp=ts,
                metadata=dict(n),
            )

        all_edges: List[TemporalEdge] = []
        for e in edges:
            src = str(e.get("sourceId") or e.get("source", ""))
            dst = str(e.get("targetId") or e.get("target", ""))
            if not src or not dst:
                continue
            rel_type = str(e.get("type") or e.get("relationship", "ASSOCIATED_WITH"))
            weight = float(e.get("weight", 1.0) or 1.0)
            conf = float(e.get("confidence", 0.90) or 0.90)
            ts = float(e.get("timestamp", 0.0) or 0.0)

            all_edges.append(TemporalEdge(
                source_id=src,
                target_id=dst,
                rel_type=rel_type,
                weight=weight,
                confidence=conf,
                timestamp=ts,
                metadata=dict(e),
            ))

        sequence = DynamicGraphSequence.from_elements(
            all_nodes=all_nodes,
            all_edges=all_edges,
            case_id=case_id,
            num_snapshots=num_snapshots,
        )

        return self.engine.analyze_sequence(sequence)

    def analyze_active_case_graph(self, case_id: str) -> Dict[str, Any]:
        """Queries the active NetraGraph Neo4j/in-memory graph for a case and analyzes its temporal evolution."""
        try:
            from database.neo4j import neo4j_db
            ev_data = neo4j_db.query_evidence_graph(case_id=case_id)
            raw_nodes = ev_data.get("nodes", [])
            raw_rels = ev_data.get("relationships", [])
        except Exception as exc:
            logger.warning(f"Could not load graph from Neo4j for case {case_id}: {exc}. Using empty sequence.")
            raw_nodes, raw_rels = [], []

        return self.analyze_graph_data(
            nodes=raw_nodes,
            edges=raw_rels,
            case_id=case_id,
            num_snapshots=3,
        )


# Global service instance accessor
dt_gnn_service = DTGNNService.get_instance()
