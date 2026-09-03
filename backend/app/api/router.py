from fastapi import APIRouter
from .ingestion_router import router as ingestion_router
from .ncrb_router import router as ncrb_router
from .cases_router import router as cases_router
from .evidence_router import router as evidence_router
from .audit_router import router as audit_router
from .analytics_router import router as analytics_router
from .entities import router as entities_router
from .relationships_router import router as relationships_router
from .network import router as network_router
from .profile import router as profile_router
from .analysis import router as analysis_router
from .ai_endpoints import router as ai_endpoints_router
from .ml_router import router as ml_router
from .research_router import router as research_router
from .gnn_router import router as gnn_router
from .threat_fusion_router import router as threat_fusion_router

api_router = APIRouter(prefix="/api")

api_router.include_router(ingestion_router)
api_router.include_router(ncrb_router)
api_router.include_router(cases_router)
api_router.include_router(evidence_router)
api_router.include_router(audit_router)
api_router.include_router(analytics_router)
api_router.include_router(entities_router)
api_router.include_router(relationships_router)
api_router.include_router(network_router)
api_router.include_router(profile_router)
api_router.include_router(analysis_router)
api_router.include_router(ai_endpoints_router)
api_router.include_router(ml_router)
api_router.include_router(research_router)
api_router.include_router(gnn_router)
api_router.include_router(threat_fusion_router)
