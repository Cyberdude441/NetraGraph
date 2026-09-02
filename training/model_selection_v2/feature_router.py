"""
Feature Router Module for NetraGraph Model Selection V2.
Directs inputs through the domain-selected representation pipeline with robust safety guards.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd

try:
    from training.model_selection_v2.config import RepresentationType, SecurityDomain
    from training.model_selection_v2.domain_profiler import DomainProfileResult, DomainProfiler
    from training.model_selection_v2.representation_registry import BaseRepresentation, RepresentationRegistry
except ImportError:
    from config import RepresentationType, SecurityDomain
    from domain_profiler import DomainProfileResult, DomainProfiler
    from representation_registry import BaseRepresentation, RepresentationRegistry


@dataclass
class FeatureRoutingResult:
    X_transformed: np.ndarray
    representation_used: RepresentationType
    domain_profile: DomainProfileResult
    is_fallback: bool
    feature_dim: int


class FeatureRouter:
    """
    Directs input data through domain-specific representation transformers.
    """

    def __init__(self, registry: Optional[RepresentationRegistry] = None, profiler: Optional[DomainProfiler] = None):
        self.registry = registry or RepresentationRegistry()
        self.profiler = profiler or DomainProfiler()

    def route_features(
        self,
        X: Union[pd.DataFrame, Dict[str, Any], np.ndarray],
        forced_representation: Optional[RepresentationType] = None,
    ) -> FeatureRoutingResult:
        """
        Profile input, select representation, and transform feature matrix.
        """
        # 1. Normalize input to DataFrame
        if isinstance(X, dict):
            df = pd.DataFrame([X])
        elif isinstance(X, np.ndarray):
            df = pd.DataFrame(X, columns=[f"f_{i}" for i in range(X.shape[1])])
        elif isinstance(X, pd.DataFrame):
            df = X
        else:
            raise TypeError(f"Unsupported data type for routing: {type(X)}")

        # 2. Profile Domain
        profile = self.profiler.profile_dataset(df)

        # 3. Determine Representation
        if forced_representation is not None:
            repr_type = forced_representation
            is_fallback = False
        elif profile.is_ambiguous:
            repr_type = RepresentationType.FALLBACK_TABULAR_V1
            is_fallback = True
        else:
            repr_type = profile.recommended_representation
            is_fallback = False

        # 4. Transform Matrix
        transformer: BaseRepresentation = self.registry.get_representation(repr_type)
        try:
            X_trans = transformer.transform(df)
        except Exception:
            # Safe fallback if domain transformer fails on anomalous input
            fallback_transformer = self.registry.get_representation(RepresentationType.FALLBACK_TABULAR_V1)
            X_trans = fallback_transformer.transform(df)
            repr_type = RepresentationType.FALLBACK_TABULAR_V1
            is_fallback = True

        return FeatureRoutingResult(
            X_transformed=X_trans,
            representation_used=repr_type,
            domain_profile=profile,
            is_fallback=is_fallback,
            feature_dim=X_trans.shape[1] if X_trans.ndim > 1 else 1,
        )
