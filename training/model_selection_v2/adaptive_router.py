"""
Adaptive Router Gateway V2 for NetraGraph.
End-to-end domain-aware inference router integrating profiling, representations, model selection, confidence, and explainability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

try:
    from training.model_selection_v2.confidence import ConfidenceEvaluator, ConfidenceReport
    from training.model_selection_v2.config import RepresentationType, SecurityDomain
    from training.model_selection_v2.domain_profiler import DomainProfileResult, DomainProfiler
    from training.model_selection_v2.domain_selector import DomainSelectionDecision, DomainSelector
    from training.model_selection_v2.explainability import ExplainabilityEngine
    from training.model_selection_v2.feature_router import FeatureRouter, FeatureRoutingResult
    from training.model_selection_v2.model_registry import CandidateModelWrapper, ModelRegistryV2
except ImportError:
    from confidence import ConfidenceEvaluator, ConfidenceReport
    from config import RepresentationType, SecurityDomain
    from domain_profiler import DomainProfileResult, DomainProfiler
    from domain_selector import DomainSelectionDecision, DomainSelector
    from explainability import ExplainabilityEngine
    from feature_router import FeatureRouter, FeatureRoutingResult
    from model_registry import CandidateModelWrapper, ModelRegistryV2


@dataclass
class AdaptiveRouterV2Result:
    predictions: np.ndarray
    probabilities: np.ndarray
    domain: SecurityDomain
    representation_used: RepresentationType
    selected_model: str
    is_fallback_active: bool
    confidence_report: ConfidenceReport
    explanation: Dict[str, Any]
    feature_dimension: int


class AdaptiveRouterV2:
    """
    Domain-Aware Adaptive Router Gateway V2.
    """

    def __init__(
        self,
        profiler: Optional[DomainProfiler] = None,
        feature_router: Optional[FeatureRouter] = None,
        selector: Optional[DomainSelector] = None,
        model_registry: Optional[ModelRegistryV2] = None,
        confidence_evaluator: Optional[ConfidenceEvaluator] = None,
        explainer: Optional[ExplainabilityEngine] = None,
    ):
        self.profiler = profiler or DomainProfiler()
        self.feature_router = feature_router or FeatureRouter(profiler=self.profiler)
        self.selector = selector or DomainSelector()
        self.model_registry = model_registry or ModelRegistryV2()
        self.confidence_evaluator = confidence_evaluator or ConfidenceEvaluator()
        self.explainer = explainer or ExplainabilityEngine()

        # Cache of fitted domain models
        self.active_models: Dict[str, CandidateModelWrapper] = {}

    def register_fitted_model(self, domain_or_model_key: str, model_wrapper: CandidateModelWrapper) -> None:
        """Register a pre-trained domain model."""
        self.active_models[domain_or_model_key] = model_wrapper

    def route_and_predict(
        self,
        X: Union[pd.DataFrame, Dict[str, Any], np.ndarray],
        forced_representation: Optional[RepresentationType] = None,
        forced_model: Optional[str] = None,
    ) -> AdaptiveRouterV2Result:
        """
        Execute full domain-aware routing and inference pipeline.
        """
        # 1. Route and Transform Features
        routing_res: FeatureRoutingResult = self.feature_router.route_features(
            X=X, forced_representation=forced_representation
        )
        domain = routing_res.domain_profile.domain
        repr_used = routing_res.representation_used

        # 2. Select Optimal Model Architecture
        if domain == SecurityDomain.UNKNOWN_DOMAIN:
            decision = self.selector.select_model_for_domain(SecurityDomain.NETWORK_INTRUSION)
            chosen_model_name = forced_model or decision.fallback_model
            is_fallback = True
        else:
            decision = self.selector.select_model_for_domain(domain)
            chosen_model_name = forced_model or decision.selected_model
            is_fallback = routing_res.is_fallback

        # 3. Model Inference
        model_key = f"{domain.value}_{chosen_model_name}"
        if model_key in self.active_models:
            model = self.active_models[model_key]
        else:
            # Retrieve or instantiate from registry
            is_multi = (domain == SecurityDomain.MALWARE_ATTRIBUTION)
            model = self.model_registry.get_candidate_model(chosen_model_name, is_multiclass=is_multi)

        probas = model.predict_proba(routing_res.X_transformed)
        preds = np.argmax(probas, axis=1)

        # 4. Confidence Evaluation
        conf_report = self.confidence_evaluator.evaluate_confidence(
            domain_confidence=routing_res.domain_profile.confidence,
            model_probas=probas,
        )

        # 5. Check if Low-Confidence Safety Fallback Triggered
        if conf_report.requires_fallback and not is_fallback:
            is_fallback = True
            chosen_model_name = decision.fallback_model

        # 6. Generate Explainability Trace
        explanation = self.explainer.explain_routing_decision(
            domain_profile=routing_res.domain_profile,
            selection_decision=decision,
            confidence_report=conf_report,
            representation_used=repr_used.value,
            is_fallback_active=is_fallback,
        )

        return AdaptiveRouterV2Result(
            predictions=preds,
            probabilities=probas,
            domain=domain,
            representation_used=repr_used,
            selected_model=chosen_model_name,
            is_fallback_active=is_fallback,
            confidence_report=conf_report,
            explanation=explanation,
            feature_dimension=routing_res.feature_dim,
        )
