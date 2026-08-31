"""Configuration, Schemas, and Hyperparameters for CSE-CIC-IDS2018 Pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Default Paths
DEFAULT_DATA_DIR = Path("/kaggle/input/ids-intrusion-csv")
COLAB_DATA_DIR = Path("/content/cicids2018")
DEFAULT_OUTPUT_DIR = Path("artifacts/network-anomaly-cicids2018/v1")
LOCAL_ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts" / "network-anomaly-cicids2018" / "v1"

# Primary Target Specifications
PRIMARY_TARGET = "Label"

# Binary Label Normalization Contract
BINARY_LABEL_MAPPING = {
    "0": "Benign",
    "1": "Attack",
}

# Multi-Class Attack Taxonomy Normalization
MULTICLASS_ATTACK_CATEGORIES: Dict[str, int] = {
    "benign": 0,
    "ftp-bruteforce": 1,
    "ssh-bruteforce": 2,
    "dos-attacks-goldeneye": 3,
    "dos-attacks-slowloris": 4,
    "dos-attacks-slowhttptest": 5,
    "dos-attacks-hulk": 6,
    "ddos-attacks-loic-http": 7,
    "ddos-attack-hoic": 8,
    "ddos-attack-loic-udp": 9,
    "brute force -web": 10,
    "brute force -xss": 11,
    "sql injection": 12,
    "infilteration": 13,
    "bot": 14,
}

# Explicit Leakage & Identifier Columns to Remove
LEAKAGE_COLUMNS = [
    "flow id",
    "src ip",
    "source ip",
    "dst ip",
    "destination ip",
    "src port",
    "source port",
    "timestamp",
    "unnamed: 0",
]

# The 10 Official CSE-CIC-IDS2018 Daily CSV Filenames
OFFICIAL_DAILY_CSVS = [
    "02-14-2018.csv",
    "02-15-2018.csv",
    "02-16-2018.csv",
    "02-20-2018.csv",  # 84-column file with Flow ID, Src IP, Src Port, Dst IP
    "02-21-2018.csv",  # 84-column file in some distributions
    "02-22-2018.csv",
    "02-23-2018.csv",
    "02-28-2018.csv",
    "03-01-2018.csv",
    "03-02-2018.csv",
]


@dataclass
class TrainingConfig:
    data_dir: str = str(DEFAULT_DATA_DIR)
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    model_name: str = "network-anomaly-cicids2018"
    model_version: str = "v1"
    device: str = "auto"  # "gpu", "cpu", or "auto"
    iterations: int = 1200
    depth: int = 6
    learning_rate: float = 0.05
    early_stopping_rounds: int = 50
    random_seed: int = 42
    auto_class_weights: Optional[str] = "Balanced"
    eval_metric: str = "Logloss"
    subsample_ratio: Optional[float] = None
    use_parquet_cache: bool = True
    save_local_artifact: bool = True


@dataclass
class SchemaAuditReport:
    total_files_scanned: int = 0
    file_column_counts: Dict[str, int] = field(default_factory=dict)
    normalized_feature_count: int = 0
    missing_values_count: int = 0
    infinite_values_count: int = 0
    total_rows: int = 0
    benign_rows: int = 0
    attack_rows: int = 0
    dropped_leakage_columns: List[str] = field(default_factory=list)
    class_distribution: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
