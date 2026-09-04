"""FastAPI router for Graph & Model Drift Observatory (Phase 16).

Implements 10 approved decision-support and observability endpoints with
explicit RBAC clearance and mandatory non-causal forensic disclaimers.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
import jwt

try:
    from app.auth.config import auth_config
    from ml.drift_observatory import (
        GENERAL_DRIFT_DISCLAIMER,
        BaselineListResponse,
        BaselineRegistrationRequest,
        DriftComputeRequest,
        DriftDomain,
        DriftObservationRecord,
        DriftSeverity,
        GraphDriftResponse,
        IncompatibleBaselineError,
        ModelDriftResponse,
        ObservationListResponse,
        ObservatoryHealthResponse,
        ObservatoryOverview,
        ReferenceBaseline,
        drift_observatory_engine,
    )
except ImportError:
    from ..auth.config import auth_config
    from backend.ml.drift_observatory import (
        GENERAL_DRIFT_DISCLAIMER,
        BaselineListResponse,
        BaselineRegistrationRequest,
        DriftComputeRequest,
        DriftDomain,
        DriftObservationRecord,
        DriftSeverity,
        GraphDriftResponse,
        IncompatibleBaselineError,
        ModelDriftResponse,
        ObservationListResponse,
        ObservatoryHealthResponse,
        ObservatoryOverview,
        ReferenceBaseline,
        drift_observatory_engine,
    )

logger = logging.getLogger("DriftRouter")

router = APIRouter(
    prefix="/drift",
    tags=["Graph & Model Drift Observatory"],
)


# =============================================================================
# RBAC Clearance Dependency
# =============================================================================
def require_drift_clearance(allowed_roles: List[str]):
    """
    RBAC dependency verifying role clearance for Drift Observatory endpoints.
    Validates JWT token if present, with header fallback for test environments.
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
            user_roles = ["ANALYST"]
            user_id = "analyst-default"

        allowed_upper = [r.upper() for r in allowed_roles]
        if "ADMIN" in user_roles:
            return {"user_id": user_id, "roles": user_roles}

        if not any(r in allowed_upper for r in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of the following clearance roles: {', '.join(allowed_roles)}. Current: {user_roles}",
            )

        return {"user_id": user_id, "roles": user_roles}

    return _checker


# =============================================================================
# 1. Health Endpoint
# =============================================================================
@router.get(
    "/health",
    response_model=ObservatoryHealthResponse,
    summary="Observatory Health & Status",
    description="Returns uptime, active baselines count, total observations count, and monitored domains.",
)
async def get_drift_health(
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["ANALYST", "INVESTIGATOR", "ADMIN"])),
) -> ObservatoryHealthResponse:
    return drift_observatory_engine.get_health()


# =============================================================================
# 2. Baselines Listing
# =============================================================================
@router.get(
    "/baselines",
    response_model=BaselineListResponse,
    summary="List Registered Baselines",
    description="Retrieves registered and frozen reference baselines with optional domain filtering.",
)
async def list_baselines(
    domain: Optional[DriftDomain] = Query(None, description="Filter by domain"),
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["ANALYST", "INVESTIGATOR", "ADMIN"])),
) -> BaselineListResponse:
    baselines = drift_observatory_engine.list_baselines(domain)
    return BaselineListResponse(
        total=len(baselines),
        baselines=baselines,
        disclaimer=GENERAL_DRIFT_DISCLAIMER,
    )


# =============================================================================
# 3. Single Baseline Lookup
# =============================================================================
@router.get(
    "/baselines/{baseline_id}",
    response_model=ReferenceBaseline,
    summary="Get Baseline Details",
    description="Retrieves a specific reference baseline with feature distributions and data digests.",
)
async def get_baseline(
    baseline_id: str,
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["ANALYST", "INVESTIGATOR", "ADMIN"])),
) -> ReferenceBaseline:
    base = drift_observatory_engine.get_baseline(baseline_id)
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference baseline '{baseline_id}' not found.",
        )
    return base


# =============================================================================
# 4. Register Baseline (Restricted to INVESTIGATOR, ADMIN)
# =============================================================================
@router.post(
    "/baselines",
    response_model=ReferenceBaseline,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Reference Baseline",
    description="Freezes and registers a reference baseline. Restricted to INVESTIGATOR and ADMIN.",
)
async def register_baseline(
    request: BaselineRegistrationRequest,
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["INVESTIGATOR", "ADMIN"])),
) -> ReferenceBaseline:
    try:
        return drift_observatory_engine.register_baseline(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register baseline: {str(exc)}",
        )


