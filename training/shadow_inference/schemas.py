"""
Standardized research-only schemas for NetraGraph Shadow Inference.

These data contracts are strictly isolated from production and provide stable
representations for parallel shadow evaluation, telemetry, and reporting.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


@dataclass
class ProductionResult:
    """Read-only result from production Models A–E execution."""
    model: str
    prediction: Union[str, int, float]
    risk_score: float
    latency_ms: float
    model_version: str = "v1"
    raw_output: Dict[str, Any] = field(default_factory=dict)
    status: str = "SUCCESS"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "prediction": str(self.prediction),
            "risk_score": round(float(self.risk_score), 4),
            "latency_ms": round(float(self.latency_ms), 4),
            "model_version": self.model_version,
            "status": self.status,
            "error": self.error,
        }


@dataclass
class AdaptiveResult:
    """Result from adaptive model selection and parallel research inference."""
    model: str
    selection_confidence: float
    prediction: Union[str, int, float]
    risk_score: float
    rationale: str
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    selection_latency_ms: float = 0.0
    inference_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    dataset_family: str = "unknown"
    task_type: str = "unknown"
    status: str = "SUCCESS"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "selection_confidence": round(float(self.selection_confidence), 4),
            "prediction": str(self.prediction),
            "risk_score": round(float(self.risk_score), 4),
            "rationale": self.rationale,
            "alternatives": self.alternatives,
            "selection_latency_ms": round(float(self.selection_latency_ms), 4),
            "inference_latency_ms": round(float(self.inference_latency_ms), 4),
            "total_latency_ms": round(float(self.total_latency_ms), 4),
            "dataset_family": self.dataset_family,
            "task_type": self.task_type,
            "status": self.status,
            "error": self.error,
        }


@dataclass
class ComparisonResult:
    """Comparison metrics between production and adaptive results."""
    prediction_agreement: bool
    risk_delta: float
    model_changed: bool
    production_model: str
    adaptive_model: str
    production_prediction: str
    adaptive_prediction: str
    latency_delta_ms: float
    disagreement_severity: str = "NONE"  # NONE, LOW, MEDIUM, CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_agreement": bool(self.prediction_agreement),
            "risk_delta": round(float(self.risk_delta), 4),
            "model_changed": bool(self.model_changed),
            "production_model": self.production_model,
            "adaptive_model": self.adaptive_model,
            "production_prediction": self.production_prediction,
            "adaptive_prediction": self.adaptive_prediction,
            "latency_delta_ms": round(float(self.latency_delta_ms), 4),
            "disagreement_severity": self.disagreement_severity,
        }


@dataclass
class ShadowResult:
    """Complete Shadow Inference result container."""
    request_id: str
    timestamp: str
    dataset_name: str
    production: ProductionResult
    adaptive: AdaptiveResult
    comparison: ComparisonResult
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "dataset_name": self.dataset_name,
            "production": self.production.to_dict(),
            "adaptive": self.adaptive.to_dict(),
            "comparison": self.comparison.to_dict(),
            "metadata": self.metadata,
        }


@dataclass
class DriftReport:
    """Distribution drift detection telemetry."""
    feature_psi: Dict[str, float]
    overall_feature_psi: float
    feature_ks_pvalues: Dict[str, float]
    prediction_distribution_shift: float
    confidence_shift: float
    drift_severity: str  # LOW, MEDIUM, HIGH
    sample_size_reference: int
    sample_size_current: int
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_psi": {k: round(float(v), 5) for k, v in self.feature_psi.items()},
            "overall_feature_psi": round(float(self.overall_feature_psi), 5),
            "feature_ks_pvalues": {k: round(float(v), 5) for k, v in self.feature_ks_pvalues.items()},
            "prediction_distribution_shift": round(float(self.prediction_distribution_shift), 5),
            "confidence_shift": round(float(self.confidence_shift), 5),
            "drift_severity": self.drift_severity,
            "sample_size_reference": self.sample_size_reference,
            "sample_size_current": self.sample_size_current,
            "evaluated_at": self.evaluated_at,
        }


@dataclass
class AggregateShadowReport:
    """Comprehensive evaluation summary across a dataset or evaluation run."""
    dataset_name: str
    sample_count: int
    agreement_rate: float
    disagreement_rate: float
    mean_risk_delta: float
    median_risk_delta: float
    production_metrics: Dict[str, Any]
    adaptive_metrics: Dict[str, Any]
    metrics_delta: Dict[str, Any]
    latency_summary: Dict[str, Any]
    model_selection_distribution: Dict[str, float]
    drift_summary: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
