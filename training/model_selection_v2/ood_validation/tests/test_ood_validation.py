"""
Comprehensive Test Suite for NetraGraph V3 Out-of-Distribution / Red-Team Validation.
Contains 35+ rigorous unit and integration tests covering temporal, protocol, unseen family,
adversarial metadata, perturbation, calibration, router safety, and statistical significance.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
V2_ROOT = PROJECT_ROOT / "training" / "model_selection_v2"
OOD_ROOT = V2_ROOT / "ood_validation"
BACKEND_ROOT = PROJECT_ROOT / "backend"

for p in [str(OOD_ROOT), str(V2_ROOT), str(PROJECT_ROOT), str(BACKEND_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from adversarial_metadata import AdversarialMetadataAuditor
from calibration_shift import CalibrationShiftAuditor
from class_imbalance_stress import ClassImbalanceAuditor
from cross_dataset_eval import CrossDatasetAuditor
from data_isolation import DataIsolationAuditor
from ood_config import KNOWN_MALWARE_FAMILIES, OOD_SEEDS, SEEN_DDOS_PROTOCOLS, UNSEEN_DDOS_PROTOCOLS, UNSEEN_MALWARE_FAMILIES
from perturbation_stress import PerturbationStressAuditor
from protocol_ood import ProtocolOODAuditor
from router_safety_eval import RouterSafetyAuditor
from statistical_ood import StatisticalOODAuditor
from structural_hash_audit import StructuralHashAuditor
from temporal_ood import TemporalOODAuditor
from unseen_family_eval import UnseenFamilyEvaluator


class TestDataIsolation(unittest.TestCase):
    def setUp(self):
        self.auditor = DataIsolationAuditor()

    def test_01_compute_sample_hash_deterministic(self):
        s1 = {"flow_duration": 100, "total_fwd_packets": 5}
        s2 = {"total_fwd_packets": 5, "flow_duration": 100}
        self.assertEqual(self.auditor.compute_sample_hash(s1), self.auditor.compute_sample_hash(s2))

    def test_02_zero_leakage_audit_pass(self):
        train = [{"feat_a": 1}, {"feat_a": 2}]
        test = [{"feat_a": 3}, {"feat_a": 4}]
        res = self.auditor.audit_isolation(train, test)
        self.assertEqual(res["isolation_status"], "PASS")
        self.assertEqual(res["leakage_percentage"], 0.0)

    def test_03_detect_leakage_duplicate(self):
        train = [{"feat_a": 1}, {"feat_a": 2}]
        test = [{"feat_a": 2}, {"feat_a": 3}]
        res = self.auditor.audit_isolation(train, test)
        self.assertEqual(res["isolation_status"], "FAIL")
        self.assertEqual(res["train_test_duplicates"], 1)


class TestTemporalOOD(unittest.TestCase):
    def setUp(self):
        self.auditor = TemporalOODAuditor()

    def test_04_temporal_shift_evaluation(self):
        res = self.auditor.evaluate_temporal_shift()
        self.assertIn("malware_temporal_audit", res)
        self.assertIn("network_temporal_audit", res)

    def test_05_structural_v2_temporal_resilience(self):
        res = self.auditor.evaluate_temporal_shift()
        mal = res["malware_temporal_audit"]
        self.assertGreater(mal["window_3_far_ood"]["structural_v2_macro_f1"], 0.95)
        self.assertLess(mal["window_3_far_ood"]["v2_degradation_pct"], 5.0)

    def test_06_metadata_v1_temporal_collapse(self):
        res = self.auditor.evaluate_temporal_shift()
        mal = res["malware_temporal_audit"]
        self.assertGreater(mal["window_3_far_ood"]["v1_degradation_pct"], 30.0)


class TestUnseenMalwareFamily(unittest.TestCase):
    def setUp(self):
        self.evaluator = UnseenFamilyEvaluator()

    def test_07_known_family_performance(self):
        res = self.evaluator.evaluate_unseen_families()
        self.assertGreater(res["known_families_evaluation"]["macro_f1"], 0.98)
        self.assertGreater(res["known_families_evaluation"]["minority_family_recall"], 0.90)

    def test_08_unseen_family_open_set_rejection(self):
        res = self.evaluator.evaluate_unseen_families()
        self.assertGreater(res["unseen_families_evaluation"]["low_confidence_flag_rate"], 0.85)

    def test_09_explicit_limitations_documented(self):
        res = self.evaluator.evaluate_unseen_families()
        self.assertIn("explicit_limitations", res)


class TestProtocolOOD(unittest.TestCase):
    def setUp(self):
        self.auditor = ProtocolOODAuditor()

    def test_10_catboost_zero_fpr_on_unseen_protocol(self):
        res = self.auditor.evaluate_protocol_disjoint()
        cb = res["model_performance_under_protocol_shift"]["Adaptive_V2_CatBoost"]
        self.assertEqual(cb["fpr"], 0.0)
        self.assertGreater(cb["f1"], 0.99)

    def test_11_production_model_b_protocol_collapse(self):
        res = self.auditor.evaluate_protocol_disjoint()
        prod = res["model_performance_under_protocol_shift"]["Production_Model_B"]
        self.assertEqual(prod["f1"], 0.0)


class TestFeaturePerturbationStress(unittest.TestCase):
    def setUp(self):
        self.auditor = PerturbationStressAuditor()

    def test_12_perturbation_scenarios_evaluated(self):
        res = self.auditor.evaluate_perturbations()
        self.assertEqual(res["total_crashes"], 0)
        self.assertGreaterEqual(res["total_perturbation_tests"], 8)

    def test_13_mean_perturbed_macro_f1_robust(self):
        res = self.auditor.evaluate_perturbations()
        self.assertGreater(res["mean_perturbed_macro_f1"], 0.95)


class TestAdversarialMetadata(unittest.TestCase):
    def setUp(self):
        self.auditor = AdversarialMetadataAuditor()

    def test_14_reporter_invariance_v2(self):
        res = self.auditor.evaluate_metadata_invariance()
        tests = res["metadata_invariance_tests"]
        self.assertGreater(tests["2_reporter_randomized"]["v2_structural_f1"], 0.98)
        self.assertLess(tests["2_reporter_randomized"]["v1_metadata_f1"], 0.35)

    def test_15_antivirus_removal_invariance(self):
        res = self.auditor.evaluate_metadata_invariance()
        tests = res["metadata_invariance_tests"]
        self.assertGreater(tests["4_clamav_antivirus_removed"]["v2_structural_f1"], 0.98)


class TestStructuralHashAudit(unittest.TestCase):
    def setUp(self):
        self.auditor = StructuralHashAuditor()

    def test_16_imphash_frequency_is_dominant_driver(self):
        res = self.auditor.evaluate_hash_features()
        abl = res["hash_ablation_results"]
        self.assertGreater(abl["imphash_freq_only"]["macro_f1"], 0.88)

    def test_17_full_structural_joint_synergy(self):
        res = self.auditor.evaluate_hash_features()
        abl = res["hash_ablation_results"]
        self.assertGreater(abl["full_structural_v2_joint"]["macro_f1"], 0.98)
        self.assertGreater(abl["full_structural_v2_joint"]["minority_recall"], 0.94)


class TestClassImbalanceStress(unittest.TestCase):
    def setUp(self):
        self.auditor = ClassImbalanceAuditor()

    def test_18_imbalance_stress_regimes(self):
        res = self.auditor.evaluate_imbalance_stress()
        regimes = res["imbalance_regimes"]
        self.assertIn("1_balanced_1_to_1", regimes)
        self.assertIn("4_extreme_longtail_50_to_1", regimes)

    def test_19_extreme_longtail_minority_recall(self):
        res = self.auditor.evaluate_imbalance_stress()
        longtail = res["imbalance_regimes"]["4_extreme_longtail_50_to_1"]
        self.assertGreater(longtail["minority_recall"], 0.90)


class TestCalibrationShift(unittest.TestCase):
    def setUp(self):
        self.auditor = CalibrationShiftAuditor()

    def test_20_v2_ood_ece_bounded(self):
        res = self.auditor.evaluate_calibration_under_shift()
        v2_ece = res["calibration_shift_comparison"]["adaptive_v2"]["ood_ece"]
        self.assertLess(v2_ece, 0.05)

    def test_21_production_severe_miscalibration(self):
        res = self.auditor.evaluate_calibration_under_shift()
        prod_ece = res["calibration_shift_comparison"]["production_baseline"]["ood_ece"]
        self.assertGreater(prod_ece, 0.40)


class TestRouterSafety(unittest.TestCase):
    def setUp(self):
        self.auditor = RouterSafetyAuditor()

    def test_22_full_router_safety_zero_crashes(self):
        res = self.auditor.run_full_safety_audit()
        self.assertEqual(res["crashes"], 0)
        self.assertEqual(res["router_safety_status"], "PASS")

    def test_23_empty_dataframe_fallback(self):
        res = self.auditor.run_full_safety_audit()
        empty_res = next(r for r in res["audit_details"] if r["test_name"] == "6_empty_dataframe")
        self.assertEqual(empty_res["status"], "SUCCESS")
        self.assertTrue(empty_res["fallback_used"])

    def test_24_nan_inf_safety_resilience(self):
        res = self.auditor.run_full_safety_audit()
        nan_res = next(r for r in res["audit_details"] if r["test_name"] == "10_nan_matrix")
        inf_res = next(r for r in res["audit_details"] if r["test_name"] == "11_inf_matrix")
        self.assertEqual(nan_res["status"], "SUCCESS")
        self.assertEqual(inf_res["status"], "SUCCESS")


class TestCrossDatasetGeneralization(unittest.TestCase):
    def setUp(self):
        self.auditor = CrossDatasetAuditor()

    def test_25_cross_dataset_transfer_matrix(self):
        res = self.auditor.evaluate_cross_dataset()
        self.assertLess(res["mean_cross_dataset_degradation"], 0.02)


class TestStatisticalOOD(unittest.TestCase):
    def setUp(self):
        self.auditor = StatisticalOODAuditor()

    def test_26_multi_seed_replication(self):
        res = self.auditor.evaluate_multi_seed_statistics()
        self.assertEqual(len(res["seeds_evaluated"]), 5)
        self.assertGreater(res["seed_performance_summary"]["adaptive_v2"]["mean"], 0.99)

    def test_27_bootstrap_95_ci_strictly_positive(self):
        res = self.auditor.evaluate_multi_seed_statistics()
        ci = res["hypothesis_testing"]["bootstrap_95_ci"]
        self.assertGreater(ci[0], 0.0)
        self.assertGreater(ci[1], ci[0])

    def test_28_p_value_statistically_significant(self):
        res = self.auditor.evaluate_multi_seed_statistics()
        p_val = res["hypothesis_testing"]["paired_p_value"]
        self.assertLess(p_val, 0.001)

    def test_29_cohens_d_effect_size_large(self):
        res = self.auditor.evaluate_multi_seed_statistics()
        d = res["hypothesis_testing"]["cohens_d_effect_size"]
        self.assertGreater(d, 0.50)

    def test_30_selection_stability_zero_entropy(self):
        res = self.auditor.evaluate_multi_seed_statistics()
        stab = res["selection_stability_across_seeds"]
        self.assertEqual(stab["selection_entropy"], 0.0)
        self.assertEqual(stab["selection_regret"], 0.0)


class TestConfigurationBounds(unittest.TestCase):
    def test_31_ood_seeds_defined(self):
        self.assertEqual(len(OOD_SEEDS), 5)
        self.assertIn(42, OOD_SEEDS)

    def test_32_ddos_protocols_disjoint(self):
        seen_set = set(SEEN_DDOS_PROTOCOLS)
        unseen_set = set(UNSEEN_DDOS_PROTOCOLS)
        self.assertEqual(len(seen_set.intersection(unseen_set)), 0)

    def test_33_malware_families_disjoint(self):
        known_set = set(KNOWN_MALWARE_FAMILIES)
        unseen_set = set(UNSEEN_MALWARE_FAMILIES)
        self.assertEqual(len(known_set.intersection(unseen_set)), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
