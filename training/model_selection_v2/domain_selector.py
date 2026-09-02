"""
Domain-Aware Multi-Criteria Model Selector for NetraGraph Model Selection V2.
Evaluates candidate architectures using domain-calibrated multi-objective criteria.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from training.model_selection_v2.config import DOMAIN_PROFILES, SecurityDomain
except ImportError:
    from config import DOMAIN_PROFILES, SecurityDomain


@dataclass
class ModelScoreBreakdown:
    model_name: str
    performance_score: float
    robustness_score: float
    latency_score: float
    calibration_score: float
    minority_recall_score: float
    fpr_score: float
    overall_score: float


@dataclass
class DomainSelectionDecision:
    domain: SecurityDomain
    selected_model: str
    fallback_model: str
    score_breakdown: List[ModelScoreBreakdown]
    selection_confidence: float
    rationale: str


class DomainSelector:
    """
    Selects optimal ML model architecture using domain-specific multi-criteria utility functions.
    """

    # Benchmark evidence database populated from validated NetraGraph research phases
    HISTORICAL_BENCHMARKS: Dict[str, Dict[str, Dict[str, float]]] = {
        SecurityDomain.NETWORK_INTRUSION: {
            "XGBoost": {"f1": 1.000, "fpr": 0.000, "latency_us": 1.8, "ece": 0.015, "robustness": 0.98, "minority_rec": 1.00},
            "LightGBM": {"f1": 1.000, "fpr": 0.000, "latency_us": 1.5, "ece": 0.020, "robustness": 0.98, "minority_rec": 1.00},
            "Random Forest": {"f1": 0.998, "fpr": 0.002, "latency_us": 6.2, "ece": 0.080, "robustness": 0.95, "minority_rec": 0.98},
        },
        SecurityDomain.DDOS_PROTECTION: {
            "CatBoost": {"f1": 1.000, "fpr": 0.000, "latency_us": 1.2, "ece": 0.010, "robustness": 1.00, "minority_rec": 1.00},
            "XGBoost": {"f1": 0.998, "fpr": 0.001, "latency_us": 1.8, "ece": 0.018, "robustness": 0.92, "minority_rec": 0.99},
            "Random Forest": {"f1": 0.995, "fpr": 0.003, "latency_us": 5.8, "ece": 0.075, "robustness": 0.90, "minority_rec": 0.97},
        },
        SecurityDomain.URL_PHISHING: {
            "XGBoost": {"f1": 1.000, "fpr": 0.000, "latency_us": 1.6, "ece": 0.012, "robustness": 0.98, "minority_rec": 1.00},
            "LightGBM": {"f1": 1.000, "fpr": 0.000, "latency_us": 1.4, "ece": 0.018, "robustness": 0.97, "minority_rec": 1.00},
            "Random Forest": {"f1": 0.996, "fpr": 0.002, "latency_us": 5.5, "ece": 0.065, "robustness": 0.94, "minority_rec": 0.98},
        },
        SecurityDomain.MALWARE_ATTRIBUTION: {
            "CatBoost": {"f1": 0.988, "fpr": 0.005, "latency_us": 15.7, "ece": 0.041, "robustness": 0.92, "minority_rec": 0.95},
            "XGBoost": {"f1": 0.986, "fpr": 0.006, "latency_us": 13.2, "ece": 0.052, "robustness": 0.90, "minority_rec": 0.93},
            "Random Forest": {"f1": 0.982, "fpr": 0.008, "latency_us": 37.5, "ece": 0.120, "robustness": 0.88, "minority_rec": 0.88},
            "Logistic Regression": {"f1": 0.965, "fpr": 0.015, "latency_us": 5.0, "ece": 0.049, "robustness": 0.85, "minority_rec": 0.82},
        },
    }

    def select_model_for_domain(self, domain: SecurityDomain) -> DomainSelectionDecision:
        """
        Score all candidate models for the given security domain and select the optimal architecture.
        """
        profile = DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES[SecurityDomain.NETWORK_INTRUSION])
        candidates = profile["candidate_models"]
        weights = profile["scoring_weights"]
        bench_data = self.HISTORICAL_BENCHMARKS.get(domain, self.HISTORICAL_BENCHMARKS[SecurityDomain.NETWORK_INTRUSION])

        breakdowns: List[ModelScoreBreakdown] = []

        for cand in candidates:
            metrics = bench_data.get(cand, {"f1": 0.5, "fpr": 0.1, "latency_us": 50.0, "ece": 0.2, "robustness": 0.5, "minority_rec": 0.5})

            perf_score = metrics["f1"]
            fpr_score = 1.0 - metrics["fpr"]
            lat_score = 1.0 / (1.0 + (metrics["latency_us"] / 10.0))
            calib_score = 1.0 - min(1.0, metrics["ece"] * 5.0)
            robust_score = metrics["robustness"]
            min_rec_score = metrics["minority_rec"]

            overall = (
                (weights["performance_f1"] * perf_score)
                + (weights["fpr_penalty"] * fpr_score)
                + (weights["latency"] * lat_score)
                + (weights["calibration"] * calib_score)
                + (weights["robustness"] * robust_score)
                + (weights["minority_recall"] * min_rec_score)
            )

            breakdowns.append(
                ModelScoreBreakdown(
                    model_name=cand,
                    performance_score=round(perf_score, 4),
                    robustness_score=round(robust_score, 4),
                    latency_score=round(lat_score, 4),
                    calibration_score=round(calib_score, 4),
                    minority_recall_score=round(min_rec_score, 4),
                    fpr_score=round(fpr_score, 4),
                    overall_score=round(overall, 4),
                )
            )

        # Sort by overall score
        breakdowns = sorted(breakdowns, key=lambda x: x.overall_score, reverse=True)
        best_model = breakdowns[0].model_name
        fallback_model = profile.get("fallback_model", "Random Forest")

        top_score = breakdowns[0].overall_score
        second_score = breakdowns[1].overall_score if len(breakdowns) > 1 else top_score * 0.9
        conf = float(np.clip(1.0 - (second_score / max(1e-6, top_score)), 0.05, 0.95))

        rationale = f"Selected {best_model} for {profile['domain_name']} with composite score {top_score:.4f} prioritizing {profile['operational_objective']}"

        return DomainSelectionDecision(
            domain=domain,
            selected_model=best_model,
            fallback_model=fallback_model,
            score_breakdown=breakdowns,
            selection_confidence=round(conf, 4),
            rationale=rationale,
        )
