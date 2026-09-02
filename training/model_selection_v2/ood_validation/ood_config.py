"""
OOD / Red-Team Validation Configuration for NetraGraph Model Selection V2.
Defines isolated experimental protocols, perturbation bounds, and statistical validation seeds.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

MODULE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = MODULE_DIR / "results"
PLOTS_DIR = MODULE_DIR / "plots"

OOD_SEEDS = [42, 101, 2024, 777, 9999]

# Dataset Protocol & Attack Types
SEEN_DDOS_PROTOCOLS = ["DNS_Amplification", "NTP_Amplification", "MSSQL_Reflection"]
UNSEEN_DDOS_PROTOCOLS = ["UDP_Lag", "SYN_Flood", "LDAP_Reflection"]

KNOWN_MALWARE_FAMILIES = [
    "AgentTesla", "RedLine", "Formbook", "LokiBot", "Remcos", "SnakeKeylogger", "AsyncRAT", "GuLoader"
]
UNSEEN_MALWARE_FAMILIES = [
    "IcedID", "Emotet"
]

# Perturbation Bounds
PERTURBATION_NOISE_STD = 0.05
CATEGORICAL_CORRUPTION_RATE = 0.15
MISSING_VALUE_RATE = 0.20
