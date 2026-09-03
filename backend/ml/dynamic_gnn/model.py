"""Dynamic Temporal Graph Neural Network (DT-GNN) PyTorch Model Architecture."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import DTGNNConfig
from .data import DynamicGraphSequence
from .features import EdgeFeatureEncoder, NodeFeatureEncoder
from .temporal import BochnerHarmonicTimeEncoder, TemporalSequenceAggregator


class RelationalSpatialGraphConv(nn.Module):
    """Spatial Graph Convolution Layer with relational edge conditioning and attention weighting."""

    def __init__(self, hidden_dim: int, time_dim: int, dropout: float = 0.1):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # Message projection layers
        self.w_src = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.w_dst = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.w_edge = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.w_time = nn.Linear(time_dim, hidden_dim, bias=False)

        # Attention vector
        self.attn_vec = nn.Parameter(torch.empty(hidden_dim))
        nn.init.xavier_uniform_(self.attn_vec.unsqueeze(0))

        # Node update
        self.w_val = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.update_proj = nn.Linear(hidden_dim * 2, hidden_dim)
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        node_emb: torch.Tensor,
        edge_index: torch.Tensor,
        edge_emb: torch.Tensor,
        edge_time_emb: torch.Tensor,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Args:

        node_emb: (N, hidden_dim)
        edge_index: (2, E) where edge_index[0] is source, edge_index[1] is target
        edge_emb: (E, hidden_dim)
        edge_time_emb: (E, time_dim)
        Returns:
            updated_node_emb: (N, hidden_dim)
            edge_attention: (E,)
        """
        N = node_emb.size(0)
        E = edge_index.size(1)

        if E == 0 or N == 0:
            # Graph with no edges
            return node_emb, None

        src_idx = edge_index[0]
        dst_idx = edge_index[1]

        h_src = self.w_src(node_emb[src_idx])
        h_dst = self.w_dst(node_emb[dst_idx])
        h_edge = self.w_edge(edge_emb)
        h_time = self.w_time(edge_time_emb)

        # Joint relational message vector
        m_ij = F.leaky_relu(h_src + h_dst + h_edge + h_time, negative_slope=0.2)
        
        # Unnormalized attention score: e_ij = m_ij * attn_vec
        scores = (m_ij * self.attn_vec).sum(dim=-1)  # (E,)

        # Numerically stable destination-based softmax using scatter_add
        # For pure PyTorch without torch_geometric dependency:
        max_scores = torch.zeros(N, device=node_emb.device).fill_(-1e9)
        max_scores.scatter_reduce_(0, dst_idx, scores, reduce="amax", include_self=False)
        max_scores = torch.where(max_scores == -1e9, torch.zeros_like(max_scores), max_scores)
        
        exp_scores = torch.exp(scores - max_scores[dst_idx])
        sum_exp = torch.zeros(N, device=node_emb.device).scatter_add(0, dst_idx, exp_scores)
        sum_exp = torch.clamp(sum_exp, min=1e-12)
        alpha = exp_scores / sum_exp[dst_idx]  # (E,) Normalized attention

        alpha_drop = self.dropout(alpha)

        # Message passing aggregation: sum_{i \in N(j)} alpha_ij * W_val * h_i
        val_src = self.w_val(node_emb[src_idx]) * alpha_drop.unsqueeze(-1)
        aggregated = torch.zeros((N, self.hidden_dim), device=node_emb.device)
        aggregated.index_add_(0, dst_idx, val_src)

        # Residual connection and layer normalization
        combined = torch.cat([node_emb, aggregated], dim=-1)
        updated = self.layer_norm(node_emb + self.dropout(F.gelu(self.update_proj(combined))))

        return updated, alpha


