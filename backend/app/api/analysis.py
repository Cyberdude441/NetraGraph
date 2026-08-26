from fastapi import APIRouter, status
from ..models.analysis import AnalysisRequest, AnalysisResponse
from ..services.analysis_service import analysis_service

router = APIRouter(prefix="/analyze", tags=["AI Investigation Assistant"])


@router.post(
    "",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run AI criminal network reasoning and path analysis",
    description="Analyzes complex investigative queries, identifies network bridge nodes, calculates shortest funding/comms paths, and summarizes risk drivers.",
)
async def run_ai_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    return analysis_service.perform_network_analysis(payload)
