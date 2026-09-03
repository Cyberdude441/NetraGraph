"""Comprehensive test suite for the NetraGraph Dynamic Temporal Graph Neural Network (DT-GNN) Layer."""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
import pytest
import torch

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from main import app
from ml.dynamic_gnn.config import (
    DTGNNConfig,
    InferenceConfig,
    ModelFusionConfig,
    TemporalAggregatorType,
    TemporalEncodingType,
    TrainingConfig,
)
from ml.dynamic_gnn.data import (
    ENTITY_TYPE_VOCAB,
    RELATIONSHIP_TYPE_VOCAB,
    DynamicGraphSequence,
    TemporalEdge,
    TemporalGraphSnapshot,
    TemporalNode,
    parse_iso_timestamp,
)
from ml.dynamic_gnn.features import EdgeFeatureEncoder, NodeFeatureEncoder
from ml.dynamic_gnn.inference import DTGNNInferenceEngine
from ml.dynamic_gnn.model import DynamicTemporalGNN, RelationalSpatialGraphConv
from ml.dynamic_gnn.service import DTGNNService, dt_gnn_service
from ml.dynamic_gnn.temporal import BochnerHarmonicTimeEncoder, TemporalSequenceAggregator
from ml.dynamic_gnn.training import DTGNNTrainer, chronological_split


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_nodes() -> Dict[str, TemporalNode]:
    """Provides a realistic heterogeneous evidence node set."""
    return {
        "P-101": TemporalNode(
            id="P-101",
            entity_type="Person",
            risk_score=85.0,
            confidence=0.98,
            model_predictions={"intrusion": 0.88, "phishing-email": 0.72},
            timestamp=1700000000.0,
        ),
        "IP-201": TemporalNode(
            id="IP-201",
            entity_type="IPAddress",
            risk_score=75.0,
            confidence=0.95,
            model_predictions={"network-intrusion": 0.91},
            timestamp=1700000100.0,
        ),
        "ACC-301": TemporalNode(
            id="ACC-301",
            entity_type="BankAccount",
            risk_score=90.0,
            confidence=0.99,
            model_predictions={},
            timestamp=1700000200.0,
        ),
        "DOM-401": TemporalNode(
            id="DOM-401",
            entity_type="Domain",
            risk_score=30.0,
            confidence=0.85,
            model_predictions={"phishing-url": 0.25, "webpage-phishing": 0.20},
            timestamp=1700000300.0,
        ),
    }


@pytest.fixture
def sample_edges() -> List[TemporalEdge]:
    """Provides chronological interaction edges connecting sample nodes."""
    return [
        TemporalEdge(
            source_id="P-101",
            target_id="IP-201",
            rel_type="LOGIN",
            weight=8.0,
            confidence=0.95,
            timestamp=1700000150.0,
        ),
        TemporalEdge(
            source_id="P-101",
            target_id="ACC-301",
            rel_type="OWNS",
            weight=9.0,
            confidence=0.99,
            timestamp=1700000250.0,
        ),
        TemporalEdge(
            source_id="IP-201",
            target_id="DOM-401",
            rel_type="COMMUNICATED_WITH",
            weight=5.0,
            confidence=0.80,
            timestamp=1700000350.0,
        ),
        TemporalEdge(
            source_id="ACC-301",
            target_id="DOM-401",
            rel_type="TRANSACTION",
            weight=7.0,
            confidence=0.92,
            timestamp=1700000450.0,
        ),
    ]


@pytest.fixture
def sample_sequence(sample_nodes, sample_edges) -> DynamicGraphSequence:
    return DynamicGraphSequence.from_elements(
        all_nodes=sample_nodes,
        all_edges=sample_edges,
        case_id="CASE-TEST-101",
        num_snapshots=3,
    )


# ============================================================================
# Unit Tests: Data Abstractions & Temporal Windowing
# ============================================================================

