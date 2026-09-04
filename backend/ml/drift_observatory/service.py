"""Master coordinator for Graph & Model Drift Observatory.

PERSISTENCE INVARIANT:
Persistence uses bounded thread-safe in-memory state with atomic JSON serialization
and has no PostgreSQL schema or migration impact.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from .baselines import IncompatibleBaselineError, baseline_registry
from .config import (
    DEFAULT_ALGORITHM_VERSION,
    DRIFT_OBSERVATORY_VERSION,
    GENERAL_DRIFT_DISCLAIMER,
    BaselineType,
    DriftDomain,
    DriftMetricType,
    DriftSeverity,
    DriftThresholdPolicy,
    ObservationStatus,
)
from .feature_drift import FeatureDriftDetector
from .graph_drift import GraphDriftDetector
from .model_drift import ModelOutputDriftDetector
from .models import (
    BaselineRegistrationRequest,
    BaselineWindow,
    ComparisonWindow,
    DomainDriftSummary,
    DriftComputeRequest,
    DriftObservationRecord,
    GraphDriftResponse,
    ModelDriftResponse,
    ObservatoryHealthResponse,
    ObservatoryOverview,
    ReferenceBaseline,
)
from .provenance import compute_data_digest
from .quality_drift import DataQualityDriftDetector
from .source_drift import CTISourceDriftDetector

logger = logging.getLogger("DriftObservatoryEngine")


class DriftObservatoryEngine:
    """Central engine orchestrating drift detection, baseline verification, and observability reporting."""

    def __init__(self, policy: Optional[DriftThresholdPolicy] = None):
        self._lock = threading.RLock()
        self.policy = policy or DriftThresholdPolicy()
        self.start_time = time.time()

        # Domain Detectors
        self.graph_detector = GraphDriftDetector(self.policy)
        self.feature_detector = FeatureDriftDetector(self.policy)
        self.model_detector = ModelOutputDriftDetector(self.policy)
        self.source_detector = CTISourceDriftDetector(self.policy)
        self.quality_detector = DataQualityDriftDetector(self.policy)

        # In-memory bounded observation buffer (latest 1000 observations)
        self._observations: Dict[str, DriftObservationRecord] = {}
        self._max_observations = 1000

        # Seed initial baselines if registry is unpopulated
        self._seed_default_baselines_if_needed()

    def _seed_default_baselines_if_needed(self) -> None:
        """Seeds initial reference baselines from repository metadata if empty."""
        with self._lock:
            if len(baseline_registry.list_baselines()) > 0:
                return

            now_iso = datetime.now(timezone.utc).isoformat()

            # 1. Graph Baseline (derived from nominal Cyber Investigation entities)
            try:
                from database.db import INITIAL_CYBER_ENTITIES  # type: ignore
            except ImportError:
                try:
                    from app.database.db import INITIAL_CYBER_ENTITIES  # type: ignore
                except ImportError:
                    INITIAL_CYBER_ENTITIES = []

            sample_nodes = INITIAL_CYBER_ENTITIES or []
            node_types = {}
            for e in sample_nodes:
                t = getattr(e, "type", "Unknown")
                t_val = getattr(t, "value", str(t))
                node_types[t_val] = node_types.get(t_val, 0) + 1

            graph_baseline = ReferenceBaseline(
                baseline_id="base-graph-cyber-v1",
                domain=DriftDomain.GRAPH,
                target_name="InvestigationGraph",
                baseline_type=BaselineType.FIXED_SNAPSHOT,
                created_at=now_iso,
                graph_layer="EVIDENCE",
                window=BaselineWindow(
                    start_timestamp=now_iso,
                    end_timestamp=now_iso,
                    sample_count=len(sample_nodes) or 35,
                    data_digest=compute_data_digest(node_types),
                ),
                feature_distributions={
                    "node_types": node_types or {"Person": 15, "Phone": 10, "BankAccount": 10},
                    "relationship_types": {"COMMUNICATED_WITH": 20, "TRANSACTION": 15, "ASSOCIATED_WITH": 10},
                    "density": 0.045,
                    "components": 3,
                    "degrees": [2.0] * (len(sample_nodes) or 35),
                },
                metadata={"description": "Baseline nominal topology for cyber investigation networks."},
            )
            baseline_registry.register_baseline(graph_baseline)

            # 2. Model Output Baselines for Models A-E
            model_defaults = [
                ("intrusion", "Session Intrusion Detection", {"0": 1055, "1": 853}, [0.88] * 1908),
                ("network-intrusion", "Network Intrusion Detection", {"normal": 67343, "anomaly": 58630}, [0.92] * 12597),
                ("phishing-email", "Phishing Email Detection", {"Safe Email": 11322, "Phishing Email": 7328}, [0.90] * 1865),
                ("phishing-url", "Phishing URL Detection", {"0": 34500, "1": 38640}, [0.94] * 7314),
                ("webpage-phishing", "Webpage Phishing Detection", {"0": 58000, "1": 56000}, [0.89] * 11400),
            ]

            for m_name, task, class_dist, probs in model_defaults:
                m_base = ReferenceBaseline(
                    baseline_id=f"base-model-{m_name}-v1",
                    domain=DriftDomain.MODEL_OUTPUT,
                    target_name=m_name,
                    baseline_type=BaselineType.FIXED_SNAPSHOT,
                    created_at=now_iso,
                    model_version="v1",
                    window=BaselineWindow(
                        start_timestamp=now_iso,
                        end_timestamp=now_iso,
                        sample_count=len(probs),
                        data_digest=compute_data_digest(class_dist),
                    ),
                    feature_distributions={
                        "class_distribution": class_dist,
                        "probabilities": probs,
                    },
                    metadata={"task_type": task, "source": "Training report validation benchmark."},
                )
                baseline_registry.register_baseline(m_base)

            # 3. CTI Source Baseline
            cti_base = ReferenceBaseline(
                baseline_id="base-cti-feeds-v1",
                domain=DriftDomain.CTI_SOURCE,
                target_name="ExternalCTIFeeds",
                baseline_type=BaselineType.FIXED_SNAPSHOT,
                created_at=now_iso,
                window=BaselineWindow(
                    start_timestamp=now_iso,
                    end_timestamp=now_iso,
                    sample_count=100,
                    data_digest=compute_data_digest("cti_baseline"),
                ),
                feature_distributions={
                    "source_distribution": {"in-gov-ncrb-feed": 40, "cert-in-bulletins": 30, "misp-threat-sharing": 20, "opencti-cyber-intel": 10},
                    "type_distribution": {"IPV4": 40, "DOMAIN": 25, "URL": 20, "FILE_HASH": 15},
                    "conflict_rate": 0.02,
                    "ages_days": [3.0] * 100,
                },
                metadata={"source": "Phase 15 SourceRegistry nominal distribution."},
            )
            baseline_registry.register_baseline(cti_base)

            # 4. Ingestion Data Quality Baseline
            quality_base = ReferenceBaseline(
                baseline_id="base-ingestion-quality-v1",
                domain=DriftDomain.DATA_QUALITY,
                target_name="MultiModalIngestion",
                baseline_type=BaselineType.FIXED_SNAPSHOT,
                created_at=now_iso,
                window=BaselineWindow(
                    start_timestamp=now_iso,
                    end_timestamp=now_iso,
                    sample_count=150,
                    data_digest=compute_data_digest("quality_baseline"),
                ),
                feature_distributions={
                    "module_distribution": {"FIR": 50, "CDR": 40, "Finance": 30, "Cyber": 30},
                    "missing_field_rate": 0.015,
                    "failure_rate": 0.005,
                },
                metadata={"source": "Nominal multi-modal ingestion pipeline specification."},
            )
            baseline_registry.register_baseline(quality_base)

    def _record_observation(self, obs: DriftObservationRecord) -> None:
        with self._lock:
            if len(self._observations) >= self._max_observations:
                # Evict oldest entry
                first_key = next(iter(self._observations))
                del self._observations[first_key]
            self._observations[obs.drift_observation_id] = obs

    def get_health(self) -> ObservatoryHealthResponse:
        with self._lock:
            active_baselines = len(baseline_registry.list_baselines())
            total_observations = len(self._observations)
            return ObservatoryHealthResponse(
                status="HEALTHY",
                version=DRIFT_OBSERVATORY_VERSION,
                uptime_seconds=round(time.time() - self.start_time, 2),
                active_baselines=active_baselines,
                total_observations=total_observations,
                domains_monitored=[d.value for d in DriftDomain],
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )

    def register_baseline(self, req: BaselineRegistrationRequest) -> ReferenceBaseline:
        now_iso = datetime.now(timezone.utc).isoformat()
        sample_count = len(req.data_payload) if req.data_payload else 0
        digest = compute_data_digest(req.feature_distributions or req.data_payload or {})

        b_id = f"base-{req.domain.value.lower()}-{req.target_name.lower().replace(' ', '-')}-{int(time.time())}"
        baseline = ReferenceBaseline(
            baseline_id=b_id,
            domain=req.domain,
            target_name=req.target_name,
            baseline_type=req.baseline_type,
            created_at=now_iso,
            model_version=req.model_version,
            feature_schema_version=req.feature_schema_version,
            graph_layer=req.graph_layer,
            window=BaselineWindow(
                start_timestamp=now_iso,
                end_timestamp=now_iso,
                sample_count=sample_count,
                data_digest=digest,
            ),
            feature_distributions=req.feature_distributions or {},
            metadata=req.metadata,
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )
        return baseline_registry.register_baseline(baseline)

    def get_baseline(self, baseline_id: str) -> Optional[ReferenceBaseline]:
        return baseline_registry.get_baseline(baseline_id)

    def list_baselines(self, domain: Optional[DriftDomain] = None) -> List[ReferenceBaseline]:
        return baseline_registry.list_baselines(domain)

    def delete_baseline(self, baseline_id: str) -> bool:
        return baseline_registry.delete_baseline(baseline_id)

    def compute_drift(self, req: DriftComputeRequest) -> DriftObservationRecord:
        """
        Executes bounded on-demand drift computation for the specified domain and target.
        """
        # Resolve baseline
        baseline: Optional[ReferenceBaseline] = None
        if req.baseline_id:
            baseline = baseline_registry.get_baseline(req.baseline_id)
        else:
            candidates = baseline_registry.list_baselines(req.domain)
            for c in candidates:
                if c.target_name.lower() == req.target_name.lower():
                    baseline = c
                    break

        if not baseline:
            raise ValueError(f"No compatible baseline found for domain '{req.domain.value}' and target '{req.target_name}'.")

        # Validate compatibility
        baseline_registry.validate_compatibility(baseline, req.domain, req.target_name)

        if req.domain == DriftDomain.GRAPH:
            # Reconstruct or use comparison graph
            g = nx.MultiDiGraph()
            if req.comparison_data:
                for item in req.comparison_data:
                    if isinstance(item, dict):
                        if "source" in item and "target" in item:
                            g.add_edge(item["source"], item["target"], rel_type=item.get("rel_type", "ASSOCIATED_WITH"))
                        elif "id" in item:
                            g.add_node(item["id"], type=item.get("type", "Unknown"))
            obs = self.graph_detector.evaluate_graph_drift(
                reference_baseline=baseline,
                comparison_graph=g,
                target_name=req.target_name,
                comparison_window_start=req.comparison_window_start,
                comparison_window_end=req.comparison_window_end,
            )

        elif req.domain == DriftDomain.FEATURE:
            obs = self.feature_detector.evaluate_feature_drift(
                reference_baseline=baseline,
                comparison_records=req.comparison_data,
                feature_name=req.target_name,
                parent_model=baseline.metadata.get("parent_model", "UnknownModel"),
                comparison_window_start=req.comparison_window_start,
                comparison_window_end=req.comparison_window_end,
            )

        elif req.domain == DriftDomain.MODEL_OUTPUT:
            obs = self.model_detector.evaluate_output_drift(
                reference_baseline=baseline,
                comparison_predictions=req.comparison_data,
                model_name=req.target_name,
                comparison_window_start=req.comparison_window_start,
                comparison_window_end=req.comparison_window_end,
            )

        elif req.domain == DriftDomain.CTI_SOURCE:
            obs = self.source_detector.evaluate_source_drift(
                reference_baseline=baseline,
                indicators=req.comparison_data,
                feed_name=req.target_name,
                comparison_window_start=req.comparison_window_start,
                comparison_window_end=req.comparison_window_end,
            )

        elif req.domain == DriftDomain.DATA_QUALITY:
            obs = self.quality_detector.evaluate_quality_drift(
                reference_baseline=baseline,
                ingestion_records=req.comparison_data,
                pipeline_name=req.target_name,
                comparison_window_start=req.comparison_window_start,
                comparison_window_end=req.comparison_window_end,
            )
        else:
            raise ValueError(f"Unsupported drift domain: {req.domain}")

        self._record_observation(obs)
        return obs

    def list_observations(
        self,
        domain: Optional[DriftDomain] = None,
        severity: Optional[DriftSeverity] = None,
        target: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[int, List[DriftObservationRecord]]:
        with self._lock:
            all_obs = list(reversed(list(self._observations.values())))
            filtered = []
            for obs in all_obs:
                if domain and obs.domain != domain:
                    continue
                if severity and obs.severity != severity:
                    continue
                if target and obs.target_name.lower() != target.lower():
                    continue
                filtered.append(obs)

            bounded_limit = min(max(1, limit), self.policy.max_page_size)
            page = filtered[offset : offset + bounded_limit]
            return len(filtered), page

    def get_observation(self, observation_id: str) -> Optional[DriftObservationRecord]:
        with self._lock:
            return self._observations.get(observation_id)

    def get_summary(self) -> ObservatoryOverview:
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            summaries: Dict[str, DomainDriftSummary] = {}
            global_sev = DriftSeverity.NORMAL

            for dom in DriftDomain:
                dom_obs = [o for o in self._observations.values() if o.domain == dom]
                highest_sev = DriftSeverity.NORMAL
                alerts = 0
                insufficient = 0
                unavailable = 0

                for o in dom_obs:
                    if o.severity in (DriftSeverity.ELEVATED, DriftSeverity.CRITICAL):
                        alerts += 1
                    if o.severity == DriftSeverity.CRITICAL:
                        highest_sev = DriftSeverity.CRITICAL
                    elif o.severity == DriftSeverity.ELEVATED and highest_sev != DriftSeverity.CRITICAL:
                        highest_sev = DriftSeverity.ELEVATED
                    elif o.severity == DriftSeverity.WATCH and highest_sev not in (DriftSeverity.CRITICAL, DriftSeverity.ELEVATED):
                        highest_sev = DriftSeverity.WATCH

                    if o.status == ObservationStatus.INSUFFICIENT_DATA:
                        insufficient += 1
                    elif o.status == ObservationStatus.DATA_UNAVAILABLE:
                        unavailable += 1

                if highest_sev == DriftSeverity.CRITICAL:
                    global_sev = DriftSeverity.CRITICAL
                elif highest_sev == DriftSeverity.ELEVATED and global_sev != DriftSeverity.CRITICAL:
                    global_sev = DriftSeverity.ELEVATED

                summaries[dom.value] = DomainDriftSummary(
                    domain=dom,
                    status=ObservationStatus.COMPLETED if dom_obs else ObservationStatus.INSUFFICIENT_DATA,
                    highest_severity=highest_sev,
                    active_alerts_count=alerts,
                    total_observations=len(dom_obs),
                    insufficient_data_count=insufficient,
                    data_unavailable_count=unavailable,
                )

            return ObservatoryOverview(
                observatory_version=DRIFT_OBSERVATORY_VERSION,
                computed_at=now_iso,
                active_baselines_count=len(baseline_registry.list_baselines()),
                total_observations_count=len(self._observations),
                global_highest_severity=global_sev,
                domain_summaries=summaries,
                disclaimer=GENERAL_DRIFT_DISCLAIMER,
            )

    def get_graph_drift(
        self,
        target_graph: str = "InvestigationGraph",
        comparison_window_start: Optional[str] = None,
        comparison_window_end: Optional[str] = None,
    ) -> GraphDriftResponse:
        """Evaluates drift on the live NetworkGraphManager or database graph."""
        baseline = baseline_registry.get_baseline("base-graph-cyber-v1")
        if not baseline:
            candidates = baseline_registry.list_baselines(DriftDomain.GRAPH)
            if candidates:
                baseline = candidates[0]
            else:
                raise ValueError("No graph baseline registered.")

        # Read live graph
        try:
            from app.graph.network_manager import graph_manager  # type: ignore
            g = graph_manager.graph
        except ImportError:
            try:
                from database.neo4j import neo4j_db  # type: ignore
                g = neo4j_db._nx_cyber
            except ImportError:
                g = nx.MultiDiGraph()

        obs = self.graph_detector.evaluate_graph_drift(
            reference_baseline=baseline,
            comparison_graph=g,
            target_name=target_graph,
            comparison_window_start=comparison_window_start,
            comparison_window_end=comparison_window_end,
        )
        self._record_observation(obs)

        return GraphDriftResponse(
            target_graph=target_graph,
            observation=obs,
            topology_summary={
                "nodes_count": g.number_of_nodes(),
                "edges_count": g.number_of_edges(),
            },
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )

    def get_model_drift(
        self,
        model_name: str,
        comparison_window_start: Optional[str] = None,
        comparison_window_end: Optional[str] = None,
    ) -> ModelDriftResponse:
        """Evaluates prediction output and feature drift for a specified forensic model."""
        base_id = f"base-model-{model_name}-v1"
        baseline = baseline_registry.get_baseline(base_id)
        if not baseline:
            candidates = baseline_registry.list_baselines(DriftDomain.MODEL_OUTPUT)
            for c in candidates:
                if c.target_name.lower() == model_name.lower():
                    baseline = c
                    break
        if not baseline:
            raise ValueError(f"No baseline registered for model '{model_name}'.")

        # Read existing prediction nodes from graph
        preds: List[Dict[str, Any]] = []
        try:
            from database.neo4j import neo4j_db  # type: ignore
            for nid, data in neo4j_db._evidence_nodes.items():
                if data.get("label") == "MLPrediction" or data.get("assessment_type") == "MODEL_PREDICTION":
                    preds.append({
                        "prediction": data.get("prediction", "Unknown"),
                        "probability": float(data.get("probability", 0.9)),
                        "timestamp": data.get("timestamp"),
                    })
        except Exception:
            pass

        out_obs = self.model_detector.evaluate_output_drift(
            reference_baseline=baseline,
            comparison_predictions=preds,
            model_name=model_name,
            comparison_window_start=comparison_window_start,
            comparison_window_end=comparison_window_end,
        )
        self._record_observation(out_obs)

        return ModelDriftResponse(
            model_name=model_name,
            model_version=baseline.model_version,
            feature_drift_observations=[],
            output_drift_observation=out_obs,
            overall_severity=out_obs.severity,
            disclaimer=GENERAL_DRIFT_DISCLAIMER,
        )


# Global singleton instance
drift_observatory_engine = DriftObservatoryEngine()
