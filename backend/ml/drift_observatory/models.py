"""Pydantic contracts and data representations for Graph & Model Drift Observatory."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .config import (
    DRIFT_OBSERVATORY_SCHEMA_VERSION,
    GENERAL_DRIFT_DISCLAIMER,
    BaselineType,
    DriftDomain,
    DriftMetricType,
    DriftSeverity,
    ObservationStatus,
)


class BaselineWindow(BaseModel):
    """Specification of the reference baseline temporal and sample bounds."""
    start_timestamp: Optional[str] = Field(default=None, description="ISO timestamp of reference start")
    end_timestamp: Optional[str] = Field(default=None, description="ISO timestamp of reference end")
    sample_count: int = Field(default=0, description="Total sample observations in reference")
    data_digest: str = Field(..., description="Deterministic SHA-256 digest of reference data")


class ComparisonWindow(BaseModel):
    """Specification of the comparison operational window bounds."""
    start_timestamp: Optional[str] = Field(default=None, description="ISO timestamp of comparison start")
    end_timestamp: Optional[str] = Field(default=None, description="ISO timestamp of comparison end")
    sample_count: int = Field(default=0, description="Total sample observations in comparison")
    data_digest: str = Field(..., description="Deterministic SHA-256 digest of comparison data")


class ReferenceBaseline(BaseModel):
    """Registered and frozen baseline for drift comparison."""
    baseline_id: str = Field(..., description="Unique deterministic identifier of the baseline")
    domain: DriftDomain = Field(..., description="Observed domain (GRAPH, FEATURE, etc.)")
    target_name: str = Field(..., description="Target model, entity type, feature, or feed name")
    baseline_type: BaselineType = Field(default=BaselineType.FIXED_SNAPSHOT)
    created_at: str = Field(..., description="ISO creation timestamp")
    schema_version: str = Field(default=DRIFT_OBSERVATORY_SCHEMA_VERSION)
    model_version: Optional[str] = Field(default=None, description="Model version if applicable")
    feature_schema_version: Optional[str] = Field(default=None)
    graph_layer: Optional[str] = Field(default=None, description="Graph layer (e.g. NCRB or EVIDENCE)")
    window: BaselineWindow
    feature_distributions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Frozen statistical representations (quantiles, frequencies, bins)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)


class DriftDimensionDelta(BaseModel):
    """Specific dimensional delta contributing to overall drift."""
    dimension_name: str
    reference_value: Any
    comparison_value: Any
    delta_percentage: Optional[float] = None
    delta_absolute: Optional[float] = None
    interpretation: Optional[str] = None


class DriftExplanation(BaseModel):
    """Non-causal plain-language and dimensional explanation of detected drift."""
    summary: str = Field(..., description="Objective summary of detected distribution shift")
    dimension_deltas: List[DriftDimensionDelta] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)


class DriftObservationRecord(BaseModel):
    """
    Immutable observation record of a single measured drift assessment.
    
    CRITICAL PROVENANCE INVARIANT:
    drift_observation_id is derived strictly from canonical analytical inputs
    (domain, target, reference baseline, comparison digest, metric, algorithm version,
    and policy version) without any computation timestamp dependency.
    """
    drift_observation_id: str = Field(..., description="Deterministic analytical identity hash")
    domain: DriftDomain
    target_name: str
    parent_target: Optional[str] = Field(default=None, description="Parent model, graph, or feed")
    metric_name: DriftMetricType
    metric_value: Optional[float] = Field(default=None, description="Calculated divergence scalar")
    reference_baseline_id: str
    reference_window: BaselineWindow
    comparison_window: ComparisonWindow
    severity: DriftSeverity
    status: ObservationStatus = Field(default=ObservationStatus.COMPLETED)
    is_statistically_valid: bool = Field(default=True)
    threshold_policy_version: str = Field(default="1.0.0")
    threshold_applied: Optional[float] = Field(default=None)
    algorithm_version: str = Field(default="1.0.0")
    explanation: DriftExplanation
    computed_at: str = Field(..., description="Temporal execution timestamp (separate from ID)")
    run_id: Optional[str] = Field(default=None, description="Optional execution run identifier")
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)


class DomainDriftSummary(BaseModel):
    """Aggregated status and drift health for an individual domain."""
    domain: DriftDomain
    status: ObservationStatus
    highest_severity: DriftSeverity
    active_alerts_count: int
    total_observations: int
    insufficient_data_count: int = 0
    data_unavailable_count: int = 0
    target_summaries: Dict[str, Any] = Field(default_factory=dict)


class ObservatoryOverview(BaseModel):
    """Global system-level overview across all 5 drift observatory domains."""
    observatory_version: str
    computed_at: str
    active_baselines_count: int
    total_observations_count: int
    global_highest_severity: DriftSeverity
    domain_summaries: Dict[str, DomainDriftSummary]
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)


# ============================================================
# API Request / Response Models
# ============================================================
class BaselineRegistrationRequest(BaseModel):
    domain: DriftDomain
    target_name: str
    baseline_type: BaselineType = BaselineType.FIXED_SNAPSHOT
    model_version: Optional[str] = None
    feature_schema_version: Optional[str] = None
    graph_layer: Optional[str] = None
    data_payload: Optional[List[Any]] = None
    feature_distributions: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DriftComputeRequest(BaseModel):
    domain: DriftDomain
    target_name: str
    baseline_id: Optional[str] = None
    comparison_data: Optional[List[Any]] = None
    comparison_window_start: Optional[str] = None
    comparison_window_end: Optional[str] = None
    metric_type: Optional[DriftMetricType] = None
    custom_policy_version: Optional[str] = None


class BaselineListResponse(BaseModel):
    total: int
    baselines: List[ReferenceBaseline]
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)


class ObservationListResponse(BaseModel):
    total: int
    observations: List[DriftObservationRecord]
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)


class ObservatoryHealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    active_baselines: int
    total_observations: int
    domains_monitored: List[str]
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)


class GraphDriftResponse(BaseModel):
    target_graph: str
    observation: DriftObservationRecord
    topology_summary: Dict[str, Any]
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)


class ModelDriftResponse(BaseModel):
    model_name: str
    model_version: Optional[str] = None
    feature_drift_observations: List[DriftObservationRecord]
    output_drift_observation: Optional[DriftObservationRecord] = None
    overall_severity: DriftSeverity
    disclaimer: str = Field(default=GENERAL_DRIFT_DISCLAIMER)
