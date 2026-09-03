"""Feature extraction, categorical embeddings, and Models A-E fusion layers."""
from __future__ import annotations

from typing import Dict, List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import DTGNNConfig, ModelFusionConfig
from .data import DynamicGraphSequence, ENTITY_TYPE_VOCAB, RELATIONSHIP_TYPE_VOCAB, TemporalNode


class NodeFeatureEncoder(nn.Module):
    """Encodes heterogeneous entity types and continuous features into unified representations."""

    def __init__(self, config: DTGNNConfig):
        super().__init__()
        self.config = config
        
        # Categorical embedding for entity types (9 standard types + Unknown = 10)
        self.type_embedding = nn.Embedding(
            num_embeddings=len(ENTITY_TYPE_VOCAB),
            embedding_dim=config.node_categorical_dim,
        )

        # Continuous feature projection
        # Features: [riskScore/100, confidence, in_degree_norm, out_degree_norm, has_preds_flag, extra1, extra2, extra3]
        self.continuous_proj = nn.Linear(
            in_features=config.node_continuous_dim,
            out_features=config.node_categorical_dim,
        )

        # Models A-E Fusion Projection
        # 5 Models: intrusion, network-intrusion, phishing-url, webpage-phishing, phishing-email
        self.fusion_enabled = config.model_fusion.enabled
        if self.fusion_enabled:
            num_models = len(config.model_fusion.model_names)
            self.model_fusion_proj = nn.Sequential(
                nn.Linear(num_models, config.model_fusion.fusion_dim),
                nn.ReLU(),
                nn.Dropout(config.model_fusion.dropout),
            )
            combined_input_dim = (
                config.node_categorical_dim * 2 + config.model_fusion.fusion_dim
            )
        else:
            combined_input_dim = config.node_categorical_dim * 2

        # Final node feature projection to hidden_dim
        self.out_proj = nn.Sequential(
            nn.Linear(combined_input_dim, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
        )

    def extract_node_feature_matrix(
        self,
        sequence: DynamicGraphSequence,
        device: torch.device,
    ) -> torch.Tensor:
        """Constructs raw feature tensors for all nodes in the sequence and projects to hidden_dim."""
        num_nodes = sequence.total_nodes
        if num_nodes == 0:
            return torch.zeros((0, self.config.hidden_dim), device=device)

        type_indices: List[int] = []
        continuous_features: List[List[float]] = []
        model_pred_features: List[List[float]] = []

        model_keys = self.config.model_fusion.model_names

        for nid in sequence.all_node_ids:
            node = sequence.all_nodes[nid]
            type_indices.append(node.type_idx())

            # Continuous features: [norm_risk, confidence, extra...]
            norm_risk = float(node.risk_score) / 100.0
            conf = float(node.confidence)
            has_preds = 1.0 if node.model_predictions else 0.0

            cont_row = [norm_risk, conf, has_preds, 0.0, 0.0, 0.0, 0.0, 0.0]
            continuous_features.append(cont_row)

            # Models A-E predictions (optional 5-dim vector)
            pred_row: List[float] = []
            for mk in model_keys:
                pred_val = node.model_predictions.get(mk)
                if pred_val is not None:
                    # Convert to float probability 0.0-1.0
                    try:
                        p_float = float(pred_val)
                    except (ValueError, TypeError):
                        p_float = 0.5
                    pred_row.append(max(0.0, min(1.0, p_float)))
                else:
                    pred_row.append(0.0)  # Zero-padded when model prediction is absent
            model_pred_features.append(pred_row)

        type_tensor = torch.tensor(type_indices, dtype=torch.long, device=device)
        cont_tensor = torch.tensor(continuous_features, dtype=torch.float32, device=device)
        pred_tensor = torch.tensor(model_pred_features, dtype=torch.float32, device=device)

        return self.forward(type_tensor, cont_tensor, pred_tensor)

    def forward(
        self,
        type_idx: torch.Tensor,
        continuous_feats: torch.Tensor,
        model_preds: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        type_emb = self.type_embedding(type_idx)
        cont_emb = self.continuous_proj(continuous_feats)

        parts = [type_emb, cont_emb]

        if self.fusion_enabled:
            if model_preds is None:
                batch_size = type_idx.size(0)
                num_models = len(self.config.model_fusion.model_names)
                model_preds = torch.zeros((batch_size, num_models), device=type_idx.device)
            fusion_emb = self.model_fusion_proj(model_preds)
            parts.append(fusion_emb)

        combined = torch.cat(parts, dim=-1)
        return self.out_proj(combined)


class EdgeFeatureEncoder(nn.Module):
    """Encodes heterogeneous relationship types and interaction features."""

    def __init__(self, config: DTGNNConfig):
        super().__init__()
        self.config = config

        self.rel_embedding = nn.Embedding(
            num_embeddings=len(RELATIONSHIP_TYPE_VOCAB),
            embedding_dim=config.edge_categorical_dim,
        )

        self.continuous_proj = nn.Linear(
            in_features=config.edge_continuous_dim,
            out_features=config.edge_categorical_dim,
        )

        self.out_proj = nn.Sequential(
            nn.Linear(config.edge_categorical_dim * 2, config.hidden_dim),
            nn.LayerNorm(config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
        )

    def forward(
        self,
        rel_types: torch.Tensor,
        edge_attrs: torch.Tensor,
    ) -> torch.Tensor:
        if rel_types.numel() == 0:
            return torch.zeros((0, self.config.hidden_dim), device=rel_types.device)

        rel_emb = self.rel_embedding(rel_types)
        attr_emb = self.continuous_proj(edge_attrs)
        combined = torch.cat([rel_emb, attr_emb], dim=-1)
        return self.out_proj(combined)
