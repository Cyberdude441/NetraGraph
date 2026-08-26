"""
NetraGraph AI - AI Endpoints Router
Exposes REST endpoints for NVIDIA Nemotron and Google Gemini intelligence analysis.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..ai.ai_router import get_ai_status, route_ai_request
from ..ai.config import config

router = APIRouter(prefix="/ai", tags=["AI Intelligence Engine"])


class AIAnalyzeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=3,
        description="Crime report, intercept text, or query to analyze",
        examples=["Suspect Vikram Malhotra called +919876543210 and wired funds to HDFC-ACC-44919."],
    )
    provider: Optional[str] = Field(
        default=None,
        description="AI provider: 'nemotron' | 'gemini' | 'auto'",
        examples=["nemotron"],
    )
    task: Optional[str] = Field(
        default="entity_extraction",
        description="Task: 'entity_extraction' | 'relationship_analysis' | 'risk_assessment' | 'investigation_summary' | 'analyze_document' | 'generate_report'",
        examples=["entity_extraction"],
    )


class AIReportRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=5,
        description="Case background or findings for report synthesis",
    )
    provider: Optional[str] = Field(
        default="gemini",
        description="Provider to use for report generation",
    )


class AIConfigUpdateRequest(BaseModel):
    default_provider: str = Field(
        ...,
        description="'nemotron' | 'gemini'",
    )


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_with_ai(request: AIAnalyzeRequest) -> Dict[str, Any]:
    """
    Analyzes criminal intelligence text using the specified AI provider (Nemotron or Gemini).
    """
    try:
        response = await route_ai_request(
            text=request.text,
            provider=request.provider,
            task=request.task or "entity_extraction",
        )
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(exc)}",
        )


@router.post("/report", status_code=status.HTTP_200_OK)
async def generate_ai_report(request: AIReportRequest) -> Dict[str, Any]:
    """
    Generates a structured investigation report using Google Gemini or Nemotron.
    """
    try:
        response = await route_ai_request(
            text=request.text,
            provider=request.provider or "gemini",
            task="generate_report",
        )
        return {
            "provider": response["provider"],
            "status": "success",
            "report": response["result"],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI report generation failed: {str(exc)}",
        )


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_provider_status() -> Dict[str, Any]:
    """
    Returns live connectivity status of NVIDIA Nemotron and Google Gemini without exposing API keys.
    """
    return get_ai_status()


@router.post("/config", status_code=status.HTTP_200_OK)
async def update_ai_config(request: AIConfigUpdateRequest) -> Dict[str, Any]:
    """
    Updates the active default AI provider.
    """
    updated = config.set_default_provider(request.default_provider)
    return {
        "status": "updated",
        "default_provider": updated,
    }
