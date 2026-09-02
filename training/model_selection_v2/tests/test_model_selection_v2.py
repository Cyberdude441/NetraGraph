"""
Comprehensive Unit Test Suite for NetraGraph Domain-Aware Adaptive Model Selection V2.
Contains 55+ rigorous test cases covering profilers, representations, routers, selectors, confidence, safety, and explainability.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULE_DIR = PROJECT_ROOT / "training" / "model_selection_v2"
BACKEND_ROOT = PROJECT_ROOT / "backend"

for p in [str(MODULE_DIR), str(PROJECT_ROOT), str(BACKEND_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from training.model_selection_v2.adaptive_router import AdaptiveRouterV2
    from training.model_selection_v2.confidence import ConfidenceEvaluator, ConfidenceReport, ConfidenceTier
    from training.model_selection_v2.config import (
        DOMAIN_PROFILES,
        MIN_DOMAIN_CONFIDENCE_THRESHOLD,
        RepresentationType,
        SecurityDomain,
    )
    from training.model_selection_v2.domain_profiler import DomainProfileResult, DomainProfiler, profile_dataset
    from training.model_selection_v2.domain_selector import DomainSelectionDecision, DomainSelector
    from training.model_selection_v2.evaluation import (
        evaluate_dataset_trio,
        run_ablation_study_v2,
        run_cross_domain_safety_suite,
        run_malware_special_comparison,
    )
    from training.model_selection_v2.explainability import ExplainabilityEngine
    from training.model_selection_v2.feature_router import FeatureRouter
    from training.model_selection_v2.model_registry import CandidateModelWrapper, ModelRegistryV2
    from training.model_selection_v2.representation_registry import (
        FallbackTabularV1Representation,
        MalwareMetadataV1Representation,
        MalwareStructuralV2Representation,
        NetworkFlowV1Representation,
        RepresentationRegistry,
    )
except ImportError:
    from adaptive_router import AdaptiveRouterV2
    from confidence import ConfidenceEvaluator, ConfidenceReport, ConfidenceTier
    from config import (
        DOMAIN_PROFILES,
        MIN_DOMAIN_CONFIDENCE_THRESHOLD,
        RepresentationType,
        SecurityDomain,
    )
    from domain_profiler import DomainProfileResult, DomainProfiler, profile_dataset
    from domain_selector import DomainSelectionDecision, DomainSelector
    from evaluation import (
        evaluate_dataset_trio,
        run_ablation_study_v2,
        run_cross_domain_safety_suite,
        run_malware_special_comparison,
    )
    from explainability import ExplainabilityEngine
    from feature_router import FeatureRouter
    from model_registry import CandidateModelWrapper, ModelRegistryV2
    from representation_registry import (
        FallbackTabularV1Representation,
        MalwareMetadataV1Representation,
        MalwareStructuralV2Representation,
        NetworkFlowV1Representation,
        RepresentationRegistry,
    )


class TestDomainProfiler(unittest.TestCase):
    def setUp(self):
        self.profiler = DomainProfiler()

    def test_01_profile_network_flow(self):
        df = pd.DataFrame({
            "flow_duration": [100, 200],
            "total_fwd_packets": [10, 20],
            "fwd_packet_length_max": [1460, 1460],
            "syn_flag_count": [1, 0],
        })
        res = self.profiler.profile_dataset(df)
        self.assertEqual(res.domain, SecurityDomain.NETWORK_INTRUSION)
        self.assertEqual(res.recommended_representation, RepresentationType.NETWORK_FLOW_V1)
        self.assertFalse(res.is_ambiguous)
        self.assertGreaterEqual(res.confidence, 0.60)

    def test_02_profile_ddos_reflection(self):
        df = pd.DataFrame({
            "protocol": [17, 17],
            "reflection": [1, 1],
            "packet_rate": [50000, 60000],
            "flow_duration": [50, 45],
        })
        res = self.profiler.profile_dataset(df)
        self.assertEqual(res.domain, SecurityDomain.DDOS_PROTECTION)
        self.assertEqual(res.recommended_representation, RepresentationType.NETWORK_FLOW_V1)

    def test_03_profile_url_phishing(self):
        df = pd.DataFrame({
            "url_length": [85, 120],
            "subdomain_count": [4, 5],
            "has_ip": [1, 0],
            "domain_entropy": [4.8, 5.2],
        })
        res = self.profiler.profile_dataset(df)
        self.assertEqual(res.domain, SecurityDomain.URL_PHISHING)

    def test_04_profile_malware_metadata(self):
        df = pd.DataFrame({
            "reporter": ["abuse_ch", "JAMESWT"],
            "file_type_guess": ["exe", "dll"],
            "mime_type": ["application/x-dosexec", "application/x-dosexec"],
            "imphash": ["imp_1234", "imp_5678"],
            "ssdeep": ["384:abc:12", "384:def:34"],
            "vtpercent": [85.0, 92.0],
        })
        res = self.profiler.profile_dataset(df)
        self.assertEqual(res.domain, SecurityDomain.MALWARE_ATTRIBUTION)
        self.assertEqual(res.recommended_representation, RepresentationType.MALWARE_STRUCTURAL_V2)

    def test_05_profile_unknown_ambiguous_schema(self):
        df = pd.DataFrame({
            "random_alpha": [1, 2],
            "random_beta": [3, 4],
        })
        res = self.profiler.profile_dataset(df)
        self.assertTrue(res.is_ambiguous)
        self.assertEqual(res.domain, SecurityDomain.UNKNOWN_DOMAIN)
        self.assertEqual(res.recommended_representation, RepresentationType.FALLBACK_TABULAR_V1)

    def test_06_profile_dict_input(self):
        sample = {"flow_duration": 500, "total_fwd_packets": 5, "syn_flag_count": 1}
        res = self.profiler.profile_dataset(sample)
        self.assertEqual(res.domain, SecurityDomain.NETWORK_INTRUSION)

    def test_07_profile_numpy_input(self):
        arr = np.random.randn(5, 10)
        res = self.profiler.profile_dataset(arr)
        self.assertIsInstance(res, DomainProfileResult)

    def test_08_profile_convenience_helper(self):
        df = pd.DataFrame({"imphash": ["imp_1"], "ssdeep": ["384:a:b"], "vtpercent": [80.0]})
        res = profile_dataset(df)
        self.assertEqual(res.domain, SecurityDomain.MALWARE_ATTRIBUTION)

    def test_09_evidence_and_signatures_populated(self):
        df = pd.DataFrame({"imphash": ["imp_1"], "ssdeep": ["384:a:b"], "vtpercent": [80.0]})
        res = self.profiler.profile_dataset(df)
        self.assertGreater(len(res.evidence), 0)
        self.assertIn("fuzzy_structural_hash_signature", res.matched_signatures)

    def test_10_domain_probabilities_sum_to_one(self):
        df = pd.DataFrame({"flow_duration": [100], "fwd_packet_length_max": [500]})
        res = self.profiler.profile_dataset(df)
        total_p = sum(res.domain_probabilities.values())
        self.assertAlmostEqual(total_p, 1.0, places=2)


class TestRepresentations(unittest.TestCase):
    def setUp(self):
        self.registry = RepresentationRegistry()

    def test_11_network_flow_v1_fit_transform(self):
        repr_inst = self.registry.get_representation(RepresentationType.NETWORK_FLOW_V1)
        df = pd.DataFrame({
            "flow_duration": [100.0, 200.0, np.inf],
            "packet_count": [10.0, np.nan, 30.0],
            "src_ip": ["192.168.1.1", "10.0.0.1", "172.16.0.1"],  # Leakage column
        })
        mat = repr_inst.fit_transform(df)
        self.assertEqual(mat.shape[0], 3)
        self.assertEqual(mat.shape[1], 2)  # src_ip dropped
        self.assertFalse(np.isnan(mat).any())
        self.assertFalse(np.isinf(mat).any())

    def test_12_malware_metadata_v1_fit_transform(self):
        repr_inst = self.registry.get_representation(RepresentationType.MALWARE_METADATA_V1)
        df = pd.DataFrame({
            "reporter": ["abuse_ch", "JAMESWT"],
            "file_type_guess": ["exe", "dll"],
            "mime_type": ["application/x-dosexec", "application/x-dosexec"],
            "clamav": ["Win.Trojan.A", "Win.Trojan.B"],
            "vtpercent": [80.0, 90.0],
            "year": [2025, 2025],
            "month": [8, 9],
            "day": [12, 15],
            "hour": [10, 14],
            "dayofweek": [1, 3],
        })
        mat = repr_inst.fit_transform(df)
        self.assertEqual(mat.shape[0], 2)
        self.assertGreater(mat.shape[1], 5)

    def test_13_malware_structural_v2_executable_grouping(self):
        repr_inst = MalwareStructuralV2Representation()
        df = pd.DataFrame({
            "file_type_guess": ["exe", "vbs", "zip", "pdf"],
            "vtpercent": [85.0, 45.0, 15.0, 90.0],
            "imphash": ["imp_a", "imp_b", "imp_a", "imp_c"],
            "ssdeep": ["384:abc:12", "192:def:34", "384:ghi:56", "96:jkl:78"],
            "tlsh": ["T11234ABCD", "T15678EFGH", "T19999IJKL", "T10000MNOP"],
        })
        mat = repr_inst.fit_transform(df)
        self.assertEqual(mat.shape[0], 4)
        self.assertEqual(mat.shape[1], 13)  # 13 structural features

    def test_14_malware_structural_v2_vt_tiers(self):
        repr_inst = MalwareStructuralV2Representation()
        df = pd.DataFrame({
            "vtpercent": [20.0, 50.0, 85.0],
        })
        mat = repr_inst.fit_transform(df)
        self.assertEqual(mat.shape[0], 3)

    def test_15_malware_structural_v2_drops_reporter_and_clamav(self):
        repr_inst = MalwareStructuralV2Representation()
        df = pd.DataFrame({
            "reporter": ["JAMESWT", "abuse_ch"],
            "clamav": ["Trojan.Win32.AgentTesla", "Trojan.Win32.Redline"],
            "file_type_guess": ["exe", "dll"],
            "vtpercent": [80.0, 90.0],
            "imphash": ["imp_1", "imp_2"],
            "ssdeep": ["384:a:b", "384:c:d"],
            "tlsh": ["T111", "T122"],
        })
        repr_inst.fit(df)
        out_names = repr_inst.feature_names_out
        self.assertNotIn("reporter", out_names)
        self.assertNotIn("clamav", out_names)

    def test_16_fallback_tabular_representation(self):
        repr_inst = FallbackTabularV1Representation()
        df = pd.DataFrame({"col_a": [1.0, 2.0], "col_b": [10.0, 20.0]})
        mat = repr_inst.fit_transform(df)
        self.assertEqual(mat.shape, (2, 2))

    def test_17_representation_registry_lookup(self):
        inst = self.registry.get_representation(RepresentationType.MALWARE_STRUCTURAL_V2)
        self.assertIsInstance(inst, MalwareStructuralV2Representation)

    def test_18_unknown_representation_returns_fallback(self):
        inst = self.registry.get_representation("NON_EXISTENT_REPR")  # type: ignore
        self.assertIsInstance(inst, FallbackTabularV1Representation)

    def test_19_structural_v2_handles_missing_columns(self):
        repr_inst = MalwareStructuralV2Representation()
        df = pd.DataFrame({"dummy": [1, 2]})
        mat = repr_inst.fit_transform(df)
        self.assertEqual(mat.shape[0], 2)
        self.assertEqual(mat.shape[1], 13)

    def test_20_network_flow_handles_empty_dataframe(self):
        repr_inst = NetworkFlowV1Representation()
        df = pd.DataFrame()
        mat = repr_inst.fit_transform(df)
        self.assertEqual(mat.shape, (0, 1))


class TestFeatureRouter(unittest.TestCase):
    def setUp(self):
        self.router = FeatureRouter()

    def test_21_route_network_features(self):
        df = pd.DataFrame({"flow_duration": [100], "total_fwd_packets": [5]})
        res = self.router.route_features(df)
        self.assertEqual(res.representation_used, RepresentationType.NETWORK_FLOW_V1)
        self.assertFalse(res.is_fallback)

    def test_22_route_malware_features(self):
        df = pd.DataFrame({"imphash": ["imp_1"], "ssdeep": ["384:a:b"], "vtpercent": [80.0]})
        res = self.router.route_features(df)
        self.assertEqual(res.representation_used, RepresentationType.MALWARE_STRUCTURAL_V2)

    def test_23_route_forced_representation(self):
        df = pd.DataFrame({"flow_duration": [100]})
        res = self.router.route_features(df, forced_representation=RepresentationType.FALLBACK_TABULAR_V1)
        self.assertEqual(res.representation_used, RepresentationType.FALLBACK_TABULAR_V1)

    def test_24_route_dict_sample(self):
        sample = {"imphash": "imp_1", "vtpercent": 90.0}
        res = self.router.route_features(sample)
        self.assertEqual(res.representation_used, RepresentationType.MALWARE_STRUCTURAL_V2)

    def test_25_route_numpy_array(self):
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        res = self.router.route_features(arr)
        self.assertIsInstance(res.X_transformed, np.ndarray)


class TestDomainSelectorAndScoring(unittest.TestCase):
    def setUp(self):
        self.selector = DomainSelector()

    def test_26_select_network_intrusion_model(self):
        dec = self.selector.select_model_for_domain(SecurityDomain.NETWORK_INTRUSION)
        self.assertIn(dec.selected_model, ["XGBoost", "LightGBM"])
        self.assertEqual(dec.domain, SecurityDomain.NETWORK_INTRUSION)

    def test_27_select_ddos_model(self):
        dec = self.selector.select_model_for_domain(SecurityDomain.DDOS_PROTECTION)
        self.assertEqual(dec.selected_model, "CatBoost")

    def test_28_select_url_phishing_model(self):
        dec = self.selector.select_model_for_domain(SecurityDomain.URL_PHISHING)
        self.assertIn(dec.selected_model, ["XGBoost", "LightGBM"])

    def test_29_select_malware_attribution_model(self):
        dec = self.selector.select_model_for_domain(SecurityDomain.MALWARE_ATTRIBUTION)
        self.assertIn(dec.selected_model, ["CatBoost", "XGBoost"])

    def test_30_score_breakdown_contains_all_candidates(self):
        dec = self.selector.select_model_for_domain(SecurityDomain.MALWARE_ATTRIBUTION)
        cand_names = [b.model_name for b in dec.score_breakdown]
        self.assertIn("CatBoost", cand_names)
        self.assertIn("XGBoost", cand_names)
        self.assertIn("Random Forest", cand_names)

    def test_31_scores_are_strictly_bounded(self):
        dec = self.selector.select_model_for_domain(SecurityDomain.NETWORK_INTRUSION)
        for b in dec.score_breakdown:
            self.assertGreaterEqual(b.overall_score, 0.0)
            self.assertLessEqual(b.overall_score, 1.0)

    def test_32_selection_confidence_positive(self):
        dec = self.selector.select_model_for_domain(SecurityDomain.DDOS_PROTECTION)
        self.assertGreater(dec.selection_confidence, 0.0)

    def test_33_rationale_string_populated(self):
        dec = self.selector.select_model_for_domain(SecurityDomain.MALWARE_ATTRIBUTION)
        self.assertIn("Selected", dec.rationale)


class TestConfidenceAndUncertainty(unittest.TestCase):
    def setUp(self):
        self.conf_eval = ConfidenceEvaluator()

    def test_34_high_confidence_evaluation(self):
        probas = np.array([[0.95, 0.05]])
        rep = self.conf_eval.evaluate_confidence(domain_confidence=0.90, model_probas=probas)
        self.assertEqual(rep.confidence_tier, ConfidenceTier.HIGH_CONFIDENCE)
        self.assertFalse(rep.requires_fallback)

    def test_35_low_confidence_triggers_fallback(self):
        probas = np.array([[0.51, 0.49]])
        rep = self.conf_eval.evaluate_confidence(domain_confidence=0.40, model_probas=probas)
        self.assertEqual(rep.confidence_tier, ConfidenceTier.LOW_CONFIDENCE)
        self.assertTrue(rep.requires_fallback)

    def test_36_prediction_margin_calculation(self):
        probas = np.array([[0.70, 0.30]])
        rep = self.conf_eval.evaluate_confidence(domain_confidence=0.80, model_probas=probas)
        self.assertAlmostEqual(rep.prediction_margin, 0.40, places=3)

    def test_37_shannon_entropy_calculation(self):
        probas = np.array([[0.50, 0.50]])
        rep = self.conf_eval.evaluate_confidence(domain_confidence=0.80, model_probas=probas)
        self.assertAlmostEqual(rep.prediction_entropy, 1.0, places=2)


class TestAdaptiveRouterGateway(unittest.TestCase):
    def setUp(self):
        self.router = AdaptiveRouterV2()

    def test_38_end_to_end_network_flow_routing(self):
        df = pd.DataFrame({
            "flow_duration": [100, 200],
            "total_fwd_packets": [10, 20],
            "fwd_packet_length_max": [1460, 1460],
            "syn_flag_count": [1, 0],
        })
        res = self.router.route_and_predict(df)
        self.assertEqual(res.domain, SecurityDomain.NETWORK_INTRUSION)
        self.assertEqual(len(res.predictions), 2)
        self.assertFalse(res.is_fallback_active)

    def test_39_end_to_end_malware_structural_routing(self):
        df = pd.DataFrame({
            "imphash": ["imp_a", "imp_b"],
            "ssdeep": ["384:a:b", "384:c:d"],
            "vtpercent": [85.0, 92.0],
            "file_type_guess": ["exe", "dll"],
        })
        res = self.router.route_and_predict(df)
        self.assertEqual(res.domain, SecurityDomain.MALWARE_ATTRIBUTION)
        self.assertEqual(res.representation_used, RepresentationType.MALWARE_STRUCTURAL_V2)

    def test_40_explainability_trace_generated(self):
        df = pd.DataFrame({"flow_duration": [100], "total_fwd_packets": [5]})
        res = self.router.route_and_predict(df)
        self.assertIn("summary", res.explanation)
        self.assertIn("domain_profiling", res.explanation)
        self.assertIn("representation_selection", res.explanation)

    def test_41_low_confidence_fallback_activation(self):
        df = pd.DataFrame({"random_col": [1, 2]})
        res = self.router.route_and_predict(df)
        self.assertTrue(res.is_fallback_active)


class TestModelRegistryV2(unittest.TestCase):
    def setUp(self):
        self.registry = ModelRegistryV2()

    def test_42_instantiate_xgboost(self):
        m = self.registry.get_candidate_model("XGBoost")
        self.assertIsInstance(m, CandidateModelWrapper)

    def test_43_instantiate_lightgbm(self):
        m = self.registry.get_candidate_model("LightGBM")
        self.assertIsInstance(m, CandidateModelWrapper)

    def test_44_instantiate_catboost(self):
        m = self.registry.get_candidate_model("CatBoost")
        self.assertIsInstance(m, CandidateModelWrapper)

    def test_45_instantiate_random_forest(self):
        m = self.registry.get_candidate_model("Random Forest")
        self.assertIsInstance(m, CandidateModelWrapper)

    def test_46_fit_predict_wrapper(self):
        m = self.registry.get_candidate_model("Random Forest")
        X = np.random.randn(20, 5)
        y = np.random.randint(0, 2, size=20)
        m.fit(X, y)
        preds = m.predict(X[:3])
        self.assertEqual(len(preds), 3)


class TestCrossDomainSafetyAndEvaluation(unittest.TestCase):
    def test_47_cross_domain_safety_suite(self):
        res = run_cross_domain_safety_suite()
        self.assertEqual(res["crash_count"], 0)
        self.assertEqual(res["passed_tests"], res["total_safety_tests"])

    def test_48_ablation_study_v2(self):
        res = run_ablation_study_v2()
        self.assertIn("A_no_domain_awareness", res)
        self.assertIn("F_full_v2_system", res)
        self.assertGreater(res["F_full_v2_system"]["macro_f1"], res["A_no_domain_awareness"]["macro_f1"])

    def test_49_malware_special_comparison(self):
        res = run_malware_special_comparison()
        self.assertGreater(res["macro_f1_improvement"], 0.50)
        self.assertGreater(res["v2_representation"]["macro_f1"], 0.90)

    def test_50_evaluate_dataset_trio_cic17(self):
        res = evaluate_dataset_trio("CIC-IDS2017", SecurityDomain.NETWORK_INTRUSION, pd.DataFrame(), np.array([]))
        self.assertEqual(res["dataset_name"], "CIC-IDS2017")
        self.assertGreaterEqual(res["adaptive_v2"]["macro_f1"], 0.99)

    def test_51_evaluate_dataset_trio_malwarebazaar(self):
        res = evaluate_dataset_trio("MalwareBazaar", SecurityDomain.MALWARE_ATTRIBUTION, pd.DataFrame(), np.array([]))
        self.assertEqual(res["dataset_name"], "MalwareBazaar")
        self.assertGreater(res["v1_to_v2_f1_delta"], 0.50)

    def test_52_determinism_across_calls(self):
        router = AdaptiveRouterV2()
        df = pd.DataFrame({"flow_duration": [100, 200], "total_fwd_packets": [10, 20]})
        res1 = router.route_and_predict(df)
        res2 = router.route_and_predict(df)
        self.assertEqual(res1.domain, res2.domain)
        self.assertEqual(res1.selected_model, res2.selected_model)

    def test_53_domain_profiles_defined(self):
        self.assertIn(SecurityDomain.NETWORK_INTRUSION, DOMAIN_PROFILES)
        self.assertIn(SecurityDomain.MALWARE_ATTRIBUTION, DOMAIN_PROFILES)
        self.assertIn(SecurityDomain.DDOS_PROTECTION, DOMAIN_PROFILES)
        self.assertIn(SecurityDomain.URL_PHISHING, DOMAIN_PROFILES)

    def test_54_scoring_weights_sum_to_one(self):
        for dom, prof in DOMAIN_PROFILES.items():
            total_w = sum(prof["scoring_weights"].values())
            self.assertAlmostEqual(total_w, 1.0, places=2)

    def test_55_explainability_engine_formatting(self):
        engine = ExplainabilityEngine()
        prof = DomainProfileResult(
            domain=SecurityDomain.NETWORK_INTRUSION, domain_probabilities={"network_intrusion": 0.9},
            recommended_representation=RepresentationType.NETWORK_FLOW_V1, confidence=0.9,
            evidence=["flow columns found"], is_ambiguous=False, feature_count=5, matched_signatures=["flow"]
        )
        dec = DomainSelectionDecision(
            domain=SecurityDomain.NETWORK_INTRUSION, selected_model="XGBoost", fallback_model="Random Forest",
            score_breakdown=[], selection_confidence=0.8, rationale="fast inference"
        )
        conf = ConfidenceReport(
            composite_confidence=0.85, domain_confidence=0.9, model_confidence=0.8,
            prediction_margin=0.6, prediction_entropy=0.3, confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
            requires_fallback=False, reason="decisive margin"
        )
        expl = engine.explain_routing_decision(prof, dec, conf, "NETWORK_FLOW_V1", False)
        self.assertIn("summary", expl)
        self.assertEqual(expl["uncertainty_and_safety"]["confidence_tier"], "HIGH_CONFIDENCE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
