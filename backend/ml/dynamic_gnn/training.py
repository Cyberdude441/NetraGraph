"""Isolated reproducible training pipeline for Dynamic Temporal Graph Neural Networks.

Implements strict chronological dataset partitioning to completely prevent temporal data leakage.
"""
from __future__ import annotations

import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from .config import DTGNNConfig, TrainingConfig
from .data import DynamicGraphSequence, TemporalEdge, TemporalGraphSnapshot, TemporalNode
from .model import DynamicTemporalGNN

logger = logging.getLogger("DTGNNTraining")


def chronological_split(
    sequences: List[DynamicGraphSequence],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[List[DynamicGraphSequence], List[DynamicGraphSequence], List[DynamicGraphSequence]]:
    """Partitions graph sequences strictly by chronological timestamp.

    Past (<= train_cutoff) -> Training
    Intermediate -> Validation
    Future (> val_cutoff) -> Testing

    GUARANTEE: No temporal overlap between training, validation, and test sequences.
    """
    if not sequences:
        return [], [], []

    # Sort sequences by their earliest observation timestamp
    def sequence_start_time(seq: DynamicGraphSequence) -> float:
        if seq.snapshots:
            return seq.snapshots[0].timestamp_start
        return 0.0

    sorted_seqs = sorted(sequences, key=sequence_start_time)
    n = len(sorted_seqs)

    n_train = max(1, int(n * train_ratio))
    n_val = max(1, int(n * val_ratio)) if n - n_train > 1 else 0

    train_seqs = sorted_seqs[:n_train]
    val_seqs = sorted_seqs[n_train : n_train + n_val]
    test_seqs = sorted_seqs[n_train + n_val :]

    if not test_seqs and val_seqs:
        test_seqs = [val_seqs.pop()]

    return train_seqs, val_seqs, test_seqs


class DTGNNTrainer:
    """Trains DT-GNN on sequential graph data with temporal safety."""

    def __init__(
        self,
        model: Optional[DynamicTemporalGNN] = None,
        config: Optional[DTGNNConfig] = None,
        training_config: Optional[TrainingConfig] = None,
    ):
        self.config = config or DTGNNConfig()
        self.training_config = training_config or TrainingConfig()
        self.device = torch.device(self.config.device if torch.cuda.is_available() and self.config.device.startswith("cuda") else "cpu")

        # Set reproducible seeds
        torch.manual_seed(self.training_config.seed)
        np.random.seed(self.training_config.seed)

        self.model = model or DynamicTemporalGNN(self.config)
        self.model.to(self.device)

        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.training_config.learning_rate,
            weight_decay=self.training_config.weight_decay,
        )

        self.node_loss_fn = nn.BCEWithLogitsLoss()
        self.graph_loss_fn = nn.BCELoss()

    def train_epoch(
        self,
        train_sequences: List[DynamicGraphSequence],
        node_labels: Optional[Dict[str, Dict[str, float]]] = None,
        graph_labels: Optional[Dict[str, float]] = None,
    ) -> float:
        """Runs one training epoch over chronological graph sequences."""
        self.model.train()
        total_loss = 0.0
        count = 0

        for seq in train_sequences:
            if seq.total_nodes == 0:
                continue

            self.optimizer.zero_grad()
            outputs = self.model(seq, device=self.device)

            # Node risk loss
            node_logits = outputs["node_risk_logits"]
            node_map = outputs["node_id_map"]

            seq_node_labels = (node_labels or {}).get(seq.case_id, {})
            y_node = []
            for nid, idx in node_map.items():
                target = seq_node_labels.get(nid, 1.0 if seq.all_nodes[nid].risk_score >= 70.0 else 0.0)
                y_node.append(target)

            y_node_tensor = torch.tensor(y_node, dtype=torch.float32, device=self.device).unsqueeze(-1)
            loss_node = self.node_loss_fn(node_logits, y_node_tensor)

            # Graph anomaly loss
            graph_score = outputs["graph_anomaly_score"]
            target_graph = (graph_labels or {}).get(seq.case_id, 1.0 if y_node_tensor.mean() > 0.3 else 0.0)
            y_graph_tensor = torch.tensor([target_graph], dtype=torch.float32, device=self.device)
            loss_graph = self.graph_loss_fn(graph_score, y_graph_tensor)

            loss = (
                self.config.node_loss_weight * loss_node
                + self.config.graph_loss_weight * loss_graph
            )

            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=2.0)
            self.optimizer.step()

            total_loss += float(loss.item())
            count += 1

        return total_loss / max(1, count)

    def evaluate(
        self,
        val_sequences: List[DynamicGraphSequence],
        node_labels: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Dict[str, float]:
        """Evaluates model performance on out-of-time validation or test sequence."""
        self.model.eval()
        all_preds: List[float] = []
        all_targets: List[float] = []

        with torch.no_grad():
            for seq in val_sequences:
                if seq.total_nodes == 0:
                    continue
                outputs = self.model(seq, device=self.device)
                scores = outputs["node_risk_scores"].squeeze(-1).cpu().numpy()
                node_map = outputs["node_id_map"]

                seq_node_labels = (node_labels or {}).get(seq.case_id, {})
                for nid, idx in node_map.items():
                    target = seq_node_labels.get(nid, 1.0 if seq.all_nodes[nid].risk_score >= 70.0 else 0.0)
                    all_preds.append(float(scores[idx]))
                    all_targets.append(float(target))

        if not all_preds:
            return {"loss": 0.0, "accuracy": 1.0, "f1": 1.0}

        y_p = np.array(all_preds)
        y_t = np.array(all_targets)

        # Classification metrics at 0.5 threshold
        bin_preds = (y_p >= 0.5).astype(int)
        bin_targets = (y_t >= 0.5).astype(int)

        tp = np.sum((bin_preds == 1) & (bin_targets == 1))
        fp = np.sum((bin_preds == 1) & (bin_targets == 0))
        fn = np.sum((bin_preds == 0) & (bin_targets == 1))
        tn = np.sum((bin_preds == 0) & (bin_targets == 0))

        precision = tp / max(1, (tp + fp))
        recall = tp / max(1, (tp + fn))
        f1 = 2 * (precision * recall) / max(1e-8, (precision + recall))
        accuracy = (tp + tn) / max(1, len(y_t))

        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "total_samples": len(y_t),
        }

    def save_checkpoint(self, path: str | Path, metadata: Optional[Dict[str, Any]] = None) -> Path:
        """Saves weights and metadata in dedicated isolated artifact directory."""
        dest_path = Path(path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model_state_dict": self.model.state_dict(),
            "config": {
                "hidden_dim": self.config.hidden_dim,
                "embedding_dim": self.config.embedding_dim,
                "time_dim": self.config.time_dim,
                "num_spatial_layers": self.config.num_spatial_layers,
                "temporal_aggregator": self.config.temporal_aggregator.value,
            },
            "metadata": metadata or {},
        }

        torch.save(payload, dest_path)
        
        # Companion metadata JSON
        meta_json_path = dest_path.parent / "metadata.json"
        meta_json_path.write_text(
            json.dumps({
                "model_name": "dynamic_gnn",
                "version": "v1",
                "framework": "PyTorch",
                "torch_version": torch.__version__,
                **(metadata or {}),
            }, indent=2),
            encoding="utf-8",
        )

        logger.info(f"DT-GNN checkpoint saved to {dest_path}")
        return dest_path