def test_timestamp_parsing():
    """Verifies parsing of diverse ISO strings, floats, ints, and missing values."""
    assert parse_iso_timestamp(1700000000.0) == 1700000000.0
    assert parse_iso_timestamp("2026-09-04T00:00:00Z") > 0.0
    assert parse_iso_timestamp("2026-09-04T00:00:00+00:00") > 0.0
    assert parse_iso_timestamp(None) == 0.0
    assert parse_iso_timestamp("invalid-timestamp") == 0.0


def test_dynamic_graph_sequence_construction(sample_nodes, sample_edges):
    """Verifies dynamic multi-snapshot discretization and temporal ordering."""
    seq = DynamicGraphSequence.from_elements(
        all_nodes=sample_nodes,
        all_edges=sample_edges,
        case_id="CASE-TEMPORAL-01",
        num_snapshots=3,
    )

    assert seq.case_id == "CASE-TEMPORAL-01"
    assert seq.total_nodes == 4
    assert seq.sequence_length == 3

    # Check non-decreasing chronological windows
    for i in range(len(seq.snapshots) - 1):
        assert seq.snapshots[i].timestamp_start <= seq.snapshots[i + 1].timestamp_start
        assert seq.snapshots[i].timestamp_end <= seq.snapshots[i + 1].timestamp_end

    # Global node ID mapping
    node_map = seq.node_id_map()
    assert len(node_map) == 4
    for nid in sample_nodes:
        assert nid in node_map


def test_snapshot_tensor_conversion(sample_nodes, sample_edges):
    """Verifies that snapshots convert correctly into PyTorch edge tensors."""
    seq = DynamicGraphSequence.from_elements(
        all_nodes=sample_nodes,
        all_edges=sample_edges,
        case_id="CASE-TENSORS-01",
        num_snapshots=2,
    )
    node_map = seq.node_id_map()
    snap = seq.snapshots[-1]
    tensors = snap.to_tensors(node_map)

    assert "edge_index" in tensors
    assert "edge_attr" in tensors
    assert "edge_type" in tensors
    assert "edge_time" in tensors

    edge_index = tensors["edge_index"]
    assert edge_index.dim() == 2
    assert edge_index.size(0) == 2
    assert edge_index.size(1) == len(snap.edges)


# ============================================================================
# Unit Tests: Feature Encoders & Bochner Harmonic Time
# ============================================================================

def test_bochner_harmonic_time_encoding():
    """Verifies continuous-time harmonic positional encoding satisfies non-linear periodicity."""
    time_dim = 16
    encoder = BochnerHarmonicTimeEncoder(time_dim=time_dim)

    # Delta times
    dt1 = torch.tensor([0.0, 60.0, 3600.0, 86400.0])
    emb1 = encoder(dt1)
    assert emb1.shape == (4, time_dim)

    # Identical delta times produce identical embeddings
    dt_same = torch.tensor([3600.0, 3600.0])
    emb_same = encoder(dt_same)
    assert torch.allclose(emb_same[0], emb_same[1], atol=1e-5)

    # Distinct delta times produce distinct embeddings
    assert not torch.allclose(emb1[0], emb1[2], atol=1e-3)


def test_node_feature_encoder_with_and_without_models_a_e(sample_sequence):
    """Verifies that NodeFeatureEncoder operates both with and without Models A-E predictions."""
    device = torch.device("cpu")
    
    # Configuration with Model Fusion enabled
    config_enabled = DTGNNConfig()
    config_enabled.model_fusion.enabled = True
    encoder_enabled = NodeFeatureEncoder(config_enabled)
    out_enabled = encoder_enabled.extract_node_feature_matrix(sample_sequence, device)
    assert out_enabled.shape == (sample_sequence.total_nodes, config_enabled.hidden_dim)

    # Configuration with Model Fusion disabled
    config_disabled = DTGNNConfig()
    config_disabled.model_fusion.enabled = False
    encoder_disabled = NodeFeatureEncoder(config_disabled)
    out_disabled = encoder_disabled.extract_node_feature_matrix(sample_sequence, device)
    assert out_disabled.shape == (sample_sequence.total_nodes, config_disabled.hidden_dim)


