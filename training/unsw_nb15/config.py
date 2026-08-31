"""UNSW-NB15 Pipeline Configuration & Hyperparameters."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Default Paths
DEFAULT_DATA_DIR = Path("/content/UNSW-NB15")
DEFAULT_OUTPUT_DIR = Path("artifacts/network-anomaly-unsw/v1")
LOCAL_ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts" / "network-anomaly-unsw" / "v1"

# Target & Category Specifications
PRIMARY_TARGET = "label"  # Binary: 0 = Normal, 1 = Attack
SECONDARY_TARGET = "attack_cat"  # Multi-class attack taxonomy

LABEL_MAPPING = {
    "0": "normal",
    "1": "attack",
}

# Identifier & Leakage Columns to Drop
LEAKAGE_COLUMNS = [
    "id",
    "srcip",
    "dstip",
    "sport",
    "dsport",
    "Stime",
    "Ltime",
    "attack_cat",  # Secondary target must never leak into binary target matrix
]

# Official UNSW-NB15 Categorical Feature Columns
CATEGORICAL_FEATURES = [
    "proto",
    "service",
    "state",
]

# Expected Official CSV Filenames
OFFICIAL_TRAIN_FILE = "UNSW_NB15_training-set.csv"
OFFICIAL_TEST_FILE = "UNSW_NB15_testing-set.csv"
RAW_PART_FILES = [
    "UNSW-NB15_1.csv",
    "UNSW-NB15_2.csv",
    "UNSW-NB15_3.csv",
    "UNSW-NB15_4.csv",
]


@dataclass
class TrainingConfig:
    data_dir: str = str(DEFAULT_DATA_DIR)
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    model_name: str = "network-anomaly-unsw"
    model_version: str = "v1"
    device: str = "auto"  # "gpu", "cpu", or "auto"
    iterations: int = 1000
    depth: int = 6
    learning_rate: float = 0.05
    early_stopping_rounds: int = 50
    random_seed: int = 42
    auto_class_weights: Optional[str] = "Balanced"
    eval_metric: str = "Logloss"
    subsample_ratio: Optional[float] = None  # Optional fraction for rapid Colab prototyping
    drop_leakage_cols: bool = True
    save_local_artifact: bool = True


@dataclass
class DataValidationReport:
    total_files_found: int = 0
    file_names: List[str] = field(default_factory=list)
    train_rows: int = 0
    test_rows: int = 0
    feature_count: int = 0
    missing_values: dict = field(default_factory=dict)
    duplicate_rows: int = 0
    train_test_overlap_rows: int = 0
    constant_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    numerical_columns: List[str] = field(default_factory=list)
    target_distribution: dict = field(default_factory=dict)
    leakage_warnings: List[str] = field(default_factory=list)
