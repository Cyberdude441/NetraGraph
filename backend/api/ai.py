from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import os

try:
    from services.graph_ai import graph_reasoning_engine
except ImportError:
    from ..services.graph_ai import graph_reasoning_engine

router = APIRouter(prefix="/ai", tags=["AI Copilot & Graph Reasoning"])


class GraphAIQueryRequest(BaseModel):
    question: str = Field(..., description="Investigator query or question")
    provider: Optional[str] = Field("gemini", description="AI Provider: 'gemini' or 'nemotron'")


@router.post("/graph-query")
async def execute_graph_ai_query(req: GraphAIQueryRequest):
    """
    Executes a Graph-Augmented Generation (Graph RAG) query:
    Question -> Neo4j Graph Query -> NCRB Analytics Aggregation -> LLM Explanation.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = graph_reasoning_engine.execute_graph_rag_pipeline(
            question=req.question.strip(),
            provider=req.provider or "gemini",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph RAG execution failed: {str(e)}")


@router.get("/providers")
async def get_ai_providers_status():
    """
    Check availability of Google Gemini and NVIDIA Nemotron AI providers.
    """
    has_gemini = bool(os.getenv("GOOGLE_GEMINI_API_KEY", ""))
    has_nemotron = bool(os.getenv("NVIDIA_NEMOTRON_API_KEY", ""))

    return {
        "providers": [
            {
                "id": "gemini",
                "name": "Google Gemini 1.5 Pro",
                "status": "AVAILABLE" if has_gemini else "HEURISTIC_MODE",
                "capabilities": ["Graph RAG", "Dossier Synthesis", "Legal Section Mapping"],
            },
            {
                "id": "nemotron",
                "name": "NVIDIA Nemotron-4 340B Instruct",
                "status": "AVAILABLE" if has_nemotron else "HEURISTIC_MODE",
                "capabilities": ["Criminal Network Link Analysis", "Multi-Hop Inference", "Risk Scoring"],
            },
        ],
        "default_provider": "gemini",
        "pipeline": "Neo4j Knowledge Graph Grounding (Zero Hallucination)",
    }