class DynamicTemporalGNN(nn.Module):
    """Deep Dynamic Temporal Graph Neural Network."""

    def __init__(self, config: Optional[DTGNNConfig] = None):
        super().__init__()
        self.config = config or DTGNNConfig()

        # 1. Feature encoders
        self.node_encoder = NodeFeatureEncoder(self.config)
        self.edge_encoder = EdgeFeatureEncoder(self.config)
        self.time_encoder = BochnerHarmonicTimeEncoder(self.config.time_dim)

        # 2. Spatial Convolutional Stacks
        self.spatial_layers = nn.ModuleList([
            RelationalSpatialGraphConv(
                hidden_dim=self.config.hidden_dim,
                time_dim=self.config.time_dim,
                dropout=self.config.dropout,
            )
            for _ in range(self.config.num_spatial_layers)
        ])

        # 3. Temporal Sequence Aggregator
        self.temporal_aggregator = TemporalSequenceAggregator(self.config)

        # 4. Multi-task Readout Heads
        # A. Node Threat Risk Head: outputs (N, 1) probability in [0, 1]
        self.node_risk_head = nn.Sequential(
            nn.Linear(self.config.hidden_dim, self.config.hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(self.config.dropout),
            nn.Linear(self.config.hidden_dim // 2, 1),
        )

        # B. Edge Link Risk Head: outputs (E, 1) suspicious connection score
        self.edge_risk_head = nn.Sequential(
            nn.Linear(self.config.hidden_dim * 2 + self.config.hidden_dim, self.config.hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(self.config.dropout),
            nn.Linear(self.config.hidden_dim // 2, 1),
        )

        # C. Global Graph Anomaly & Network Representation Head
        self.graph_attention_pool = nn.Linear(self.config.hidden_dim, 1)
        self.graph_embedding_head = nn.Sequential(
            nn.Linear(self.config.hidden_dim, self.config.embedding_dim),
            nn.LayerNorm(self.config.embedding_dim),
        )
        self.graph_anomaly_head = nn.Sequential(
            nn.Linear(self.config.embedding_dim, self.config.hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(self.config.hidden_dim // 4, 1),
        )

    def encode_snapshot(
        self,
        node_embeddings: torch.Tensor,
        snapshot_tensors: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Applies multi-layer spatial relational graph convolution on a single snapshot."""
        edge_index = snapshot_tensors["edge_index"]
        edge_attr = snapshot_tensors["edge_attr"]
        edge_type = snapshot_tensors["edge_type"]
        edge_time = snapshot_tensors["edge_time"]

        edge_emb = self.edge_encoder(edge_type, edge_attr)
        edge_time_emb = self.time_encoder(edge_time)

        h = node_embeddings
        last_attention = None

        for layer in self.spatial_layers:
            h, last_attention = layer(h, edge_index, edge_emb, edge_time_emb)

        return h, last_attention

    def forward(
        self,
        sequence: DynamicGraphSequence,
        device: Optional[torch.device] = None,
    ) -> Dict[str, Any]:
        """Full forward pass across temporal graph snapshots.

        Returns:
            dict containing:
                node_risk_scores: Tensor (N, 1)
                graph_embedding: Tensor (embedding_dim,)
                graph_anomaly_score: Tensor (1,)
                snapshot_representations: List of snapshot node embeddings
                last_edge_attention: Tensor (E,) or None
        """
        if device is None:
            device = next(self.parameters()).device

        num_nodes = sequence.total_nodes
        if num_nodes == 0:
            # Handle empty sequence gracefully
            return {
                "node_risk_scores": torch.zeros((0, 1), device=device),
                "graph_embedding": torch.zeros((self.config.embedding_dim,), device=device),
                "graph_anomaly_score": torch.tensor([0.0], device=device),
                "dynamic_node_embeddings": torch.zeros((0, self.config.hidden_dim), device=device),
                "last_edge_attention": None,
                "node_id_map": {},
            }

        node_map = sequence.node_id_map()

        # 1. Base node representations
        base_node_emb = self.node_encoder.extract_node_feature_matrix(sequence, device=device)

        # 2. Iterate through snapshots
        snapshot_representations: List[torch.Tensor] = []
        snapshot_timestamps: List[float] = []
        last_attention = None

        if sequence.sequence_length == 0:
            snapshot_representations.append(base_node_emb)
            snapshot_timestamps.append(0.0)
        else:
            for snap in sequence.snapshots:
                snap_tensors = snap.to_tensors(node_map)
                snap_tensors = {k: v.to(device) for k, v in snap_tensors.items()}
                h_snap, last_attention = self.encode_snapshot(base_node_emb, snap_tensors)
                snapshot_representations.append(h_snap)
                snapshot_timestamps.append(snap.timestamp_end)

        # 3. Temporal Sequence Aggregation
        dynamic_node_emb = self.temporal_aggregator(
            snapshot_representations,
            snapshot_timestamps=snapshot_timestamps,
        )

        # 4. Multi-task Readouts
        # Node threat risk scores in [0, 1]
        node_risk_logits = self.node_risk_head(dynamic_node_emb)
        node_risk_scores = torch.sigmoid(node_risk_logits)

        # Global Graph Anomaly & Network Embedding
        # Attention-weighted pooling over nodes
        pool_weights = F.softmax(self.graph_attention_pool(dynamic_node_emb), dim=0)
        pooled_graph = (pool_weights * dynamic_node_emb).sum(dim=0)  # (hidden_dim,)

        graph_embedding = self.graph_embedding_head(pooled_graph)  # (embedding_dim,)
        graph_anomaly_score = torch.sigmoid(self.graph_anomaly_head(graph_embedding))

        return {
            "node_risk_scores": node_risk_scores,
            "node_risk_logits": node_risk_logits,
            "graph_embedding": graph_embedding,
            "graph_anomaly_score": graph_anomaly_score,
            "dynamic_node_embeddings": dynamic_node_emb,
            "last_edge_attention": last_attention,
            "node_id_map": node_map,
        }

    def score_edges(
        self,
        dynamic_node_emb: torch.Tensor,
        edge_index: torch.Tensor,
        edge_emb: torch.Tensor,
    ) -> torch.Tensor:
        """Scores pairwise edges for suspicious/anomalous interactions."""
        if edge_index.size(1) == 0:
            return torch.zeros((0, 1), device=dynamic_node_emb.device)

        src_idx = edge_index[0]
        dst_idx = edge_index[1]

        h_u = dynamic_node_emb[src_idx]
        h_v = dynamic_node_emb[dst_idx]

        combined = torch.cat([h_u, h_v, edge_emb], dim=-1)
        edge_risk_logits = self.edge_risk_head(combined)
        return torch.sigmoid(edge_risk_logits)
