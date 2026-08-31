"""Comprehensive Smoke & Unit Test Suite for UNSW-NB15 Training Pipeline."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
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

from anomaly_detector import get_anomaly_detector
from config import TrainingConfig
from cross_validate_model_b import align_unsw_to_model_b_schema
from evaluate import compute_cybersecurity_metrics, evaluate_saved_artifact
from prepare_data import audit_and_validate_data, discover_unsw_files, prepare_features
from train import train_unsw_model
from utils import detect_hardware, inspect_and_extract_zip


def generate_synthetic_unsw_sample(num_rows: int = 80) -> pd.DataFrame:
    """Creates synthetic UNSW-NB15 formatted DataFrame for testing."""
    np.random.seed(42)
    protocols = ["tcp", "udp", "arp", "icmp"]
    services = ["-", "http", "ftp", "smtp", "dns", "ssh"]
    states = ["FIN", "INT", "CON", "REQ", "RST"]
    attack_cats = ["Normal", "Generic", "Exploits", "Fuzzers", "DoS"]

    df = pd.DataFrame({
        "id": np.arange(1, num_rows + 1),
        "dur": np.random.uniform(0.0001, 10.0, num_rows),
        "proto": np.random.choice(protocols, num_rows),
        "service": np.random.choice(services, num_rows),
        "state": np.random.choice(states, num_rows),
        "spkts": np.random.randint(1, 100, num_rows),
        "dpkts": np.random.randint(0, 100, num_rows),
        "sbytes": np.random.randint(100, 50000, num_rows),
        "dbytes": np.random.randint(0, 50000, num_rows),
        "rate": np.random.uniform(1.0, 5000.0, num_rows),
        "sttl": np.random.randint(31, 255, num_rows),
        "dttl": np.random.randint(0, 255, num_rows),
        "sload": np.random.uniform(100.0, 100000.0, num_rows),
        "dload": np.random.uniform(0.0, 100000.0, num_rows),
        "sloss": np.random.randint(0, 10, num_rows),
        "dloss": np.random.randint(0, 10, num_rows),
        "sinpkt": np.random.uniform(0.0, 100.0, num_rows),
        "dinpkt": np.random.uniform(0.0, 100.0, num_rows),
        "sjit": np.random.uniform(0.0, 50.0, num_rows),
        "djit": np.random.uniform(0.0, 50.0, num_rows),
        "swin": np.random.choice([0, 255], num_rows),
        "stcpb": np.random.randint(0, 1000000, num_rows),
        "dtcpb": np.random.randint(0, 1000000, num_rows),
        "dwin": np.random.choice([0, 255], num_rows),
        "tcprtt": np.random.uniform(0.0, 1.0, num_rows),
        "synack": np.random.uniform(0.0, 0.5, num_rows),
        "ackdat": np.random.uniform(0.0, 0.5, num_rows),
        "smean": np.random.randint(30, 500, num_rows),
        "dmean": np.random.randint(0, 500, num_rows),
        "trans_depth": np.random.choice([0, 1, 2], num_rows),
        "response_body_len": np.random.randint(0, 10000, num_rows),
        "ct_srv_src": np.random.randint(1, 20, num_rows),
        "ct_state_ttl": np.random.randint(0, 5, num_rows),
        "ct_dst_ltm": np.random.randint(1, 20, num_rows),
        "ct_src_dport_ltm": np.random.randint(1, 20, num_rows),
        "ct_dst_sport_ltm": np.random.randint(1, 20, num_rows),
        "ct_dst_src_ltm": np.random.randint(1, 20, num_rows),
        "is_ftp_login": np.random.choice([0, 1], num_rows),
        "ct_ftp_cmd": np.random.choice([0, 1], num_rows),
        "ct_flw_http_mthd": np.random.choice([0, 1], num_rows),
        "ct_src_ltm": np.random.randint(1, 20, num_rows),
        "ct_srv_dst": np.random.randint(1, 20, num_rows),
        "is_sm_ips_ports": np.random.choice([0, 1], num_rows),
        "attack_cat": np.random.choice(attack_cats, num_rows),
        "label": np.random.choice([0, 1], num_rows),
    })
    return df


class TestUNSWPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="unsw_test_"))
        self.data_dir = self.temp_dir / "dataset"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = self.temp_dir / "artifacts" / "network-anomaly-unsw" / "v1"

        # Create sample train and test CSVs
        self.train_df = generate_synthetic_unsw_sample(60)
        self.test_df = generate_synthetic_unsw_sample(30)
        self.train_df.to_csv(self.data_dir / "UNSW_NB15_training-set.csv", index=False)
        self.test_df.to_csv(self.data_dir / "UNSW_NB15_testing-set.csv", index=False)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_hardware_detection(self):
        hw = detect_hardware()
        self.assertIn("cuda_available", hw)
        self.assertIn("training_device", hw)
        self.assertIn(hw["training_device"], ["GPU", "CPU"])

    def test_02_safe_zip_inspection_ignores_pcaps(self):
        zip_path = self.temp_dir / "sample_archive.zip"
        extract_dir = self.temp_dir / "extracted"

        # Create ZIP containing both a CSV and a PCAP file
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("UNSW_sample.csv", "dur,proto,label\n0.1,tcp,0\n")
            z.writestr("huge_dump.pcap", b"\x00\x01\x02\x03" * 100)

        extracted = inspect_and_extract_zip(zip_path, target_extract_dir=extract_dir)
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0].name, "UNSW_sample.csv")
        self.assertFalse((extract_dir / "huge_dump.pcap").exists())

    def test_03_data_validation_and_leakage_audit(self):
        report = audit_and_validate_data(self.train_df, self.test_df)
        self.assertEqual(report.train_rows, 60)
        self.assertEqual(report.test_rows, 30)
        self.assertIn("0", report.target_distribution)
        self.assertIn("1", report.target_distribution)
        # Verify leakage columns detected
        self.assertTrue(any("id" in w for w in report.leakage_warnings))

    def test_04_feature_preparation_and_preprocessor_fitting(self):
        cfg = TrainingConfig(data_dir=str(self.data_dir), drop_leakage_cols=True)
        X_train, y_train, X_test, y_test, preprocessor, feature_names, cat_indices = prepare_features(
            self.train_df, self.test_df, cfg
        )
        self.assertNotIn("id", feature_names)
        self.assertNotIn("attack_cat", feature_names)
        self.assertIn("dur", feature_names)
        self.assertIn("proto", feature_names)

        # Verify preprocessor transforms properly
        transformed = preprocessor.transform(X_train)
        self.assertEqual(transformed.shape[0], 60)

    def test_05_smoke_training_and_artifact_bundle_creation(self):
        cfg = TrainingConfig(
            data_dir=str(self.data_dir),
            output_dir=str(self.output_dir),
            device="cpu",
            iterations=5,  # Minimal iterations for rapid smoke test
            depth=2,
            save_local_artifact=False,
        )
        saved_dir = train_unsw_model(cfg)
        self.assertTrue(saved_dir.exists())

        # Verify all 8 required companion files
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
            self.assertTrue((saved_dir / req).exists(), f"Missing artifact companion file: {req}")

        # Verify metadata content
        meta = json.loads((saved_dir / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["model_name"], "network-anomaly-unsw")
        self.assertEqual(meta["model_version"], "v1")

    def test_06_metrics_computation(self):
        y_true = np.array([0, 0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 1, 0, 0])
        metrics = compute_cybersecurity_metrics(y_true, y_pred)
        self.assertIn("false_positive_rate", metrics)
        self.assertIn("false_negative_rate", metrics)
        self.assertAlmostEqual(metrics["false_positive_rate"], 1 / 3)
        self.assertAlmostEqual(metrics["false_negative_rate"], 1 / 3)

    def test_07_model_b_schema_alignment_bridge(self):
        dummy_model_b_schema = {
            "feature_names": ["duration", "protocol_type", "src_bytes", "dst_bytes", "root_shell"],
            "target_column": "class",
        }
        aligned_df, map_report = align_unsw_to_model_b_schema(self.train_df, dummy_model_b_schema)
        self.assertEqual(len(aligned_df), 60)
        self.assertIn("duration", aligned_df.columns)
        self.assertIn("root_shell", aligned_df.columns)
        self.assertIn("duration", map_report["mapped_features"])
        self.assertIn("root_shell", map_report["unmapped_features"])

    def test_08_anomaly_detector_factory(self):
        iforest = get_anomaly_detector("isolation_forest", contamination=0.1)
        self.assertIsNotNone(iforest)
        ocsvm = get_anomaly_detector("one_class_svm")
        self.assertIsNotNone(ocsvm)
        ae = get_anomaly_detector("autoencoder")
        self.assertIsNotNone(ae)


if __name__ == "__main__":
    unittest.main()
