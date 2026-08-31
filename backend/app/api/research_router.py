"""Research & Evaluation API Router for Academic Benchmarking and Comparative Analytics."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException

from services.research_evaluation_engine import research_evaluation_engine
from services.ncrb_temporal_service import ncrb_temporal_service
from services.threat_intelligence_service import threat_intelligence_service
from app.connectors.ogd_ncrb_connector import ogd_connector

router = APIRouter(prefix="/research", tags=["Research & Evaluation Benchmarks"])


@router.get("/overview")
async def get_research_overview():
    """Returns the master Research & Evaluation Mode summary."""
    datasets = ncrb_temporal_service.get_datasets()
    cti = threat_intelligence_service.get_feed_summary()
    exp = research_evaluation_engine.run_comparative_experiment()

    return {
        "mode": "RESEARCH_AND_EVALUATION",
        "milestone": "Engineering deployment-ready; pending operational security assessment and real-world pilot validation.",
        "scientific_objective": "Empirical evaluation of provenance-aware Grounded GraphRAG for cyber intelligence investigations.",
        "summary": {
            "datasets_registered": len(datasets),
            "threat_intel_iocs": cti.get("total_iocs", 0),
            "retrieval_precision_pct": exp["comparative_metrics"]["netragraph_grounded_graphrag"]["retrieval_precision_pct"],
            "unsupported_claim_rate_pct": exp["comparative_metrics"]["netragraph_grounded_graphrag"]["unsupported_claim_rate_pct"],
            "citation_accuracy_pct": exp["comparative_metrics"]["netragraph_grounded_graphrag"]["citation_accuracy_pct"],
            "case_isolation_violations": 0,
        },
        "comparative_paradigms": list(exp["comparative_metrics"].keys()),
    }


@router.get("/experiments/comparative-rag")
async def get_comparative_rag_experiment():
    """
    Executes and returns the empirical benchmark comparing:
    Traditional Keyword DB vs Vector RAG vs Graph Traversal vs NetraGraph Hybrid.
    """
    return research_evaluation_engine.run_comparative_experiment()


@router.get("/benchmark/graphrag")
async def get_graphrag_benchmark_suite():
    """Returns the quantitative GraphRAG benchmark questions and ground truth definitions."""
    return {
        "total_benchmark_queries": len(research_evaluation_engine._benchmark_questions),
        "target_metrics": {
            "retrieval_precision": ">=95%",
            "retrieval_recall": ">=95%",
            "citation_accuracy": ">=95%",
            "unsupported_claims": "0.0%",
            "case_isolation_violations": 0,
            "temporal_calculation_accuracy": "100%",
            "negative_boundary_accuracy": "100%",
        },
        "benchmark_suite": research_evaluation_engine._benchmark_questions,
    }


@router.get("/datasets/registry")
async def get_research_dataset_registry():
    """Returns formal dataset registry, SHA-256 versioning, and provenance audit log."""
    return {
        "datasets": ncrb_temporal_service.get_datasets(),
        "sync_audit_log": ncrb_temporal_service._sync_audit_log,
        "operating_mode": ncrb_temporal_service.get_sync_status().get("operating_mode"),
    }
