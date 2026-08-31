"""Comprehensive Smoke & Unit Test Suite for CSE-CIC-IDS2018 Training Pipeline."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Path setup
TEST_DIR = Path(__file__).resolve().parent
TRAINING_DIR = TEST_DIR.parent
PROJECT_ROOT = TRAINING_DIR.parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

import sys
if str(TRAINING_DIR) not in sys.path:
    sys.path.insert(0, str(TRAINING_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import MULTICLASS_ATTACK_CATEGORIES, TrainingConfig
from cross_validate_models import align_cicids_to_model_b_schema
from evaluate import compute_cybersecurity_metrics, evaluate_saved_artifact
from prepare_data import (
    load_and_merge_cicids2018_files,
    normalize_dataframe_schema,
    prepare_cicids2018_features,
    sanitize_numeric_values,
)
from threshold_analysis import sweep_decision_thresholds
from train_binary import train_cicids2018_binary
from train_multiclass import train_cicids2018_multiclass
from utils import detect_hardware, save_parquet_cache


def generate_synthetic_cicids_80col(num_rows: int = 50) -> pd.DataFrame:
    """Generates synthetic 80-column CIC-IDS2018 partition."""
    np.random.seed(42)
    cols = [
        "Dst Port", "Protocol", "Timestamp", "Flow Duration", "Tot Fwd Pkts", "Tot Bwd Pkts",
        "TotLen Fwd Pkts", "TotLen Bwd Pkts", "Fwd Pkt Len Max", "Fwd Pkt Len Min", "Fwd Pkt Len Mean",
        "Fwd Pkt Len Std", "Bwd Pkt Len Max", "Bwd Pkt Len Min", "Bwd Pkt Len Mean", "Bwd Pkt Len Std",
        "Flow Byts/s", "Flow Pkts/s", "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
        "Fwd IAT Tot", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Tot",
        "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min", "Fwd PSH Flags", "Bwd PSH Flags",
        "Fwd URG Flags", "Bwd URG Flags", "Fwd Header Len", "Bwd Header Len", "Fwd Pkts/s", "Bwd Pkts/s",
        "Pkt Len Min", "Pkt Len Max", "Pkt Len Mean", "Pkt Len Std", "Pkt Len Var", "FIN Flag Cnt",
        "SYN Flag Cnt", "RST Flag Cnt", "PSH Flag Cnt", "ACK Flag Cnt", "URG Flag Cnt", "CWE Flag Count",
        "ECE Flag Cnt", "Down/Up Ratio", "Pkt Size Avg", "Fwd Seg Size Avg", "Bwd Seg Size Avg",
        "Fwd Byts/b Avg", "Fwd Pkts/b Avg", "Fwd Blk Rate Avg", "Bwd Byts/b Avg", "Bwd Pkts/b Avg",
        "Bwd Blk Rate Avg", "Subflow Fwd Pkts", "Subflow Fwd Byts", "Subflow Bwd Pkts", "Subflow Bwd Byts",
        "Init Fwd Win Byts", "Init Bwd Win Byts", "Fwd Act Data Pkts", "Fwd Seg Size Min", "Active Mean",
        "Active Std", "Active Max", "Active Min", "Idle Mean", "Idle Std", "Idle Max", "Idle Min",
    ]
    data = {c: np.random.uniform(0.0, 1000.0, num_rows) for c in cols}
    data["Timestamp"] = ["14/02/2018 08:31:01"] * num_rows
    # Add infinite values to test numerical sanitization
    data["Flow Byts/s"][0] = np.inf
    data["Flow Pkts/s"][1] = -np.inf
    data["Label"] = np.random.choice(["Benign", "FTP-BruteForce", "SSH-Bruteforce", "DoS-attacks-Hulk"], num_rows)
    return pd.DataFrame(data)


def generate_synthetic_cicids_84col(num_rows: int = 50) -> pd.DataFrame:
    """Generates synthetic 84-column CIC-IDS2018 partition with Flow ID, Src IP, Src Port, Dst IP."""
    df_80 = generate_synthetic_cicids_80col(num_rows)
    df_80["Flow ID"] = [f"192.168.1.1-10.0.0.1-{i}" for i in range(num_rows)]
    df_80["Src IP"] = ["192.168.1.50"] * num_rows
    df_80["Src Port"] = [443] * num_rows
    df_80["Dst IP"] = ["10.0.0.1"] * num_rows
    return df_80


class TestCICIDS2018Pipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cicids_test_"))
        self.data_dir = self.temp_dir / "dataset"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = self.temp_dir / "artifacts" / "network-anomaly-cicids2018" / "v1"

        # Create both 80-col and 84-col CSV partitions
        self.df_80 = generate_synthetic_cicids_80col(60)
        self.df_84 = generate_synthetic_cicids_84col(60)
        self.df_80.to_csv(self.data_dir / "02-14-2018.csv", index=False)
        self.df_84.to_csv(self.data_dir / "02-20-2018.csv", index=False)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_hardware_detection(self):
        hw = detect_hardware()
        self.assertIn("cuda_available", hw)
        self.assertIn("training_device", hw)
        self.assertIn(hw["training_device"], ["GPU", "CPU"])

    def test_02_schema_harmonization_80_vs_84_columns(self):
        clean_80, dropped_80 = normalize_dataframe_schema(self.df_80)
        clean_84, dropped_84 = normalize_dataframe_schema(self.df_84)

        # Leakage headers must be dropped from 84-col file
        self.assertIn("Timestamp", dropped_80)
        self.assertIn("Flow ID", dropped_84)
        self.assertIn("Src IP", dropped_84)
        self.assertIn("Dst IP", dropped_84)

        # Columns must now be identical between the two files
        self.assertEqual(sorted(list(clean_80.columns)), sorted(list(clean_84.columns)))

    def test_03_infinite_and_nan_numerical_sanitization(self):
        clean_80, _ = normalize_dataframe_schema(self.df_80)
        feature_cols = [c for c in clean_80.columns if c != "Label"]
        sanitized = sanitize_numeric_values(clean_80, feature_cols)

        # Verify no infinite values remain
        num_inf = np.isinf(sanitized[feature_cols].select_dtypes(include=[np.number])).sum().sum()
        self.assertEqual(num_inf, 0)

    def test_04_multi_file_loading_and_parquet_cache(self):
        merged_df, report = load_and_merge_cicids2018_files(self.data_dir, use_cache=True)
        self.assertEqual(report.total_rows, 120)
        self.assertEqual(len(report.file_column_counts), 2)
        self.assertIn("02-14-2018.csv", report.file_column_counts)
        self.assertIn("02-20-2018.csv", report.file_column_counts)

    def test_05_feature_prep_and_preprocessor_fitting(self):
        merged_df, _ = load_and_merge_cicids2018_files(self.data_dir, use_cache=False)
        X_train, y_train, X_test, y_test, preprocessor, feature_names = prepare_cicids2018_features(
            merged_df, target_mode="binary"
        )
        self.assertEqual(X_train.shape[0] + X_test.shape[0], 120)
        self.assertNotIn("Flow ID", feature_names)
        self.assertNotIn("Timestamp", feature_names)

        # Preprocessor transform check
        X_train_trans = preprocessor.transform(X_train)
        self.assertEqual(X_train_trans.shape[0], X_train.shape[0])

    def test_06_decision_threshold_sweeper(self):
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y_proba = np.array([0.05, 0.10, 0.15, 0.60, 0.40, 0.85, 0.90, 0.95])
        results = sweep_decision_thresholds(y_true, y_proba, target_fpr_limit=0.25)
        self.assertIn("best_f1_threshold", results)
        self.assertIn("best_f1_metrics", results)
        self.assertIn("fpr_constrained_threshold", results)

    def test_07_binary_smoke_training_and_artifact_bundle(self):
        cfg = TrainingConfig(
            data_dir=str(self.data_dir),
            output_dir=str(self.output_dir),
            device="cpu",
            iterations=5,
            depth=2,
            use_parquet_cache=False,
            save_local_artifact=False,
        )
        saved_dir = train_cicids2018_binary(cfg)
        self.assertTrue(saved_dir.exists())

        required_files = [
            "model.joblib",
            "preprocessor.joblib",
            "feature_schema.json",
            "label_mapping.json",
            "metrics.json",
            "metadata.json",
            "requirements_model.txt",
            "training_report.json",
        ]
        for req in required_files:
            self.assertTrue((saved_dir / req).exists(), f"Missing companion file: {req}")

        meta = json.loads((saved_dir / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["model_name"], "network-anomaly-cicids2018")
        self.assertEqual(meta["model_version"], "v1")

    def test_08_multiclass_smoke_training(self):
        cfg = TrainingConfig(
            data_dir=str(self.data_dir),
            device="cpu",
            iterations=5,
            depth=2,
            use_parquet_cache=False,
        )
        output_dir = train_cicids2018_multiclass(cfg)
        self.assertTrue(output_dir.exists())
        self.assertTrue((output_dir / "model.joblib").exists())
        self.assertTrue((output_dir / "label_mapping.json").exists())

    def test_09_cross_dataset_schema_bridge(self):
        dummy_model_b_schema = {
            "feature_names": ["duration", "src_bytes", "dst_bytes", "count", "protocol_type"],
            "target_column": "class",
        }
        aligned_df, map_report = align_cicids_to_model_b_schema(self.df_80, dummy_model_b_schema)
        self.assertEqual(len(aligned_df), 60)
        self.assertIn("duration", aligned_df.columns)
        self.assertIn("duration", map_report["mapped"])


if __name__ == "__main__":
    unittest.main()
