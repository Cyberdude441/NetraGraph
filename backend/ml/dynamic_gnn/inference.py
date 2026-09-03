"""Inference Engine and Explainability Attributions for Dynamic Temporal GNN."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch

from .config import DTGNNConfig, InferenceConfig
from .data import DynamicGraphSequence
from .model import DynamicTemporalGNN

logger = logging.getLogger("DTGNNInference")


class DTGNNInferenceEngine:
    """Production inference engine for Dynamic Temporal Graph Neural Networks."""

    def __init__(
        self,
        model: Optional[DynamicTemporalGNN] = None,
        config: Optional[DTGNNConfig] = None,
        inference_config: Optional[InferenceConfig] = None,
        checkpoint_path: Optional[str | Path] = None,
    ):
        self.config = config or DTGNNConfig()
        self.inference_config = inference_config or InferenceConfig()
        self.device = torch.device(self.config.device if torch.cuda.is_available() and self.config.device.startswith("cuda") else "cpu")

        if model is not None:
            self.model = model.to(self.device)
        else:
            self.model = DynamicTemporalGNN(self.config).to(self.device)
            if checkpoint_path is not None:
                self.load_checkpoint(checkpoint_path)

        self.model.eval()

    def load_checkpoint(self, path: str | Path) -> None:
        """Loads weights and state from checkpoint file."""
        ckpt_path = Path(path)
        if not ckpt_path.is_file():
            logger.warning(f"Checkpoint file not found at {path}. Operating with initialized model.")
            return

        try:
            state = torch.load(ckpt_path, map_location=self.device, weights_only=False)
            if isinstance(state, dict) and "model_state_dict" in state:
                self.model.load_state_dict(state["model_state_dict"])
            elif isinstance(state, dict):
                self.model.load_state_dict(state)
            self.model.eval()
            logger.info(f"Loaded DT-GNN checkpoint from {path}")
        except Exception as exc:
            logger.error(f"Failed to load DT-GNN checkpoint: {exc}")

    def analyze_sequence(self, sequence: DynamicGraphSequence) -> Dict[str, Any]:
        """Performs full temporal inference and explainability extraction on dynamic graph sequence."""
        if sequence.total_nodes == 0:
            return {
                "case_id": sequence.case_id,
                "graph_anomaly_score": 0.0,
                "network_risk_level": "LOW",
                "network_embedding": [],
                "nodes": [],
                "edges": [],
                "explainability": {
                    "influential_nodes": [],
                    "influential_relationships": [],
                    "critical_subgraph": {"node_ids": [], "edge_keys": []},
                    "attribution_disclaimer": "Model-derived statistical correlation; not a determination of legal culpability or causality.",
                },
                "metadata": {
                    "total_nodes": 0,
                    "total_snapshots": 0,
                    "model_version": "DT-GNN-v1",
                    "device": str(self.device),
                }
            }

        # 1. Deterministic / seed control
        if self.inference_config.deterministic:
            torch.manual_seed(42)

        with torch.no_grad():
            outputs = self.model(sequence, device=self.device)

        node_scores = outputs["node_risk_scores"].squeeze(-1).cpu().numpy()
        graph_anomaly = float(outputs["graph_anomaly_score"].item())
        graph_embedding = outputs["graph_embedding"].cpu().numpy().tolist()
        node_id_map = outputs["node_id_map"]
        rev_node_map = {idx: nid for nid, idx in node_id_map.items()}

        # 2. Structure node outputs
        node_results: List[Dict[str, Any]] = []
        for nid, idx in node_id_map.items():
            raw_node = sequence.all_nodes[nid]
            score_val = float(node_scores[idx])
            node_results.append({
                "node_id": nid,
                "entity_type": raw_node.entity_type,
                "threat_risk_score": round(score_val, 4),
                "heuristic_prior": raw_node.risk_score,
                "confidence": raw_node.confidence,
                "is_elevated_risk": bool(score_val >= self.inference_config.confidence_threshold),
            })

        # Sort nodes by threat risk descending
        node_results.sort(key=lambda x: x["threat_risk_score"], reverse=True)

        # 3. Structure edge scores if edges exist in latest snapshot
        edge_results: List[Dict[str, Any]] = []
        if sequence.snapshots:
            latest_snap = sequence.snapshots[-1]
            for edge in latest_snap.edges:
                s_score = node_scores[node_id_map[edge.source_id]] if edge.source_id in node_id_map else 0.5
                t_score = node_scores[node_id_map[edge.target_id]] if edge.target_id in node_id_map else 0.5
                joint_risk = round(float(np.sqrt(s_score * t_score) * (edge.weight / 10.0)), 4)
                edge_results.append({
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "rel_type": edge.rel_type,
                    "edge_risk_score": joint_risk,
                    "weight": edge.weight,
                })
            edge_results.sort(key=lambda x: x["edge_risk_score"], reverse=True)

        # 4. Extract Explainability Attributions
        explainability = self._extract_explainability(
            node_results=node_results,
            edge_results=edge_results,
            last_attention=outputs["last_edge_attention"],
            sequence=sequence,
        )

        # 5. Network risk tier
        if graph_anomaly >= 0.75:
            network_risk_level = "CRITICAL"
        elif graph_anomaly >= 0.50:
            network_risk_level = "HIGH"
        elif graph_anomaly >= 0.25:
            network_risk_level = "MEDIUM"
        else:
            network_risk_level = "LOW"

        return {
            "case_id": sequence.case_id,
            "graph_anomaly_score": round(graph_anomaly, 4),
            "network_risk_level": network_risk_level,
            "network_embedding": [round(float(v), 5) for v in graph_embedding],
            "nodes": node_results,
            "edges": edge_results,
            "explainability": explainability,
            "metadata": {
                "total_nodes": sequence.total_nodes,
                "total_snapshots": sequence.sequence_length,
                "model_version": "DT-GNN-v1",
                "device": str(self.device),
            },
        }

    def _extract_explainability(
        self,
        node_results: List[Dict[str, Any]],
        edge_results: List[Dict[str, Any]],
        last_attention: Optional[torch.Tensor],
        sequence: DynamicGraphSequence,
    ) -> Dict[str, Any]:
        """Extracts top influential nodes, relationships, and the critical risk subgraph."""
        k_nodes = self.inference_config.top_k_influential_nodes
        k_edges = self.inference_config.top_k_influential_edges

        # Top influential nodes based on model threat score
        influential_nodes = [
            {
                "node_id": n["node_id"],
                "entity_type": n["entity_type"],
                "threat_risk_score": n["threat_risk_score"],
                "attribution_weight": n["threat_risk_score"],
            }
            for n in node_results[:k_nodes]
        ]

        # Top influential relationships
        influential_relationships = [
            {
                "source_id": e["source_id"],
                "target_id": e["target_id"],
                "rel_type": e["rel_type"],
                "edge_risk_score": e["edge_risk_score"],
            }
            for e in edge_results[:k_edges]
        ]

        # Critical subgraph (nodes and edges comprising elevated risk cluster)
        critical_node_ids = {n["node_id"] for n in node_results if n["threat_risk_score"] >= 0.6}
        if not critical_node_ids and node_results:
            critical_node_ids = {n["node_id"] for n in node_results[:min(3, len(node_results))]}

        critical_edges = [
            f"{e['source_id']}->{e['target_id']}:{e['rel_type']}"
            for e in edge_results
            if e["source_id"] in critical_node_ids and e["target_id"] in critical_node_ids
        ]

        return {
            "influential_nodes": influential_nodes,
            "influential_relationships": influential_relationships,
            "critical_subgraph": {
                "node_ids": sorted(list(critical_node_ids)),
                "edge_keys": critical_edges,
            },
            "attribution_disclaimer": (
                "Model-derived statistical correlation; not a determination of legal culpability or causality. "
                "Provided for analytical prioritization only."
            ),
        }