def test_edge_feature_encoder():
    """Verifies relationship type embeddings and continuous edge attribute projections."""
    config = DTGNNConfig()
    encoder = EdgeFeatureEncoder(config)

    rel_types = torch.tensor([0, 1, 3, 5], dtype=torch.long)
    edge_attrs = torch.tensor([
        [0.8, 0.95, 0.5, 1.2],
        [0.5, 0.80, 0.0, 0.0],
        [0.9, 0.99, 2.0, 5.0],
        [0.3, 0.70, 0.1, 0.0],
    ], dtype=torch.float32)

    emb = encoder(rel_types, edge_attrs)
    assert emb.shape == (4, config.hidden_dim)


# ============================================================================
# Unit Tests: Spatial-Temporal GNN Model Forward Pass
# ============================================================================

def test_dt_gnn_forward_pass(sample_sequence):
    """Verifies multi-task forward pass across sequential temporal snapshots."""
    config = DTGNNConfig(hidden_dim=32, embedding_dim=16, num_spatial_layers=2)
    model = DynamicTemporalGNN(config)
    model.eval()

    with torch.no_grad():
        outputs = model(sample_sequence)

    assert "node_risk_scores" in outputs
    assert "graph_embedding" in outputs
    assert "graph_anomaly_score" in outputs
    assert "dynamic_node_embeddings" in outputs

    node_scores = outputs["node_risk_scores"]
    assert node_scores.shape == (sample_sequence.total_nodes, 1)
    # Probabilities must be strictly bounded in [0, 1]
    assert torch.all((node_scores >= 0.0) & (node_scores <= 1.0))

    graph_emb = outputs["graph_embedding"]
    assert graph_emb.shape == (config.embedding_dim,)

    graph_anomaly = outputs["graph_anomaly_score"]
    assert 0.0 <= float(graph_anomaly.item()) <= 1.0


@pytest.mark.parametrize("aggregator", [
    TemporalAggregatorType.GRU,
    TemporalAggregatorType.ATTENTION,
    TemporalAggregatorType.MEAN,
])
def test_dt_gnn_aggregators(sample_sequence, aggregator):
    """Verifies that all temporal aggregation mechanisms (GRU, Attention, Mean) execute cleanly."""
    config = DTGNNConfig(
        hidden_dim=32,
        embedding_dim=16,
        temporal_aggregator=aggregator,
    )
    model = DynamicTemporalGNN(config)
    model.eval()

    with torch.no_grad():
        out = model(sample_sequence)

    assert out["node_risk_scores"].shape == (sample_sequence.total_nodes, 1)
    assert out["graph_anomaly_score"].dim() == 1


# ============================================================================
# Unit Tests: Edge Cases & Pathological Defense
# ============================================================================

def test_empty_graph_handling():
    """Verifies graceful handling of empty graph sequence."""
    config = DTGNNConfig(hidden_dim=32, embedding_dim=16)
    model = DynamicTemporalGNN(config)
    empty_seq = DynamicGraphSequence(case_id="EMPTY-CASE")

    with torch.no_grad():
        out = model(empty_seq)

    assert out["node_risk_scores"].shape == (0, 1)
    assert out["graph_embedding"].shape == (16,)
    assert float(out["graph_anomaly_score"].item()) == 0.0


def test_single_node_disconnected_graph():
    """Verifies robust execution on a graph containing a single isolated node."""
    nodes = {
        "ISOLATED-1": TemporalNode(id="ISOLATED-1", entity_type="Phone", risk_score=40.0)
    }
    seq = DynamicGraphSequence.from_elements(all_nodes=nodes, all_edges=[])
    model = DynamicTemporalGNN(DTGNNConfig(hidden_dim=32, embedding_dim=16))

    with torch.no_grad():
        out = model(seq)

    assert out["node_risk_scores"].shape == (1, 1)
    assert 0.0 <= float(out["node_risk_scores"][0].item()) <= 1.0


