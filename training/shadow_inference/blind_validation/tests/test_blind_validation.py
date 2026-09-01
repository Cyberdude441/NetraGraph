"""
Unit Tests for Blind Holdout and Adversarial Validation Module.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BACKEND_ROOT = PROJECT_ROOT / "backend"
MODEL_SEL_ROOT = PROJECT_ROOT / "training" / "model_selection"
SHADOW_ROOT = PROJECT_ROOT / "training" / "shadow_inference"
BLIND_ROOT = SHADOW_ROOT / "blind_validation"

for p in [str(MODEL_SEL_ROOT), str(SHADOW_ROOT), str(BLIND_ROOT), str(PROJECT_ROOT), str(BACKEND_ROOT)]:
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

from blind_config import audit_frozen_system_hashes, EVALUATION_SEEDS
from calibration_audit import calculate_ece, evaluate_calibration
from holdout_generator import generate_adversarial_stress_set, generate_blind_holdout_for_seed, hash_payload
from latency_audit import run_8stage_latency_audit


class TestBlindHoldoutGenerator(unittest.TestCase):
    def test_blind_holdout_generation(self):
        samples, audit = generate_blind_holdout_for_seed(seed=42, n_per_dataset=10)
        self.assertEqual(len(samples), 50)
        self.assertEqual(audit["total_samples"], 50)
        self.assertEqual(audit["duplicate_count"], 0)
        self.assertEqual(audit["cross_split_duplicate_rate"], 0.0)

    def test_payload_hash_reproducibility(self):
        p1 = {"a": 1, "b": "test"}
        p2 = {"b": "test", "a": 1}
        self.assertEqual(hash_payload(p1), hash_payload(p2))

    def test_adversarial_stress_set(self):
        stress_set = generate_adversarial_stress_set(seed=999)
        self.assertEqual(len(stress_set), 100)
        categories = {s["stress_category"] for s in stress_set}
        self.assertGreaterEqual(len(categories), 4)


class TestCalibrationAudit(unittest.TestCase):
    def test_calculate_ece_perfect(self):
        y_true = np.array([1, 1, 0, 0])
        y_prob = np.array([1.0, 1.0, 0.0, 0.0])
        ece = calculate_ece(y_true, y_prob)
        self.assertAlmostEqual(ece, 0.0, places=3)

    def test_evaluate_calibration_metrics(self):
        y_true = np.array([1, 0, 1, 0, 1, 0])
        p_prob = np.array([0.9, 0.2, 0.8, 0.3, 0.7, 0.4])
        a_prob = np.array([0.95, 0.05, 0.90, 0.10, 0.85, 0.15])
        cal = evaluate_calibration(y_true, p_prob, a_prob)
        self.assertIn("production", cal)
        self.assertIn("adaptive", cal)
        self.assertIn("delta", cal)
        self.assertGreaterEqual(cal["production"]["brier_score"], 0.0)
        self.assertGreaterEqual(cal["adaptive"]["brier_score"], 0.0)


class TestLatencyAudit(unittest.TestCase):
    def test_run_8stage_latency_audit(self):
        audit = run_8stage_latency_audit(n_warmup=5, n_iterations=20)
        self.assertIn("stages", audit)
        self.assertEqual(len(audit["stages"]), 8)
        for stage_name, metrics in audit["stages"].items():
            self.assertGreaterEqual(metrics["mean"], 0.0)
            self.assertGreaterEqual(metrics["median"], 0.0)


class TestSystemFreezeAndImmutability(unittest.TestCase):
    def test_audit_frozen_hashes(self):
        hashes = audit_frozen_system_hashes()
        self.assertGreaterEqual(len(hashes), 5)
        for k, v in hashes.items():
            self.assertEqual(len(v), 64, f"Invalid SHA-256 hash length for {k}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
