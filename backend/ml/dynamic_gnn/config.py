"""Configuration dataclasses for the Dynamic Temporal Graph Neural Network (DT-GNN)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TemporalEncodingType(str, Enum):
    HARMONIC = "harmonic"      # Bochner's theorem sine-cosine positional embedding
    DECAY = "decay"            # Exponential recency decay
    LINEAR = "linear"          # Normalized linear temporal interval


class TemporalAggregatorType(str, Enum):
    GRU = "gru"                # Temporal Gated Recurrent Unit
    ATTENTION = "attention"    # Temporal Multi-Head Self-Attention
    MEAN = "mean"              # Time-decay weighted pooling


@dataclass
class ModelFusionConfig:
    """Configuration for optional integration with Models A-E predictions."""
    enabled: bool = True
    model_names: List[str] = field(default_factory=lambda: [
        "intrusion",
        "network-intrusion",
        "phishing-url",
        "webpage-phishing",
        "phishing-email"
    ])
    fusion_dim: int = 16
    dropout: float = 0.1


@dataclass
class DTGNNConfig:
    """Core neural architecture hyperparameters."""
    # Input Feature Dimensions
    node_categorical_dim: int = 16
    edge_categorical_dim: int = 8
    node_continuous_dim: int = 8       # e.g., risk_score, confidence, degree, pagerank, betweenness, etc.
    edge_continuous_dim: int = 4       # e.g., weight, confidence, duration, amount
    time_dim: int = 16                 # Harmonic temporal embedding dimension

    # Hidden & Output Dimensions
    hidden_dim: int = 64
    embedding_dim: int = 32
    num_spatial_layers: int = 2
    dropout: float = 0.15

    # Temporal Dynamics
    temporal_encoding: TemporalEncodingType = TemporalEncodingType.HARMONIC
    temporal_aggregator: TemporalAggregatorType = TemporalAggregatorType.GRU
    time_decay_lambda: float = 0.05
    max_snapshots: int = 20

    # Model Fusion (Models A-E optional integration)
    model_fusion: ModelFusionConfig = field(default_factory=ModelFusionConfig)

    # Multi-task Loss Weights
    node_loss_weight: float = 1.0
    edge_loss_weight: float = 0.5
    graph_loss_weight: float = 0.5
    temporal_regularization_weight: float = 0.05

    # Safety & Resource Constraints
    max_nodes_per_snapshot: int = 10_000
    max_edges_per_snapshot: int = 50_000
    device: str = "cpu"                # Default CPU inference; CUDA when available and requested


@dataclass
class TrainingConfig:
    """Isolated training pipeline hyperparameters."""
    batch_size: int = 1                # Snapshot sequences per batch
    learning_rate: float = 0.001
    weight_decay: float = 1e-4
    epochs: int = 25
    early_stopping_patience: int = 5
    chronological_train_ratio: float = 0.70
    chronological_val_ratio: float = 0.15
    chronological_test_ratio: float = 0.15
    seed: int = 42
    checkpoint_dir: str = "artifacts/dynamic_gnn/v1"


@dataclass
class InferenceConfig:
    """Inference and explainability attribution settings."""
    confidence_threshold: float = 0.5
    top_k_influential_nodes: int = 5
    top_k_influential_edges: int = 5
    explainability_enabled: bool = True
    deterministic: bool = True
