"""Configuration, constants, enums, and versioned threshold policy defaults for Drift Observatory."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


DRIFT_OBSERVATORY_VERSION: str = "1.0.0"
DRIFT_OBSERVATORY_SCHEMA_VERSION: str = "1.0.0"
DEFAULT_ALGORITHM_VERSION: str = "1.0.0"

# ============================================================
# Centralized Mandatory Disclaimers
# ============================================================
GENERAL_DRIFT_DISCLAIMER: str = (
    "Drift metrics are operational telemetry and statistical signals indicating data or "
    "distribution variance relative to a reference baseline. Drift does not establish "
    "criminality, culpability, or malice, nor does it automatically indicate model failure."
)

CTI_OSINT_DRIFT_DISCLAIMER: str = (
    "External threat intelligence and OSINT are analytical decision-support inputs. "
    "They do not constitute definitive proof of culpability, criminal intent, or guilt under law."
)


# ============================================================
# Enums
# ============================================================
class DriftDomain(str, Enum):
    """The 5 primary observable domains."""
    GRAPH = "GRAPH"
    FEATURE = "FEATURE"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    CTI_SOURCE = "CTI_SOURCE"
    DATA_QUALITY = "DATA_QUALITY"


class DriftSeverity(str, Enum):
    """Operational significance of detected statistical drift."""
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"


class DriftMetricType(str, Enum):
    """Statistical and divergence metrics supported by the observatory."""
    PSI = "POPULATION_STABILITY_INDEX"
    JSD = "JENSEN_SHANNON_DIVERGENCE"
    WASSERSTEIN = "WASSERSTEIN_DISTANCE"
    KS = "KOLMOGOROV_SMIRNOV"
    MISSINGNESS_DELTA = "MISSINGNESS_RATE_DELTA"
    TOPOLOGY_DELTA = "TOPOLOGY_DELTA"


class BaselineType(str, Enum):
    """Mode of the reference baseline."""
    FIXED_SNAPSHOT = "FIXED_SNAPSHOT"
    ROLLING_WINDOW = "ROLLING_WINDOW"


class ObservationStatus(str, Enum):
    """Execution status of a drift observation."""
    COMPLETED = "COMPLETED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    INCOMPATIBLE_BASELINE = "INCOMPATIBLE_BASELINE"


# ============================================================
# Versioned Drift Threshold Policy
# ============================================================
@dataclass
class DriftThresholdPolicy:
    """
    Versioned, configurable operational threshold policy defaults.
    
    CRITICAL ARCHITECTURAL CONVENTION:
    These values represent initial configurable policy defaults and operational guidelines,
    NOT objective truth or immutable scientific law. They must be recorded with every observation
    and are never self-modified by the drift engine.
    """
    policy_version: str = "1.0.0"

    # Population Stability Index (PSI) Initial Configurable Policy Defaults
    psi_watch: float = 0.10
    psi_elevated: float = 0.20
    psi_critical: float = 0.35

    # Jensen-Shannon Divergence (JSD) Initial Configurable Policy Defaults [0.0, 1.0]
    jsd_watch: float = 0.15
    jsd_elevated: float = 0.30
    jsd_critical: float = 0.50

    # Missingness Rate Delta Initial Configurable Policy Defaults [0.0, 1.0]
    missingness_watch: float = 0.05
    missingness_elevated: float = 0.15
    missingness_critical: float = 0.30

    # Kolmogorov-Smirnov 2-sample statistic Initial Configurable Policy Defaults [0.0, 1.0]
    ks_watch: float = 0.15
    ks_elevated: float = 0.30
    ks_critical: float = 0.50

    # Wasserstein Distance normalized shift relative to baseline scale
    wasserstein_relative_watch: float = 0.20
    wasserstein_relative_elevated: float = 0.50
    wasserstein_relative_critical: float = 1.00

    # Policy Resource & Sample Limits
    min_sample_size: int = 30
    max_samples_per_compute: int = 50000
    max_comparison_window_days: int = 365
    default_page_size: int = 20
    max_page_size: int = 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "psi": {"watch": self.psi_watch, "elevated": self.psi_elevated, "critical": self.psi_critical},
            "jsd": {"watch": self.jsd_watch, "elevated": self.jsd_elevated, "critical": self.jsd_critical},
            "missingness_delta": {"watch": self.missingness_watch, "elevated": self.missingness_elevated, "critical": self.missingness_critical},
            "ks": {"watch": self.ks_watch, "elevated": self.ks_elevated, "critical": self.ks_critical},
            "min_sample_size": self.min_sample_size,
            "max_samples_per_compute": self.max_samples_per_compute,
            "max_comparison_window_days": self.max_comparison_window_days,
        }
