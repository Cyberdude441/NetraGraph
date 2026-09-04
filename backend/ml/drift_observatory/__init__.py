"""NetraGraph Graph & Model Drift Observatory (Phase 16).

Provides investigator- and developer-facing observability and decision support
for structural graph changes, model input/output divergence, CTI feed behavior,
and data quality shifts with strict provenance and mandatory non-causal disclaimers.
"""
from __future__ import annotations

from .baselines import BaselineRegistry, IncompatibleBaselineError, baseline_registry
from .config import (
    CTI_OSINT_DRIFT_DISCLAIMER,
    DEFAULT_ALGORITHM_VERSION,
    DRIFT_OBSERVATORY_SCHEMA_VERSION,
    DRIFT_OBSERVATORY_VERSION,
    GENERAL_DRIFT_DISCLAIMER,
    BaselineType,
    DriftDomain,
    DriftMetricType,
    DriftSeverity,
    DriftThresholdPolicy,
    ObservationStatus,
)
from .feature_drift import FeatureDriftDetector
from .graph_drift import GraphDriftDetector
from .model_drift import ModelOutputDriftDetector
from .models import (
    BaselineListResponse,
    BaselineRegistrationRequest,
    BaselineWindow,
    ComparisonWindow,
    DomainDriftSummary,
    DriftComputeRequest,
    DriftDimensionDelta,
    DriftExplanation,
    DriftObservationRecord,
    GraphDriftResponse,
    ModelDriftResponse,
    ObservationListResponse,
    ObservatoryHealthResponse,
    ObservatoryOverview,
    ReferenceBaseline,
)
from .provenance import compute_analytical_observation_id, compute_data_digest, generate_run_id
from .quality_drift import DataQualityDriftDetector
from .service import DriftObservatoryEngine, drift_observatory_engine
from .source_drift import CTISourceDriftDetector
from .statistics import (
    compute_jsd,
    compute_ks_statistic,
    compute_missingness_delta,
    compute_psi,
    compute_wasserstein,
    deterministic_subsample,
)

__all__ = [
    "DRIFT_OBSERVATORY_VERSION",
    "DRIFT_OBSERVATORY_SCHEMA_VERSION",
    "DEFAULT_ALGORITHM_VERSION",
    "GENERAL_DRIFT_DISCLAIMER",
    "CTI_OSINT_DRIFT_DISCLAIMER",
    "DriftDomain",
    "DriftSeverity",
    "DriftMetricType",
    "BaselineType",
    "ObservationStatus",
    "DriftThresholdPolicy",
    "ReferenceBaseline",
    "BaselineWindow",
    "ComparisonWindow",
    "DriftDimensionDelta",
    "DriftExplanation",
    "DriftObservationRecord",
    "DomainDriftSummary",
    "ObservatoryOverview",
    "BaselineRegistrationRequest",
    "DriftComputeRequest",
    "ObservatoryHealthResponse",
    "GraphDriftResponse",
    "ModelDriftResponse",
    "compute_psi",
    "compute_jsd",
    "compute_wasserstein",
    "compute_ks_statistic",
    "compute_missingness_delta",
    "deterministic_subsample",
    "compute_data_digest",
    "compute_analytical_observation_id",
    "generate_run_id",
    "BaselineRegistry",
    "IncompatibleBaselineError",
    "baseline_registry",
    "GraphDriftDetector",
    "FeatureDriftDetector",
    "ModelOutputDriftDetector",
    "CTISourceDriftDetector",
    "DataQualityDriftDetector",
    "DriftObservatoryEngine",
    "drift_observatory_engine",
]
