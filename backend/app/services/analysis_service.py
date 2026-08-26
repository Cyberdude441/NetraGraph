from ..models.analysis import AnalysisRequest, AnalysisResponse
from ..ai.investigation_agent import investigation_agent


class AnalysisService:
    """Service to process AI investigation inquiries and graph reasoning."""

    def perform_network_analysis(self, req: AnalysisRequest) -> AnalysisResponse:
        return investigation_agent.analyze_investigation_query(req)


analysis_service = AnalysisService()
