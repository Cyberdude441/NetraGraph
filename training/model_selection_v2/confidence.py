"""
Confidence & Uncertainty Estimation Engine for NetraGraph Model Selection V2.
Evaluates domain detection reliability, posterior margins, prediction entropy, and safety fallback triggers.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from training.model_selection_v2.config import MIN_MODEL_CONFIDENCE_THRESHOLD
except ImportError:
    from config import MIN_MODEL_CONFIDENCE_THRESHOLD


class ConfidenceTier(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


@dataclass
class ConfidenceReport:
    composite_confidence: float
    domain_confidence: float
    model_confidence: float
    prediction_margin: float
    prediction_entropy: float
    confidence_tier: ConfidenceTier
    requires_fallback: bool
    reason: str


class ConfidenceEvaluator:
    """Evaluates routing and model prediction confidence."""

    def evaluate_confidence(
        self,
        domain_confidence: float,
        model_probas: np.ndarray,
    ) -> ConfidenceReport:
        """
        Compute composite confidence from domain alignment and prediction posteriors.
        """
        if model_probas.ndim == 1:
            probas = model_probas.reshape(1, -1)
        else:
            probas = model_probas

        if len(probas) == 0:
            return ConfidenceReport(
                composite_confidence=0.0,
                domain_confidence=round(domain_confidence, 4),
                model_confidence=0.5,
                prediction_margin=0.0,
                prediction_entropy=1.0,
                confidence_tier=ConfidenceTier.LOW_CONFIDENCE,
                requires_fallback=True,
                reason="Empty input payload provided; triggered safety fallback.",
            )

        top_prob = float(np.max(probas))
        sorted_probs = np.sort(probas[0])[::-1]
        second_prob = float(sorted_probs[1]) if len(sorted_probs) > 1 else 0.0
        margin = float(top_prob - second_prob)

        # Shannon Entropy
        p_safe = np.clip(probas[0], 1e-9, 1.0)
        entropy = float(-np.sum(p_safe * np.log2(p_safe)))

        # Composite Score: 40% Domain Match + 40% Top Model Posterior + 20% Margin
        comp_conf = (0.40 * domain_confidence) + (0.40 * top_prob) + (0.20 * margin)
        comp_conf = float(np.clip(comp_conf, 0.0, 1.0))

        if comp_conf >= 0.80:
            tier = ConfidenceTier.HIGH_CONFIDENCE
            req_fallback = False
            reason = "Strong domain alignment and decisive prediction margin."
        elif comp_conf >= 0.60:
            tier = ConfidenceTier.MEDIUM_CONFIDENCE
            req_fallback = False
            reason = "Adequate domain alignment with moderate posterior confidence."
        else:
            tier = ConfidenceTier.LOW_CONFIDENCE
            req_fallback = True
            reason = f"Composite confidence {comp_conf:.3f} below safety threshold {MIN_MODEL_CONFIDENCE_THRESHOLD}."

        return ConfidenceReport(
            composite_confidence=round(comp_conf, 4),
            domain_confidence=round(domain_confidence, 4),
            model_confidence=round(top_prob, 4),
            prediction_margin=round(margin, 4),
            prediction_entropy=round(entropy, 4),
            confidence_tier=tier,
            requires_fallback=req_fallback,
            reason=reason,
        )
