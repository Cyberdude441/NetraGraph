"""
NetraGraph AI - Unified AI Router
Directs intelligence tasks to NVIDIA Nemotron or Google Gemini based on task characteristics or explicit user selection.
"""

import logging
from typing import Any, Dict, Optional

from .config import config
from .providers.gemini import analyze_with_gemini
from .providers.nemotron import analyze_with_nemotron

logger = logging.getLogger("netragraph.ai.router")

GEMINI_TASKS = {
    "analyze_document",
    "summarize_report",
    "generate_report",
    "document_intelligence",
}

NEMOTRON_TASKS = {
    "entity_extraction",
    "relationship_analysis",
    "risk_assessment",
    "investigation_summary",
    "graph_reasoning",
}


async def route_ai_request(
    text: str,
    provider: Optional[str] = None,
    task: str = "entity_extraction",
) -> Dict[str, Any]:
    """
    Unified AI task routing entry point.

    :param text: Input crime report, intercept transcript, or query.
    :param provider: "nemotron" | "gemini" | "auto" (default uses configured default)
    :param task: Requested analytical task
    :return: Standardized JSON dictionary with analysis results
    """
    selected_provider = (provider or config.DEFAULT_PROVIDER).lower().strip()

    # If auto, choose the best-suited provider
    if selected_provider == "auto":
        if task in GEMINI_TASKS:
            selected_provider = "gemini"
        else:
            selected_provider = "nemotron"

    logger.info("Routing AI task '%s' to provider '%s'", task, selected_provider)

    if selected_provider == "gemini":
        result = await analyze_with_gemini(input_data=text, task_type=task)
        return {
            "provider": "gemini",
            "task": task,
            "status": "success",
            "result": result,
        }
    else:
        # Default to Nemotron
        result = await analyze_with_nemotron(text=text, task_type=task)
        return {
            "provider": "nemotron",
            "task": task,
            "status": "success",
            "result": result,
        }


async def generate_intelligence_report(
    case_data: str, provider: Optional[str] = "gemini"
) -> Dict[str, Any]:
    """Generates an official intelligence report using Gemini or Nemotron."""
    return await route_ai_request(
        text=case_data, provider=provider or "gemini", task="generate_report"
    )


def get_ai_status() -> Dict[str, Any]:
    """Returns connectivity and configuration status for all providers."""
    return config.get_provider_status()
