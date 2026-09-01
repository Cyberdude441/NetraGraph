"""
Shadow-Mode Adaptive ML Inference Gateway for NetraGraph.

Orchestrates parallel execution of the Production Path (Models A–E) and
the Adaptive Path (Model Selector). Guarantees that production output is never
overwritten or compromised.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from training.shadow_inference.adaptive_adapter import AdaptiveAdapter
    from training.shadow_inference.comparator import calculate_aggregate_comparison, compare_results
    from training.shadow_inference.config import DATASET_TO_PROD_MODEL, PRODUCTION_MODELS
    from training.shadow_inference.drift_monitor import DriftMonitor
    from training.shadow_inference.explanation import generate_shadow_explanation
    from training.shadow_inference.metrics import compute_latency_percentiles
    from training.shadow_inference.production_adapter import ProductionAdapter
    from training.shadow_inference.schemas import ComparisonResult, ShadowResult
except ImportError:
    from adaptive_adapter import AdaptiveAdapter
    from comparator import calculate_aggregate_comparison, compare_results
    from config import DATASET_TO_PROD_MODEL, PRODUCTION_MODELS
    from drift_monitor import DriftMonitor
    from explanation import generate_shadow_explanation
    from metrics import compute_latency_percentiles
    from production_adapter import ProductionAdapter
    from schemas import ComparisonResult, ShadowResult


class ShadowGateway:
    """
    Shadow-Mode Gateway executing production and adaptive inference in parallel.
    
    CRITICAL ISOLATION GUARANTEES:
    - Never modifies production model files, parameters, or configurations.
    - Never overrides or intercepts live production API traffic.
    - Production results are captured and preserved verbatim.
    """

    def __init__(
        self,
        production_adapter: Optional[ProductionAdapter] = None,
        adaptive_adapter: Optional[AdaptiveAdapter] = None,
        drift_monitor: Optional[DriftMonitor] = None,
    ):
        self.production_adapter = production_adapter or ProductionAdapter()
        self.adaptive_adapter = adaptive_adapter or AdaptiveAdapter()
        self.drift_monitor = drift_monitor or DriftMonitor()
        self._history_results: List[ShadowResult] = []

    def predict(
        self,
        request: Dict[str, Any],
    ) -> ShadowResult:
        """
        Execute parallel shadow inference on a single request.
        """
        req_id = request.get("request_id") or f"SHADOW-{uuid.uuid4().hex[:8].upper()}"
        ts = request.get("timestamp") or datetime.now(timezone.utc).isoformat()
        dataset_name = request.get("dataset_name", "cicids2018")
        payload = request.get("payload", {})
        metadata = request.get("metadata", {})

        prod_model_name = request.get("production_model")
        if not prod_model_name:
            prod_model_name = DATASET_TO_PROD_MODEL.get(dataset_name, "intrusion")

        # ── 1. Production Path (A–E) ─────────────────────────────────────────
        prod_res = self.production_adapter.predict(
            model_name=prod_model_name,
            payload=payload,
        )

        # ── 2. Adaptive Path (Model Selector) ────────────────────────────────
        adapt_res = self.adaptive_adapter.predict(
            dataset_name=dataset_name,
            payload=payload,
        )

        # ── 3. Comparator ────────────────────────────────────────────────────
        comp_res = compare_results(prod_res, adapt_res)

        # ── 4. Telemetry Recording ───────────────────────────────────────────
        self.drift_monitor.record_telemetry(
            selected_model=adapt_res.model,
            confidence=adapt_res.selection_confidence,
            prediction=str(adapt_res.prediction),
        )

        shadow_result = ShadowResult(
            request_id=req_id,
            timestamp=ts,
            dataset_name=dataset_name,
            production=prod_res,
            adaptive=adapt_res,
            comparison=comp_res,
            metadata=metadata,
        )

        self._history_results.append(shadow_result)
        return shadow_result

    def compare_batch(
        self,
        requests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Execute shadow prediction across a batch of requests and aggregate statistics.
        """
        results: List[ShadowResult] = []
        for req in requests:
            res = self.predict(req)
            results.append(res)

        comparisons = [r.comparison for r in results]
        aggregate_comp = calculate_aggregate_comparison(comparisons)

        prod_latencies = [r.production.latency_ms for r in results]
        adapt_sel_latencies = [r.adaptive.selection_latency_ms for r in results]
        adapt_inf_latencies = [r.adaptive.inference_latency_ms for r in results]
        adapt_tot_latencies = [r.adaptive.total_latency_ms for r in results]

        latency_summary = {
            "production": compute_latency_percentiles(prod_latencies),
            "adaptive_selection_overhead": compute_latency_percentiles(adapt_sel_latencies),
            "adaptive_inference": compute_latency_percentiles(adapt_inf_latencies),
            "adaptive_total": compute_latency_percentiles(adapt_tot_latencies),
        }

        selection_distribution = self.drift_monitor.get_model_selection_distribution()
        drift_report = self.drift_monitor.generate_drift_report()

        return {
            "batch_size": len(results),
            "aggregate_comparison": aggregate_comp,
            "latency_summary": latency_summary,
            "model_selection_distribution": selection_distribution,
            "drift_report": drift_report.to_dict(),
            "results": [r.to_dict() for r in results],
        }


# ── Standalone Research Interface ────────────────────────────────────────────

_GLOBAL_GATEWAY = ShadowGateway()


def shadow_predict(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standalone Research API: Execute single shadow-mode prediction.
    """
    res = _GLOBAL_GATEWAY.predict(request)
    return res.to_dict()


def compare_production_vs_adaptive(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standalone Research API: Execute batch shadow comparison and generate aggregate report.
    """
    return _GLOBAL_GATEWAY.compare_batch(requests)
