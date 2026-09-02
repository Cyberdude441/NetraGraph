"""
Domain-Aware Adaptive Model Selection V2 — Configuration & Domain Profiles.
Defines security domains, representation schemas, scoring objectives, and safety thresholds.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

MODULE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = MODULE_DIR / "results"
PLOTS_DIR = MODULE_DIR / "plots"


class SecurityDomain(str, Enum):
    NETWORK_INTRUSION = "network_intrusion"
    DDOS_PROTECTION = "ddos_protection"
    URL_PHISHING = "url_phishing"
    MALWARE_ATTRIBUTION = "malware_attribution"
    UNKNOWN_DOMAIN = "unknown_domain"


class RepresentationType(str, Enum):
    NETWORK_FLOW_V1 = "NETWORK_FLOW_V1"
    MALWARE_METADATA_V1 = "MALWARE_METADATA_V1"
    MALWARE_STRUCTURAL_V2 = "MALWARE_STRUCTURAL_V2"
    FALLBACK_TABULAR_V1 = "FALLBACK_TABULAR_V1"


DOMAIN_PROFILES: Dict[str, Dict[str, Any]] = {
    SecurityDomain.NETWORK_INTRUSION: {
        "domain_name": "Network Intrusion Detection",
        "reference_datasets": ["CIC-IDS2017", "CSE-CIC-IDS2018"],
        "task_type": "binary_classification",
        "preferred_representation": RepresentationType.NETWORK_FLOW_V1,
        "candidate_models": ["XGBoost", "LightGBM", "Random Forest"],
        "fallback_model": "Random Forest",
        "known_drift": "Port scanning and lateral movement payload variation over time.",
        "known_leakage_risks": ["Flow ID / IP address memorization", "Timestamp-based attack clustering"],
        "operational_objective": "High F1 detection with ultra-low false alarms (FPR < 1%) and sub-millisecond inference.",
        "scoring_weights": {
            "performance_f1": 0.40,
            "latency": 0.30,
            "fpr_penalty": 0.30,
            "calibration": 0.00,
            "minority_recall": 0.00,
            "robustness": 0.00,
        },
    },
    SecurityDomain.DDOS_PROTECTION: {
        "domain_name": "Distributed Denial of Service (DDoS) Mitigation",
        "reference_datasets": ["CIC-DDoS2019"],
        "task_type": "binary_classification",
        "preferred_representation": RepresentationType.NETWORK_FLOW_V1,
        "candidate_models": ["CatBoost", "XGBoost", "Random Forest"],
        "fallback_model": "CatBoost",
        "known_drift": "Unseen UDP/TCP reflection protocols and asymmetric burst rates.",
        "known_leakage_risks": ["Source IP reflection artifacts", "Static packet length signatures"],
        "operational_objective": "Zero false positive suppression under protocol-disjoint reflection traffic with 100% volumetric recall.",
        "scoring_weights": {
            "performance_f1": 0.30,
            "latency": 0.10,
            "fpr_penalty": 0.40,
            "calibration": 0.00,
            "minority_recall": 0.00,
            "robustness": 0.20,
        },
    },
    SecurityDomain.URL_PHISHING: {
        "domain_name": "Phishing URL & Web Threat Detection",
        "reference_datasets": ["UNSW-NB15"],
        "task_type": "binary_classification",
        "preferred_representation": RepresentationType.NETWORK_FLOW_V1,
        "candidate_models": ["XGBoost", "LightGBM", "Random Forest"],
        "fallback_model": "XGBoost",
        "known_drift": "Domain generation algorithms (DGA) and brand token obfuscation.",
        "known_leakage_risks": ["Top-Level Domain (TLD) frequency overfitting", "URL length thresholds"],
        "operational_objective": "High precision URL classification resilient to URL shortening and obfuscation.",
        "scoring_weights": {
            "performance_f1": 0.40,
            "latency": 0.30,
            "fpr_penalty": 0.30,
            "calibration": 0.00,
            "minority_recall": 0.00,
            "robustness": 0.00,
        },
    },
    SecurityDomain.MALWARE_ATTRIBUTION: {
        "domain_name": "Malware Family Multi-Class Attribution",
        "reference_datasets": ["MalwareBazaar"],
        "task_type": "multiclass_classification",
        "preferred_representation": RepresentationType.MALWARE_STRUCTURAL_V2,
        "candidate_models": ["CatBoost", "XGBoost", "Random Forest", "Logistic Regression"],
        "fallback_model": "Random Forest",
        "known_drift": "Temporal submission campaigns, polymorphic hash shifts, and threat actor infrastructure rotation.",
        "known_leakage_risks": ["Reporter researcher bias", "ClamAV signature name leakage", "Submission date clustering"],
        "operational_objective": "Maximized Macro F1 and minority-family recall invariant to submission timestamps and reporter tags.",
        "scoring_weights": {
            "performance_f1": 0.35,
            "latency": 0.05,
            "fpr_penalty": 0.10,
            "calibration": 0.10,
            "minority_recall": 0.25,
            "robustness": 0.15,
        },
    },
}

# Safety thresholds
MIN_DOMAIN_CONFIDENCE_THRESHOLD = 0.60
MIN_MODEL_CONFIDENCE_THRESHOLD = 0.55
FALLBACK_DOMAIN = SecurityDomain.UNKNOWN_DOMAIN
FALLBACK_REPRESENTATION = RepresentationType.FALLBACK_TABULAR_V1
