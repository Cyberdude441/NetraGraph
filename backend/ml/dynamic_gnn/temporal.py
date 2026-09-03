"""Temporal encoding and sequence aggregation for Dynamic Temporal GNNs."""
from __future__ import annotations

import math
from typing import List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import DTGNNConfig, TemporalAggregatorType, TemporalEncodingType


class BochnerHarmonicTimeEncoder(nn.Module):
    """Continuous-time harmonic positional encoder based on Bochner's theorem.

    Maps continuous time differences Delta t into high-dimensional periodic embeddings:
    Phi(Delta t) = [cos(omega_1 * Delta t), sin(omega_1 * Delta t), ..., cos(omega_k * Delta t), sin(omega_k * Delta t)]
    """

    def __init__(self, time_dim: int):
        super().__init__()
        self.time_dim = time_dim
        half_dim = time_dim // 2

        # Initialize exponential frequencies
        # omega_i = 1 / (10000 ** (2i / d))
        freqs = torch.exp(
            torch.arange(0, half_dim, dtype=torch.float32)
            * -(math.log(10000.0) / max(1, half_dim - 1))
        )
        self.register_buffer("frequencies", freqs)
        self.proj = nn.Linear(time_dim, time_dim)

    def forward(self, delta_t: torch.Tensor) -> torch.Tensor:
        """Args:

        delta_t: Tensor of shape (..., ) representing elapsed seconds or normalized time.
        Returns:
            Tensor of shape (..., time_dim)
        """
        if delta_t.dim() == 0:
            delta_t = delta_t.unsqueeze(0)

        # Reshape to (..., 1)
        t_unsqueezed = delta_t.unsqueeze(-1)
        angles = t_unsqueezed * self.frequencies  # (..., half_dim)

        cos_part = torch.cos(angles)
        sin_part = torch.sin(angles)

        encoded = torch.cat([cos_part, sin_part], dim=-1)  # (..., time_dim)
        return self.proj(encoded)


class TemporalSequenceAggregator(nn.Module):
    """Aggregates node embeddings across sequential graph snapshots [G_0, G_1, ..., G_{T-1}]."""

    def __init__(self, config: DTGNNConfig):
        super().__init__()
        self.config = config
        self.aggregator_type = config.temporal_aggregator
        self.hidden_dim = config.hidden_dim

        if self.aggregator_type == TemporalAggregatorType.GRU:
            self.cell = nn.GRUCell(input_size=config.hidden_dim, hidden_size=config.hidden_dim)
        elif self.aggregator_type == TemporalAggregatorType.ATTENTION:
            self.mha = nn.MultiheadAttention(
                embed_dim=config.hidden_dim,
                num_heads=4,
                dropout=config.dropout,
                batch_first=True,
            )
            self.norm = nn.LayerNorm(config.hidden_dim)
        else:
            # Fallback mean / decay
            self.decay_lambda = nn.Parameter(torch.tensor(config.time_decay_lambda))

    def forward(
        self,
        snapshot_node_embeddings: List[torch.Tensor],
        snapshot_timestamps: Optional[List[float]] = None,
    ) -> torch.Tensor:
        """Args:

        snapshot_node_embeddings: List of T tensors, each of shape (N, hidden_dim).
        snapshot_timestamps: List of T floats representing timestamps.
        Returns:
            Final dynamic node embeddings of shape (N, hidden_dim).
        """
        num_snapshots = len(snapshot_node_embeddings)
        if num_snapshots == 0:
            raise ValueError("Cannot aggregate empty snapshot sequence")

        if num_snapshots == 1:
            return snapshot_node_embeddings[0]

        num_nodes = snapshot_node_embeddings[0].size(0)
        device = snapshot_node_embeddings[0].device

        if self.aggregator_type == TemporalAggregatorType.GRU:
            # Sequential recurrence across snapshots
            h_t = torch.zeros((num_nodes, self.hidden_dim), device=device)
            for x_t in snapshot_node_embeddings:
                h_t = self.cell(x_t, h_t)
            return h_t

        elif self.aggregator_type == TemporalAggregatorType.ATTENTION:
            # Stack into (N, T, hidden_dim)
            seq_tensor = torch.stack(snapshot_node_embeddings, dim=1)
            # Self-attention across time axis
            attn_out, _ = self.mha(seq_tensor, seq_tensor, seq_tensor)
            seq_tensor = self.norm(seq_tensor + attn_out)
            # Take the representation at the most recent snapshot T-1
            return seq_tensor[:, -1, :]

        else:
            # Time-decay weighted pooling
            if snapshot_timestamps is not None and len(snapshot_timestamps) == num_snapshots:
                t_max = snapshot_timestamps[-1]
                weights = [
                    math.exp(-abs(self.config.time_decay_lambda) * max(0.0, t_max - ts))
                    for ts in snapshot_timestamps
                ]
                w_sum = sum(weights)
                norm_weights = [w / w_sum for w in weights]
            else:
                norm_weights = [1.0 / num_snapshots] * num_snapshots

            out = torch.zeros_like(snapshot_node_embeddings[0])
            for w, emb in zip(norm_weights, snapshot_node_embeddings):
                out = out + w * emb
            return out