# =============================================================================
# 5. On-Demand Drift Computation (Restricted to INVESTIGATOR, ADMIN)
# =============================================================================
@router.post(
    "/compute",
    response_model=DriftObservationRecord,
    summary="Compute Statistical Drift",
    description="Executes on-demand drift calculation. Restricted to INVESTIGATOR and ADMIN.",
)
async def compute_drift(
    request: DriftComputeRequest,
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["INVESTIGATOR", "ADMIN"])),
) -> DriftObservationRecord:
    try:
        return drift_observatory_engine.compute_drift(request)
    except IncompatibleBaselineError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Incompatible baseline: {str(exc)}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error in drift computation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drift computation failed: {str(exc)}",
        )


# =============================================================================
# 6. Observations History
# =============================================================================
@router.get(
    "/observations",
    response_model=ObservationListResponse,
    summary="Query Drift Observation History",
    description="Retrieves historical drift observations with domain, severity, and target filters.",
)
async def list_observations(
    domain: Optional[DriftDomain] = Query(None, description="Filter by domain"),
    severity: Optional[DriftSeverity] = Query(None, description="Filter by operational severity"),
    target: Optional[str] = Query(None, description="Filter by target name"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["ANALYST", "INVESTIGATOR", "ADMIN"])),
) -> ObservationListResponse:
    total, obs_list = drift_observatory_engine.list_observations(
        domain=domain,
        severity=severity,
        target=target,
        limit=limit,
        offset=offset,
    )
    return ObservationListResponse(
        total=total,
        observations=obs_list,
        disclaimer=GENERAL_DRIFT_DISCLAIMER,
    )


# =============================================================================
# 7. Single Observation Lookup
# =============================================================================
@router.get(
    "/observations/{observation_id}",
    response_model=DriftObservationRecord,
    summary="Get Drift Observation Detail",
    description="Retrieves an immutable drift observation record with full non-causal explanation.",
)
async def get_observation(
    observation_id: str,
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["ANALYST", "INVESTIGATOR", "ADMIN"])),
) -> DriftObservationRecord:
    obs = drift_observatory_engine.get_observation(observation_id)
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drift observation '{observation_id}' not found.",
        )
    return obs


# =============================================================================
# 8. Executive Overview / Summary
# =============================================================================
@router.get(
    "/summary",
    response_model=ObservatoryOverview,
    summary="Multi-Domain Observatory Overview",
    description="Global multi-domain overview of drift status, active alerts, and highest severities.",
)
async def get_drift_summary(
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["ANALYST", "INVESTIGATOR", "ADMIN"])),
) -> ObservatoryOverview:
    return drift_observatory_engine.get_summary()


# =============================================================================
# 9. Dedicated Graph Drift Endpoint
# =============================================================================
@router.get(
    "/graph",
    response_model=GraphDriftResponse,
    summary="Graph Structural Drift Assessment",
    description="Evaluates topological and distribution divergence on the active investigation network.",
)
async def get_graph_drift(
    target_graph: str = Query("InvestigationGraph", description="Graph target identifier"),
    start_time: Optional[str] = Query(None, description="Optional comparison start ISO"),
    end_time: Optional[str] = Query(None, description="Optional comparison end ISO"),
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["ANALYST", "INVESTIGATOR", "ADMIN"])),
) -> GraphDriftResponse:
    try:
        return drift_observatory_engine.get_graph_drift(
            target_graph=target_graph,
            comparison_window_start=start_time,
            comparison_window_end=end_time,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph drift evaluation failed: {str(exc)}",
        )


# =============================================================================
# 10. Dedicated Model Drift Endpoint
# =============================================================================
@router.get(
    "/models",
    response_model=ModelDriftResponse,
    summary="Model Prediction Drift Assessment",
    description="Evaluates output class and probability distribution divergence across Models A-E.",
)
async def get_model_drift(
    model_name: str = Query("intrusion", description="Model identifier (intrusion, phishing-email, etc.)"),
    start_time: Optional[str] = Query(None, description="Optional comparison start ISO"),
    end_time: Optional[str] = Query(None, description="Optional comparison end ISO"),
    _auth: Dict[str, Any] = Depends(require_drift_clearance(["ANALYST", "INVESTIGATOR", "ADMIN"])),
) -> ModelDriftResponse:
    try:
        return drift_observatory_engine.get_model_drift(
            model_name=model_name,
            comparison_window_start=start_time,
            comparison_window_end=end_time,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model drift evaluation failed: {str(exc)}",
        )
