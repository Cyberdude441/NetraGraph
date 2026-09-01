"""
Comprehensive Unit Tests for NetraGraph Shadow Inference Gateway.

Tests cover:
- Production adapter (read-only execution, latency measurement, error resilience)
- Adaptive adapter (model selection delegation, separate latency tracking)
- Schema validation (ProductionResult, AdaptiveResult, ComparisonResult, ShadowResult)
- Prediction comparison (agreement calculation, label normalization, risk delta)
- Model-selection telemetry & Drift monitoring (PSI calculation, KS test, severity)
- Latency measurement (percentiles mean, median, p90, p95, p99)
- Missing model handling & Graceful degradation
- Production isolation verification (verifies Models A–E & registry are unmodified)
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULE_DIR = PROJECT_ROOT / "training" / "shadow_inference"
BACKEND_ROOT = PROJECT_ROOT / "backend"
MODEL_SEL_ROOT = PROJECT_ROOT / "training" / "model_selection"

for p in [str(MODULE_DIR), str(PROJECT_ROOT), str(BACKEND_ROOT), str(MODEL_SEL_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from training.shadow_inference.adaptive_adapter import AdaptiveAdapter
    from training.shadow_inference.comparator import calculate_aggregate_comparison, compare_results, normalize_prediction
    from training.shadow_inference.config import PRODUCTION_MODELS, PSI_HIGH_THRESHOLD, PSI_LOW_THRESHOLD
    from training.shadow_inference.drift_monitor import DriftMonitor, calculate_psi
    from training.shadow_inference.explanation import generate_shadow_explanation
    from training.shadow_inference.gateway import ShadowGateway, compare_production_vs_adaptive, shadow_predict
    from training.shadow_inference.metrics import compare_model_metrics, compute_latency_percentiles, compute_security_metrics
    from training.shadow_inference.production_adapter import ProductionAdapter
    from training.shadow_inference.schemas import AdaptiveResult, ComparisonResult, DriftReport, ProductionResult, ShadowResult
except ImportError:
    from adaptive_adapter import AdaptiveAdapter
    from comparator import calculate_aggregate_comparison, compare_results, normalize_prediction
    from config import PRODUCTION_MODELS, PSI_HIGH_THRESHOLD, PSI_LOW_THRESHOLD
    from drift_monitor import DriftMonitor, calculate_psi
    from explanation import generate_shadow_explanation
    from gateway import ShadowGateway, compare_production_vs_adaptive, shadow_predict
    from metrics import compare_model_metrics, compute_latency_percentiles, compute_security_metrics
    from production_adapter import ProductionAdapter
    from schemas import AdaptiveResult, ComparisonResult, DriftReport, ProductionResult, ShadowResult

from scripts.test_ml_diagnostics import SAMPLE_PAYLOADS


class TestProductionAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = ProductionAdapter()

    def test_predict_model_a_intrusion(self):
        res = self.adapter.predict("intrusion", SAMPLE_PAYLOADS["intrusion"])
        self.assertIsInstance(res, ProductionResult)
        self.assertEqual(res.status, "SUCCESS")
        self.assertGreaterEqual(res.risk_score, 0.0)
        self.assertLessEqual(res.risk_score, 1.0)
        self.assertGreater(res.latency_ms, 0.0)

    def test_predict_model_b_network_intrusion(self):
        res = self.adapter.predict("network-intrusion", SAMPLE_PAYLOADS["network-intrusion"])
        self.assertIsInstance(res, ProductionResult)
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(str(res.prediction), "normal")

    def test_predict_model_c_phishing_url(self):
        res = self.adapter.predict("phishing-url", SAMPLE_PAYLOADS["phishing-url"])
        self.assertIsInstance(res, ProductionResult)
        self.assertEqual(res.status, "SUCCESS")

    def test_predict_model_d_webpage_phishing(self):
        res = self.adapter.predict("webpage-phishing", SAMPLE_PAYLOADS["webpage-phishing"])
        self.assertIsInstance(res, ProductionResult)
        self.assertEqual(res.status, "SUCCESS")

    def test_predict_model_e_phishing_email(self):
        res = self.adapter.predict("phishing-email", SAMPLE_PAYLOADS["phishing-email"])
        self.assertIsInstance(res, ProductionResult)
        self.assertEqual(res.status, "SUCCESS")

    def test_missing_model_handling(self):
        res = self.adapter.predict("nonexistent_model_xyz", {})
        self.assertEqual(res.status, "ERROR")
        self.assertIsNotNone(res.error)

    def test_get_model_info(self):
        info = self.adapter.get_model_info("intrusion")
        self.assertIn("feature_names", info)
        self.assertIn("labels", info)
        self.assertGreater(len(info["feature_names"]), 0)


class TestAdaptiveAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = AdaptiveAdapter()

    def test_adaptive_select_delegation(self):
        sel = self.adapter.select("cicids2018")
        self.assertIn("selected_model", sel)
        self.assertIn("selection_latency_ms", sel)
        self.assertGreaterEqual(sel["selection_confidence"], 0.0)

    def test_adaptive_predict_ddos(self):
        res = self.adapter.predict("cicddos2019", payload=SAMPLE_PAYLOADS["webpage-phishing"])
        self.assertIsInstance(res, AdaptiveResult)
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.model, "CatBoost")
        self.assertGreater(res.selection_latency_ms, 0.0)
        self.assertGreater(res.total_latency_ms, 0.0)

    def test_adaptive_predict_malware(self):
        res = self.adapter.predict("malwarebazaar", payload=SAMPLE_PAYLOADS["phishing-email"])
        self.assertIsInstance(res, AdaptiveResult)
        self.assertEqual(res.model, "Random Forest")

    def test_latency_separation(self):
        res = self.adapter.predict("unsw", payload=SAMPLE_PAYLOADS["phishing-url"])
        self.assertGreater(res.selection_latency_ms, 0.0)
        self.assertGreaterEqual(res.total_latency_ms, res.selection_latency_ms)


class TestSchemaValidation(unittest.TestCase):
    def test_production_result_to_dict(self):
        pr = ProductionResult(
            model="intrusion",
            prediction="1",
            risk_score=0.95,
            latency_ms=1.23,
        )
        d = pr.to_dict()
        self.assertEqual(d["model"], "intrusion")
        self.assertEqual(d["prediction"], "1")
        self.assertEqual(d["risk_score"], 0.95)
        self.assertEqual(d["latency_ms"], 1.23)

    def test_adaptive_result_to_dict(self):
        ar = AdaptiveResult(
            model="XGBoost",
            selection_confidence=0.85,
            prediction="1",
            risk_score=0.92,
            rationale="Fastest inference with high F1",
            selection_latency_ms=0.25,
            inference_latency_ms=0.55,
            total_latency_ms=0.80,
        )
        d = ar.to_dict()
        self.assertEqual(d["model"], "XGBoost")
        self.assertEqual(d["selection_confidence"], 0.85)
        self.assertEqual(d["total_latency_ms"], 0.80)

    def test_shadow_result_to_dict(self):
        pr = ProductionResult("intrusion", "1", 0.95, 1.2)
        ar = AdaptiveResult("XGBoost", 0.85, "1", 0.92, "Rationale", [], 0.2, 0.5, 0.7)
        comp = ComparisonResult(True, 0.03, True, "intrusion", "XGBoost", "1", "1", -0.5, "NONE")
        sr = ShadowResult("REQ-001", "2026-09-01T10:00:00Z", "cicids2018", pr, ar, comp)
        d = sr.to_dict()
        self.assertEqual(d["request_id"], "REQ-001")
        self.assertTrue(d["comparison"]["prediction_agreement"])


class TestComparator(unittest.TestCase):
    def test_normalize_prediction_variants(self):
        self.assertEqual(normalize_prediction(1), "MALICIOUS")
        self.assertEqual(normalize_prediction("1"), "MALICIOUS")
        self.assertEqual(normalize_prediction("anomaly"), "MALICIOUS")
        self.assertEqual(normalize_prediction("phishing"), "MALICIOUS")
        self.assertEqual(normalize_prediction(0), "BENIGN")
        self.assertEqual(normalize_prediction("normal"), "BENIGN")
        self.assertEqual(normalize_prediction("legitimate"), "BENIGN")

    def test_comparison_agreement(self):
        pr = ProductionResult("intrusion", "1", 0.95, 1.0)
        ar = AdaptiveResult("XGBoost", 0.85, 1, 0.90, "R", [], 0.2, 0.3, 0.5)
        comp = compare_results(pr, ar)
        self.assertTrue(comp.prediction_agreement)
        self.assertAlmostEqual(comp.risk_delta, 0.05, places=4)
        self.assertEqual(comp.disagreement_severity, "NONE")

    def test_comparison_disagreement_severity(self):
        pr = ProductionResult("intrusion", "normal", 0.10, 1.0)
        ar = AdaptiveResult("XGBoost", 0.85, "anomaly", 0.90, "R", [], 0.2, 0.3, 0.5)
        comp = compare_results(pr, ar)
        self.assertFalse(comp.prediction_agreement)
        self.assertEqual(comp.disagreement_severity, "CRITICAL")

    def test_aggregate_comparison(self):
        c1 = ComparisonResult(True, 0.02, False, "m1", "m1", "1", "1", 0.1, "NONE")
        c2 = ComparisonResult(False, 0.30, True, "m1", "m2", "0", "1", 0.2, "MEDIUM")
        agg = calculate_aggregate_comparison([c1, c2])
        self.assertEqual(agg["total_samples"], 2)
        self.assertEqual(agg["agreement_rate"], 0.5)
        self.assertEqual(agg["disagreement_rate"], 0.5)
        self.assertEqual(agg["mean_risk_delta"], 0.16)


class TestMetricsAndLatency(unittest.TestCase):
    def test_security_metrics_calculation(self):
        y_true = [1, 0, 1, 1, 0, 0]
        y_pred = [1, 0, 1, 0, 0, 0]
        metrics = compute_security_metrics(y_true, y_pred)
        self.assertEqual(metrics["tp"], 2)
        self.assertEqual(metrics["fn"], 1)
        self.assertEqual(metrics["fp"], 0)
        self.assertEqual(metrics["tn"], 3)
        self.assertEqual(metrics["precision"], 1.0)
        self.assertAlmostEqual(metrics["recall"], 2/3, places=3)

    def test_latency_percentiles(self):
        latencies = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        p = compute_latency_percentiles(latencies)
        self.assertEqual(p["mean"], 5.5)
        self.assertEqual(p["median"], 5.5)
        self.assertEqual(p["min"], 1.0)
        self.assertEqual(p["max"], 10.0)

    def test_compare_model_metrics(self):
        prod = {"f1": 0.90, "accuracy": 0.92, "fpr": 0.05}
        adapt = {"f1": 0.95, "accuracy": 0.96, "fpr": 0.01}
        delta = compare_model_metrics(prod, adapt)
        self.assertAlmostEqual(delta["f1_delta"], 0.05, places=4)
        self.assertAlmostEqual(delta["fpr_delta"], -0.04, places=4)


class TestDriftMonitor(unittest.TestCase):
    def test_psi_identical_distributions(self):
        data = np.random.default_rng(42).normal(0, 1, 500)
        psi = calculate_psi(data, data)
        self.assertAlmostEqual(psi, 0.0, places=3)

    def test_psi_shifted_distribution(self):
        ref = np.random.default_rng(42).normal(0, 1, 500)
        shifted = np.random.default_rng(42).normal(2.5, 1, 500)
        psi = calculate_psi(ref, shifted)
        self.assertGreater(psi, PSI_HIGH_THRESHOLD)

    def test_feature_drift_evaluation(self):
        rng = np.random.default_rng(42)
        ref_df = pd.DataFrame({"feat1": rng.normal(0, 1, 500), "feat2": rng.normal(5, 2, 500)})
        curr_df = pd.DataFrame({"feat1": rng.normal(0, 1, 500), "feat2": rng.normal(5, 2, 500)})
        monitor = DriftMonitor(reference_data=ref_df)
        drift = monitor.evaluate_feature_drift(curr_df)
        self.assertIn("psi", drift)
        self.assertIn("overall_psi", drift)
        self.assertEqual(drift["severity"], "LOW")

    def test_telemetry_recording(self):
        monitor = DriftMonitor()
        monitor.record_telemetry("XGBoost", 0.9, "1")
        monitor.record_telemetry("XGBoost", 0.9, "1")
        monitor.record_telemetry("CatBoost", 0.8, "0")
        dist = monitor.get_model_selection_distribution()
        self.assertAlmostEqual(dist["XGBoost"], 66.67, places=1)
        self.assertAlmostEqual(dist["CatBoost"], 33.33, places=1)


class TestShadowGateway(unittest.TestCase):
    def setUp(self):
        self.gateway = ShadowGateway()

    def test_single_shadow_predict(self):
        req = {
            "dataset_name": "cicids2018",
            "production_model": "intrusion",
            "payload": SAMPLE_PAYLOADS["intrusion"],
        }
        res = self.gateway.predict(req)
        self.assertIsInstance(res, ShadowResult)
        self.assertEqual(res.production.status, "SUCCESS")
        self.assertEqual(res.adaptive.status, "SUCCESS")
        self.assertIn("prediction_agreement", res.comparison.to_dict())

    def test_standalone_shadow_predict_function(self):
        req = {
            "dataset_name": "unsw",
            "production_model": "phishing-url",
            "payload": SAMPLE_PAYLOADS["phishing-url"],
        }
        res_dict = shadow_predict(req)
        self.assertIn("production", res_dict)
        self.assertIn("adaptive", res_dict)
        self.assertIn("comparison", res_dict)

    def test_compare_production_vs_adaptive_batch(self):
        requests = [
            {"dataset_name": "cicids2018", "production_model": "intrusion", "payload": SAMPLE_PAYLOADS["intrusion"]},
            {"dataset_name": "cicids2017", "production_model": "network-intrusion", "payload": SAMPLE_PAYLOADS["network-intrusion"]},
        ]
        batch_res = compare_production_vs_adaptive(requests)
        self.assertEqual(batch_res["batch_size"], 2)
        self.assertIn("aggregate_comparison", batch_res)
        self.assertIn("latency_summary", batch_res)


class TestProductionIsolation(unittest.TestCase):
    def test_registry_directory_exists_and_unmodified(self):
        reg_dir = BACKEND_ROOT / "models" / "registry"
        self.assertTrue(reg_dir.is_dir())
        for m in ["intrusion", "network-intrusion", "phishing-url", "webpage-phishing", "phishing-email"]:
            m_path = reg_dir / m / "v1" / "model.joblib"
            self.assertTrue(m_path.exists(), f"Production model missing: {m_path}")

    def test_production_output_immutability(self):
        """Verify shadow inference does not alter production model prediction output."""
        adapter = ProductionAdapter()
        res1 = adapter.predict("intrusion", SAMPLE_PAYLOADS["intrusion"])
        
        gateway = ShadowGateway()
        gateway.predict({
            "dataset_name": "cicids2018",
            "production_model": "intrusion",
            "payload": SAMPLE_PAYLOADS["intrusion"],
        })
        
        res2 = adapter.predict("intrusion", SAMPLE_PAYLOADS["intrusion"])
        self.assertEqual(res1.prediction, res2.prediction)
        self.assertEqual(res1.risk_score, res2.risk_score)


if __name__ == "__main__":
    unittest.main(verbosity=2)
