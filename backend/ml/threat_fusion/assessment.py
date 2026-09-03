"""Stable, typed Threat Assessment contract models."""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from .config import ASSESSMENT_SCHEMA_VERSION, FUSION_VERSION, RULE_SET_VERSION
from .explainability import GOVERNANCE_DISCLAIMER


class ThreatAssessment(BaseModel):
    """Unified threat assessment object combining models, graph signals, and symbolic rules."""
    assessment_id: str = Field(default_factory=lambda: f"ASM-{uuid.uuid4().hex[:12].upper()}")
    target_id: str = Field(..., description="Entity or Network identifier assessed")
    target_type: str = Field(default="entity", description="'entity' or 'network'")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Fused continuous risk score in [0, 1]")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Independent confidence score in [0, 1]")
    disagreement_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Dispersion index across input signals")
    severity: str = Field(..., description="Standardized severity: LOW, MEDIUM, HIGH, CRITICAL")
    timestamp: float = Field(default_factory=lambda: time.time())
    fusion_version: str = Field(default=FUSION_VERSION)
    rule_set_version: str = Field(default=RULE_SET_VERSION)
    schema_version: str = Field(default=ASSESSMENT_SCHEMA_VERSION)

    supporting_signals_count: int = Field(default=0)
    contradicting_signals_count: int = Field(default=0)
    triggered_rules_count: int = Field(default=0)

    signals_summary: List[Dict[str, Any]] = Field(default_factory=list)
    triggered_rules: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_chain: Dict[str, Any] = Field(default_factory=dict)
    explanation: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = Field(default=GOVERNANCE_DISCLAIMER)

    @field_validator("risk_score", "confidence_score", "disagreement_score")
    @classmethod
    def validate_bounds(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Score must be bounded between 0.0 and 1.0; got {v}")
        return round(float(v), 4)
