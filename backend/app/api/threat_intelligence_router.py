"""FastAPI router exposing Threat Intelligence, OSINT Ingestion, Correlation, and Provenance endpoints."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
import jwt

try:
    from app.auth.config import auth_config
    from app.auth.dependencies import get_token_from_request
    from ml.threat_intelligence import (
        MANDATORY_NON_CAUSAL_DISCLAIMER,
        CandidateCorrelation,
        FeedSourceMetadata,
        IOCType,
        ResolutionStatus,
        ReviewDecision,
        ReviewStatus,
        SourceTier,
        THREAT_INTEL_ENGINE_VERSION,
        THREAT_INTEL_SCHEMA_VERSION,
        ThreatConflictRecord,
        threat_intelligence_engine,
    )
except ImportError:
    from ...app.auth.config import auth_config
    from ...app.auth.dependencies import get_token_from_request
    from ...ml.threat_intelligence import (
        MANDATORY_NON_CAUSAL_DISCLAIMER,
        CandidateCorrelation,
        FeedSourceMetadata,
        IOCType,
        ResolutionStatus,
        ReviewDecision,
        ReviewStatus,
        SourceTier,
        THREAT_INTEL_ENGINE_VERSION,
        THREAT_INTEL_SCHEMA_VERSION,
        ThreatConflictRecord,
        threat_intelligence_engine,
    )

logger = logging.getLogger("ThreatIntelligenceRouter")

router = APIRouter(
    prefix="/threat-intelligence",
    tags=["Threat Intelligence & OSINT Fusion"],
)


# =============================================================================
# RBAC Clearance Dependency
# =============================================================================
def require_cti_clearance(allowed_roles: List[str]):
    """
    RBAC dependency verifying officer clearance for CTI endpoints.
    Validates JWT if present, with header fallback for test environments.
    """
    async def _checker(
        request: Request,
        x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
        x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    ) -> Dict[str, Any]:
        auth_hdr = request.headers.get("Authorization")
        token = None
        if auth_hdr and auth_hdr.startswith("Bearer "):
            token = auth_hdr[7:].strip()
        elif auth_hdr:
            token = auth_hdr.strip()
        elif auth_config.COOKIE_ACCESS_NAME in request.cookies:
            token = request.cookies.get(auth_config.COOKIE_ACCESS_NAME)

        if token:
            try:
                payload = jwt.decode(
                    token,
                    auth_config.JWT_SECRET_KEY,
                    algorithms=[auth_config.JWT_ALGORITHM],
                )
                user_roles = [r.upper() for r in payload.get("roles", ["ANALYST"])]
                user_id = payload.get("sub", "officer")
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token.",
                )
        elif x_user_role:
            user_roles = [x_user_role.upper()]
            user_id = x_user_id or "officer"
        else:
            # Default analyst tier for local execution
            user_roles = ["ANALYST"]
            user_id = "analyst-default"

        allowed_upper = [r.upper() for r in allowed_roles]
        if "ADMIN" in user_roles:
            return {"user_id": user_id, "roles": user_roles}

        if not any(r in allowed_upper for r in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of the following clearance roles: {', '.join(allowed_roles)}",
            )
        return {"user_id": user_id, "roles": user_roles}

    return _checker


# =============================================================================
# Request & Response Schemas
# =============================================================================
class IngestFeedRequest(BaseModel):
    source_name: str = Field(..., description="Reporting source/feed identifier")
    source_tier: SourceTier = Field(default=SourceTier.TIER_4_COMMUNITY_OSINT)
    payload_format: str = Field(default="json", description="json, csv, or lines")
    payload_content: str = Field(..., description="Raw feed content string")


class CorrelateEntitiesRequest(BaseModel):
    case_id: str = Field(..., description="Target investigation case ID")
    entities: List[Dict[str, Any]] = Field(..., description="List of entity dictionaries to correlate")
    reference_time: Optional[float] = Field(default=None, description="Optional simulation reference time")


class ReviewCorrelationRequest(BaseModel):
    decision: ReviewStatus = Field(..., description="ACCEPTED or REJECTED")
    analyst_id: str = Field(..., description="Reviewing officer identifier")
    justification: str = Field(..., description="Forensic rationale for decision")


# =============================================================================
# Endpoints
# =============================================================================
@router.get("/health", summary="Engine Health and Summary")
async def get_engine_health() -> Dict[str, Any]:
    """Health check returning engine version, schema versions, and feed telemetry."""
    summary = threat_intelligence_engine.get_feed_summary()
    return {
        "status": "ONLINE",
        "engine": "NetraGraph Threat Intelligence Engine",
        "engine_version": THREAT_INTEL_ENGINE_VERSION,
        "schema_version": THREAT_INTEL_SCHEMA_VERSION,
        "telemetry": summary,
        "mandatory_disclaimer": MANDATORY_NON_CAUSAL_DISCLAIMER,
    }


@router.get(
    "/feeds",
    summary="List Registered CTI Feeds",
    dependencies=[Depends(require_cti_clearance(["ANALYST", "INVESTIGATOR", "SUPERVISOR", "ADMIN"]))],
)
async def list_feeds() -> Dict[str, Any]:
    """Retrieves all registered threat intelligence feeds and credibility tiers."""
    sources = threat_intelligence_engine.source_registry.list_sources()
    return {
        "total_feeds": len(sources),
        "feeds": [s.model_dump() for s in sources],
        "mandatory_disclaimer": MANDATORY_NON_CAUSAL_DISCLAIMER,
    }


@router.post(
    "/feeds/ingest",
    summary="Ingest External Threat Intelligence Feed",
    dependencies=[Depends(require_cti_clearance(["INVESTIGATOR", "SUPERVISOR", "ADMIN"]))],
)
async def ingest_feed(req: IngestFeedRequest) -> Dict[str, Any]:
    """
    Ingests and normalizes an external CTI payload under strict resource and sanitization limits.
    Rejects oversized payloads with HTTP 413.
    """
    raw_bytes = req.payload_content.encode("utf-8")
    try:
        res = threat_intelligence_engine.ingest_external_feed(
            source_name=req.source_name,
            source_tier=req.source_tier,
            raw_bytes=raw_bytes,
            payload_format=req.payload_format,
        )
        res["mandatory_disclaimer"] = MANDATORY_NON_CAUSAL_DISCLAIMER
        return res
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "exceeds maximum limit" in str(ve) else status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as exc:
        logger.error(f"Failed to ingest CTI feed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feed ingestion error: {str(exc)}",
        )


@router.post(
    "/correlate",
    summary="Correlate Entities Against Threat Intelligence",
    dependencies=[Depends(require_cti_clearance(["ANALYST", "INVESTIGATOR", "SUPERVISOR", "ADMIN"]))],
)
async def correlate_entities(req: CorrelateEntitiesRequest) -> Dict[str, Any]:
    """Correlates a batch of case entities against indexed external intelligence."""
    try:
        matches = threat_intelligence_engine.correlate_entities(
            case_id=req.case_id,
            entities=req.entities,
            reference_time=req.reference_time,
        )
        return {
            "case_id": req.case_id,
            "total_matches": len(matches),
            "correlations": [m.model_dump() for m in matches],
            "domain_tag": "EXTERNAL_THREAT_INTEL",
            "mandatory_disclaimer": MANDATORY_NON_CAUSAL_DISCLAIMER,
        }
    except Exception as exc:
        logger.error(f"Correlation error for case {req.case_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Correlation error: {str(exc)}",
        )


@router.get(
    "/cases/{case_id}/correlations",
    summary="Get Case Threat Intel Correlations",
    dependencies=[Depends(require_cti_clearance(["ANALYST", "INVESTIGATOR", "SUPERVISOR", "ADMIN"]))],
)
async def get_case_correlations(case_id: str) -> Dict[str, Any]:
    """Retrieves all threat intelligence correlations for a specific case workspace."""
    try:
        return threat_intelligence_engine.correlate_case_workspace(case_id)
    except Exception as exc:
        logger.error(f"Failed to retrieve correlations for case {case_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Case correlation query error: {str(exc)}",
        )


@router.get(
    "/indicators/{indicator_id}/provenance",
    summary="Retrieve Indicator Provenance DAG",
    dependencies=[Depends(require_cti_clearance(["ANALYST", "INVESTIGATOR", "SUPERVISOR", "ADMIN"]))],
)
async def get_indicator_provenance(indicator_id: str) -> Dict[str, Any]:
    """Retrieves complete immutable provenance DAG and source records for an indicator."""
    try:
        return threat_intelligence_engine.get_indicator_provenance(indicator_id)
    except KeyError as ke:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ke))
    except Exception as exc:
        logger.error(f"Failed to retrieve provenance for indicator {indicator_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/conflicts",
    summary="List Cross-Feed Contradictions",
    dependencies=[Depends(require_cti_clearance(["INVESTIGATOR", "SUPERVISOR", "ADMIN"]))],
)
async def list_conflicts() -> Dict[str, Any]:
    """Inspects all detected contradictory assessments between external intelligence feeds."""
    conflicts = threat_intelligence_engine.list_conflicts()
    return {
        "total_conflicts": len(conflicts),
        "conflicts": [c.model_dump() for c in conflicts],
        "mandatory_disclaimer": MANDATORY_NON_CAUSAL_DISCLAIMER,
    }


@router.post(
    "/correlations/{correlation_id}/review",
    summary="Investigator Review Gate",
    dependencies=[Depends(require_cti_clearance(["SUPERVISOR", "ADMIN"]))],
)
async def review_correlation(
    correlation_id: str,
    req: ReviewCorrelationRequest,
) -> Dict[str, Any]:
    """
    Human-in-the-loop review gate (Option E): ACCEPT or REJECT candidate CTI correlation.
    Only ACCEPTED correlations become eligible for graph enrichment.
    """
    try:
        reviewed = threat_intelligence_engine.review_correlation(
            correlation_id=correlation_id,
            decision=req.decision,
            analyst_id=req.analyst_id,
            justification=req.justification,
        )
        return {
            "status": "SUCCESS",
            "correlation_id": correlation_id,
            "decision": req.decision.value,
            "review_status": reviewed.review_status.value,
            "reviewed_correlation": reviewed.model_dump(),
            "mandatory_disclaimer": MANDATORY_NON_CAUSAL_DISCLAIMER,
        }
    except KeyError as ke:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ke))
    except Exception as exc:
        logger.error(f"Review error on correlation {correlation_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