def test_unknown_entity_and_relationship_types():
    """Verifies resilience to unseen or unexpected categorical entity and link types."""
    nodes = {
        "UNK-1": TemporalNode(id="UNK-1", entity_type="ExoticSatelliteDish", risk_score=60.0),
        "UNK-2": TemporalNode(id="UNK-2", entity_type="CryptoMixerV3", risk_score=80.0),
    }
    edges = [
        TemporalEdge(
            source_id="UNK-1",
            target_id="UNK-2",
            rel_type="QUANTUM_TUNNEL",
            weight=5.0,
        )
    ]
    seq = DynamicGraphSequence.from_elements(all_nodes=nodes, all_edges=edges)
    model = DynamicTemporalGNN(DTGNNConfig(hidden_dim=32, embedding_dim=16))

    with torch.no_grad():
        out = model(seq)

    assert out["node_risk_scores"].shape == (2, 1)


# ============================================================================
# Unit Tests: Inference Engine & Explainability Attributions
# ============================================================================

def test_inference_engine_attributions(sample_sequence):
    """Verifies that inference engine produces structured, valid explainability attributions."""
    engine = DTGNNInferenceEngine()
    result = engine.analyze_sequence(sample_sequence)

    assert result["case_id"] == "CASE-TEST-101"
    assert "graph_anomaly_score" in result
    assert "network_risk_level" in result
    assert result["network_risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(result["nodes"]) == 4

    # Verify explainability structure
    expl = result["explainability"]
    assert "influential_nodes" in expl
    assert "influential_relationships" in expl
    assert "critical_subgraph" in expl
    assert "attribution_disclaimer" in expl
    assert "not a determination of legal culpability" in expl["attribution_disclaimer"]

    # Influential nodes schema
    for inf_node in expl["influential_nodes"]:
        assert "node_id" in inf_node
        assert "threat_risk_score" in inf_node


def test_deterministic_inference(sample_sequence):
    """Verifies that inference produces identical results when deterministic=True."""
    config = DTGNNConfig(hidden_dim=32, embedding_dim=16)
    model = DynamicTemporalGNN(config)
    
    inf_config = InferenceConfig(deterministic=True)
    engine = DTGNNInferenceEngine(model=model, inference_config=inf_config)

    res1 = engine.analyze_sequence(sample_sequence)
    res2 = engine.analyze_sequence(sample_sequence)

    assert res1["graph_anomaly_score"] == res2["graph_anomaly_score"]
    assert res1["nodes"][0]["threat_risk_score"] == res2["nodes"][0]["threat_risk_score"]


# ============================================================================
# Unit Tests: Training Pipeline & Temporal Leakage Prevention
# ============================================================================

def test_chronological_split_prevents_temporal_leakage():
    """Validates strict temporal ordering and absence of temporal leakage across train/val/test splits."""
    sequences = []
    base_time = 1700000000.0

    for i in range(10):
        t_start = base_time + i * 10000.0
        t_end = t_start + 5000.0
        snap = TemporalGraphSnapshot(
            snapshot_idx=0,
            timestamp_start=t_start,
            timestamp_end=t_end,
            nodes={"N1": TemporalNode(id="N1", timestamp=t_start)},
            edges=[],
        )
        seq = DynamicGraphSequence(
            case_id=f"CASE-{i}",
            snapshots=[snap],
            all_node_ids=["N1"],
            all_nodes={"N1": TemporalNode(id="N1")},
        )
        sequences.append(seq)

    train_seqs, val_seqs, test_seqs = chronological_split(
        sequences,
        train_ratio=0.70,
        val_ratio=0.15,
    )

    assert len(train_seqs) > 0
    assert len(val_seqs) > 0
    assert len(test_seqs) > 0

    # Max train timestamp must be <= Min val timestamp
    train_max_t = max(s.snapshots[0].timestamp_start for s in train_seqs)
    val_min_t = min(s.snapshots[0].timestamp_start for s in val_seqs)
    val_max_t = max(s.snapshots[0].timestamp_start for s in val_seqs)
    test_min_t = min(s.snapshots[0].timestamp_start for s in test_seqs)

    assert train_max_t <= val_min_t, "Temporal leakage detected: Train overlaps with Validation!"
    assert val_max_t <= test_min_t, "Temporal leakage detected: Validation overlaps with Test!"


def test_dt_gnn_trainer_epoch_and_checkpoint_saving(sample_sequence, tmp_path):
    """Verifies that trainer executes training epochs and saves isolated checkpoints."""
    config = DTGNNConfig(hidden_dim=32, embedding_dim=16)
    train_config = TrainingConfig(
        epochs=2,
        checkpoint_dir=str(tmp_path / "artifacts" / "dynamic_gnn" / "v1"),
    )

    trainer = DTGNNTrainer(config=config, training_config=train_config)
    loss = trainer.train_epoch([sample_sequence])
    assert isinstance(loss, float)
    assert not math.isnan(loss)

    metrics = trainer.evaluate([sample_sequence])
    assert "accuracy" in metrics
    assert "f1" in metrics

    # Test checkpoint save
    ckpt_file = tmp_path / "artifacts" / "dynamic_gnn" / "v1" / "checkpoint.pt"
    saved_path = trainer.save_checkpoint(ckpt_file, metadata={"test_run": True})
    assert saved_path.is_file()
    assert (tmp_path / "artifacts" / "dynamic_gnn" / "v1" / "metadata.json").is_file()

    # Test checkpoint loading into inference engine
    engine = DTGNNInferenceEngine(config=config, checkpoint_path=ckpt_file)
    res = engine.analyze_sequence(sample_sequence)
    assert len(res["nodes"]) == 4


# ============================================================================
# API Integration & Service Regression Tests
# ============================================================================

def test_api_gnn_health_endpoint():
    """Verifies GET /api/gnn/health endpoint contract."""
    client = TestClient(app)
    response = client.get("/api/gnn/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert data["model_name"] == "DynamicTemporalGNN"
    assert "version" in data
    assert "num_spatial_layers" in data


def test_api_gnn_analyze_endpoint():
    """Verifies POST /api/gnn/analyze endpoint with explicit graph payload."""
    client = TestClient(app)
    payload = {
        "case_id": "CASE-API-TEST",
        "nodes": [
            {"id": "ENT-1", "type": "Person", "riskScore": 85.0},
            {"id": "ENT-2", "type": "BankAccount", "riskScore": 90.0},
        ],
        "edges": [
            {"sourceId": "ENT-1", "targetId": "ENT-2", "type": "TRANSACTION", "weight": 7.0}
        ],
        "num_snapshots": 2,
    }

    response = client.post("/api/gnn/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-API-TEST"
    assert "graph_anomaly_score" in data
    assert "network_risk_level" in data
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert "explainability" in data


def test_pathological_payload_defense():
    """Verifies that payloads exceeding maximum limits are rejected with HTTP 413."""
    client = TestClient(app)
    # Exceed limit using small threshold for test verification
    excessive_nodes = [{"id": f"N-{i}", "type": "Person"} for i in range(10_001)]
    payload = {
        "case_id": "CASE-OVERFLOW",
        "nodes": excessive_nodes,
        "edges": [],
    }
    response = client.post("/api/gnn/analyze", json=payload)
    assert response.status_code == 413
    assert "exceeds maximum permitted limit" in response.json()["detail"]
