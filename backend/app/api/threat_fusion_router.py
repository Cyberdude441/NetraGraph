"""FastAPI router exposing Neuro-Symbolic Threat Fusion & Explainable Intelligence endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Path, status
from pydantic import BaseModel, Field

from ml.threat_fusion.assessment import ThreatAssessment
from ml.threat_fusion.config import FUSION_VERSION, RULE_SET_VERSION
from ml.threat_fusion.service import threat_fusion_service
from ml.threat_fusion.signals import SignalSeverity, SignalSource, ThreatSignal

router = APIRouter(prefix="/threat-fusion", tags=["Threat Fusion & Explainability"])


class SignalInput(BaseModel):
    source: SignalSource = Field(..., description="Origin source category (e.g. model_a_e, dt_gnn, graph_anomaly)")
    signal_type: str = Field(..., description="Specific signal indicator name")
    score: Optional[float] = Field(default=0.50, description="Normalized risk score [0, 1] or null if missing")
    confidence: Optional[float] = Field(default=0.80, ge=0.0, le=1.0, description="Confidence in signal [0, 1]")
    timestamp: Optional[float] = Field(default=0.0, description="Observation epoch seconds")
    explanation: Optional[str] = Field(default="Analytical indicator", description="Descriptive finding")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    provenance_id: Optional[str] = None


class ThreatFusionAnalyzeRequest(BaseModel):
    target_id: str = Field(..., description="Entity or Network ID being evaluated")
    target_type: Optional[str] = Field(default="entity", description="'entity' or 'network'")
    signals: List[SignalInput] = Field(..., description="Collection of intelligence signals")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional environmental or case context")


class ThreatFusionHealthResponse(BaseModel):
    status: str
    fusion_version: str
    rule_set_version: str
    registered_rules_count: int
    rule_categories: List[str]


@router.get("/health", response_model=ThreatFusionHealthResponse, status_code=status.HTTP_200_OK)
def get_threat_fusion_health() -> ThreatFusionHealthResponse:
    """Returns operational health and versioning of the Threat Fusion Engine."""
    rules = threat_fusion_service.rule_engine.rules
    categories = sorted(list({r.category for r in rules}))
    return ThreatFusionHealthResponse(
        status="ONLINE",
        fusion_version=FUSION_VERSION,
        rule_set_version=RULE_SET_VERSION,
        registered_rules_count=len(rules),
        rule_categories=categories,
    )


@router.post("/analyze", response_model=ThreatAssessment, status_code=status.HTTP_200_OK)
def analyze_threat_fusion(payload: ThreatFusionAnalyzeRequest) -> ThreatAssessment:
    """Performs deterministic neuro-symbolic threat fusion and generates an explainable assessment."""
    threat_signals: List[ThreatSignal] = []

    for s_in in payload.signals:
        sig = ThreatSignal(
            source=s_in.source,
            entity_id=payload.target_id,
            signal_type=s_in.signal_type,
            score=s_in.score,
            confidence=s_in.confidence if s_in.confidence is not None else 0.80,
            timestamp=s_in.timestamp or 0.0,
            explanation=s_in.explanation or "Analytical indicator",
            metadata=s_in.metadata or {},
            provenance_id=s_in.provenance_id,
        )
        threat_signals.append(sig)

    return threat_fusion_service.assess_target(
        target_id=payload.target_id,
        signals=threat_signals,
        context=payload.context,
        target_type=payload.target_type or "entity",
    )


@router.post("/entity/{entity_id}", response_model=ThreatAssessment, status_code=status.HTTP_200_OK)
def analyze_entity_threat(
    entity_id: str = Path(..., description="Target Entity Identifier"),
    signals: Optional[List[SignalInput]] = None,
) -> ThreatAssessment:
    """Performs threat fusion for an entity combining explicit signals or default baseline signals."""
    input_signals: List[ThreatSignal] = []

    if signals:
        for s_in in signals:
            input_signals.append(
                ThreatSignal(
                    source=s_in.source,
                    entity_id=entity_id,
                    signal_type=s_in.signal_type,
                    score=s_in.score,
                    confidence=s_in.confidence if s_in.confidence is not None else 0.80,
                    timestamp=s_in.timestamp or 0.0,
                    explanation=s_in.explanation or "Analytical indicator",
                    metadata=s_in.metadata or {},
                    provenance_id=s_in.provenance_id,
                )
            )

    return threat_fusion_service.assess_target(
        target_id=entity_id,
        signals=input_signals,
        target_type="entity",
    )
