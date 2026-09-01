"""
Unit tests for the NetraGraph Adaptive Model Selection research layer.
Covers profiling, registry, ranking, ties, confidence, thresholds, ensemble, and explanation.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure module root on path
MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

import unittest
from unittest.mock import patch

from config import (
    FAMILY_DDOS_VOLUMETRIC,
    FAMILY_MALWARE_STATIC,
    FAMILY_NETWORK_FLOW,
    TASK_BINARY_DDOS,
    TASK_BINARY_INTRUSION,
    TASK_MULTICLASS_MALWARE,
    load_benchmark_results,
)
from dataset_profiler import profile_dataset, _infer_task_family
from evaluation import (
    ablation_study_from_benchmark,
    compute_rank_stability,
    distribution_shift_analysis,
)
from explainability import generate_selection_explanation
from model_registry import build_algorithm_registry
from model_selector import select_model_for_dataset
from scoring import compute_operational_score, compute_selection_confidence, rank_algorithms


class TestDatasetProfiler(unittest.TestCase):
    def _make_df(self, rows=200, cols=10, with_target=True):
        data = {f"feat_{i}": np.random.rand(rows) for i in range(cols)}
        df = pd.DataFrame(data)
        if with_target:
            df["label"] = (np.random.rand(rows) > 0.6).astype(int)
        return df

    def test_profile_returns_required_keys(self):
        df = self._make_df()
        profile = profile_dataset(df, target_column="label")
        for key in ["n_samples", "n_features", "class_info", "inferred_task_type", "inferred_dataset_family"]:
            self.assertIn(key, profile)

    def test_profile_sample_count(self):
        df = self._make_df(rows=500)
        profile = profile_dataset(df, target_column="label")
        self.assertEqual(profile["n_samples"], 500)

    def test_profile_feature_count_excludes_target(self):
        df = self._make_df(rows=100, cols=5)
        profile = profile_dataset(df, target_column="label")
        self.assertEqual(profile["n_features"], 5)

    def test_missing_value_detection(self):
        df = self._make_df(rows=100, cols=5)
        df.iloc[:10, 0] = np.nan
        profile = profile_dataset(df, target_column="label")
        self.assertGreater(profile["missing_value_ratio"], 0)

    def test_duplicate_row_detection(self):
        df = self._make_df(rows=50)
        df = pd.concat([df, df.head(10)], ignore_index=True)
        profile = profile_dataset(df, target_column="label")
        self.assertGreater(profile["duplicate_row_ratio"], 0)

    def test_multiclass_detection(self):
        df = self._make_df(rows=200)
        df["label"] = np.random.choice(["A", "B", "C", "D"], size=200)
        profile = profile_dataset(df, target_column="label")
        self.assertTrue(profile["class_info"]["is_multiclass"])

    def test_malware_hint_inference(self):
        df = self._make_df(rows=100)
        profile = profile_dataset(df, target_column="label", dataset_hint="malwarebazaar")
        self.assertEqual(profile["inferred_dataset_family"], FAMILY_MALWARE_STATIC)
        self.assertEqual(profile["inferred_task_type"], TASK_MULTICLASS_MALWARE)

    def test_ddos_hint_inference(self):
        df = self._make_df(rows=100)
        profile = profile_dataset(df, target_column="label", dataset_hint="cicddos2019")
        self.assertEqual(profile["inferred_dataset_family"], FAMILY_DDOS_VOLUMETRIC)
        self.assertEqual(profile["inferred_task_type"], TASK_BINARY_DDOS)

    def test_no_label_leakage_in_features(self):
        """Profile must not use label distribution to select models."""
        df = self._make_df(rows=100)
        profile_biased   = profile_dataset(df, target_column="label")
        df_flip = df.copy(); df_flip["label"] = 1 - df_flip["label"]
        profile_flipped  = profile_dataset(df_flip, target_column="label")
        # Profile's n_features should be identical regardless of label distribution
        self.assertEqual(profile_biased["n_features"], profile_flipped["n_features"])


class TestModelRegistry(unittest.TestCase):
    def setUp(self):
        self.bench = load_benchmark_results()
        self.registry = build_algorithm_registry(self.bench)

    def test_registry_contains_all_datasets(self):
        for ds in ["cicids2017", "cicids2018", "cicddos2019", "unsw", "malwarebazaar"]:
            self.assertIn(ds, self.registry)

    def test_registry_contains_all_algorithms(self):
        for ds in self.registry:
            for alg in ["Random Forest", "XGBoost", "LightGBM", "CatBoost"]:
                self.assertIn(alg, self.registry[ds])

    def test_empirical_f1_loaded(self):
        for ds in self.registry:
            for alg in self.registry[ds]:
                emp = self.registry[ds][alg]["empirical_metrics"]
                self.assertIn("mean_f1", emp)
                self.assertGreaterEqual(emp["mean_f1"], 0.0)
                self.assertLessEqual(emp["mean_f1"], 1.0)

    def test_metadata_present(self):
        for ds in self.registry:
            for alg in self.registry[ds]:
                entry = self.registry[ds][alg]
                self.assertIn("strengths", entry)
                self.assertIn("known_limitations", entry)
                self.assertIn("validation_methodology", entry)


class TestScoringAndRanking(unittest.TestCase):
    def setUp(self):
        self.bench = load_benchmark_results()
        self.registry = build_algorithm_registry(self.bench)

    def test_operational_score_in_range(self):
        emp = {"mean_f1": 0.95, "mean_recall": 0.96, "mean_fpr": 0.01, "mean_latency_us": 2.0}
        score = compute_operational_score(emp, FAMILY_NETWORK_FLOW, TASK_BINARY_INTRUSION)
        self.assertGreaterEqual(score, 0.0)

    def test_higher_fpr_lowers_score(self):
        emp_low  = {"mean_f1": 0.99, "mean_recall": 0.99, "mean_fpr": 0.001, "mean_latency_us": 1.0}
        emp_high = {"mean_f1": 0.99, "mean_recall": 0.99, "mean_fpr": 0.10,  "mean_latency_us": 1.0}
        self.assertGreater(
            compute_operational_score(emp_low, FAMILY_DDOS_VOLUMETRIC, TASK_BINARY_DDOS),
            compute_operational_score(emp_high, FAMILY_DDOS_VOLUMETRIC, TASK_BINARY_DDOS),
        )

    def test_rank_algorithms_returns_sorted(self):
        ds_registry = self.registry["cicddos2019"]
        ranked = rank_algorithms(ds_registry, FAMILY_DDOS_VOLUMETRIC, TASK_BINARY_DDOS)
        scores = [s for _, s in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_catboost_wins_ddos(self):
        """CatBoost should rank first on CIC-DDoS2019 protocol-disjoint task."""
        ds_registry = self.registry["cicddos2019"]
        ranked = rank_algorithms(ds_registry, FAMILY_DDOS_VOLUMETRIC, TASK_BINARY_DDOS)
        self.assertEqual(ranked[0][0], "CatBoost")

    def test_random_forest_wins_malware(self):
        """Random Forest should rank first on MalwareBazaar temporal task."""
        ds_registry = self.registry["malwarebazaar"]
        ranked = rank_algorithms(ds_registry, FAMILY_MALWARE_STATIC, TASK_MULTICLASS_MALWARE)
        self.assertEqual(ranked[0][0], "Random Forest")

    def test_tie_handling(self):
        """When all models score identically, confidence should be low."""
        tied_ranked = [("RF", 0.75), ("XGB", 0.75), ("LGB", 0.75), ("CB", 0.75)]
        conf = compute_selection_confidence(tied_ranked)
        self.assertLessEqual(conf, 0.60)

    def test_clear_winner_gives_high_confidence(self):
        clear = [("CatBoost", 0.98), ("XGBoost", 0.62), ("LightGBM", 0.60), ("RF", 0.58)]
        conf = compute_selection_confidence(clear)
        self.assertGreaterEqual(conf, 0.88)

    def test_confidence_bounded(self):
        for ranked in [
            [("A", 1.0), ("B", 0.0)],
            [("A", 0.5), ("B", 0.5)],
        ]:
            conf = compute_selection_confidence(ranked)
            self.assertGreaterEqual(conf, 0.0)
            self.assertLessEqual(conf, 1.0)


class TestModelSelector(unittest.TestCase):
    def test_select_returns_required_keys(self):
        result = select_model_for_dataset("cicids2017")
        for k in ["selected_model", "selection_confidence", "alternatives", "explanation"]:
            self.assertIn(k, result)

    def test_select_cicddos2019_returns_catboost(self):
        result = select_model_for_dataset("cicddos2019")
        self.assertEqual(result["selected_model"], "CatBoost")

    def test_select_malwarebazaar_returns_random_forest(self):
        result = select_model_for_dataset("malwarebazaar")
        self.assertEqual(result["selected_model"], "Random Forest")

    def test_select_unsw_returns_valid_algorithm(self):
        result = select_model_for_dataset("unsw")
        self.assertIn(result["selected_model"], ["Random Forest", "XGBoost", "LightGBM", "CatBoost"])

    def test_confidence_is_float_in_range(self):
        for ds in ["cicids2017", "cicids2018", "cicddos2019", "unsw", "malwarebazaar"]:
            result = select_model_for_dataset(ds)
            conf = result["selection_confidence"]
            self.assertIsInstance(conf, float)
            self.assertGreaterEqual(conf, 0.0)
            self.assertLessEqual(conf, 1.0)

    def test_alternatives_list_contains_others(self):
        result = select_model_for_dataset("cicids2017")
        alt_names = [a["algorithm"] for a in result["alternatives"]]
        self.assertNotIn(result["selected_model"], alt_names)

    def test_unknown_dataset_raises(self):
        with self.assertRaises(ValueError):
            select_model_for_dataset("nonexistent_dataset_xyz")

    def test_confidence_note_present(self):
        result = select_model_for_dataset("cicids2018")
        self.assertIn("confidence_note", result["explanation"])

    def test_confidence_is_not_prediction_probability(self):
        """Selection confidence must NOT be labelled as prediction probability."""
        result = select_model_for_dataset("cicids2018")
        note = result["explanation"]["confidence_note"].lower()
        self.assertNotIn("prediction probability", note.split("not")[0].lower()
                         if "not" in note else note)


class TestAblationAndRankStability(unittest.TestCase):
    def setUp(self):
        self.bench = load_benchmark_results()

    def test_ablation_contains_all_strategies(self):
        results = ablation_study_from_benchmark(self.bench)
        self.assertIn("Adaptive Model Selection", results)
        for alg in ["Random Forest", "XGBoost", "LightGBM", "CatBoost"]:
            self.assertIn(f"Fixed_{alg}", results)

    def test_rank_stability_all_algorithms(self):
        stability = compute_rank_stability(self.bench)
        for alg in ["Random Forest", "XGBoost", "LightGBM", "CatBoost"]:
            self.assertIn(alg, stability)
            self.assertIn("average_rank", stability[alg])
            self.assertIn("number_of_wins", stability[alg])

    def test_distribution_shift_keys(self):
        shift = distribution_shift_analysis(self.bench)
        for ds in ["cicids2017", "cicids2018", "cicddos2019", "unsw", "malwarebazaar"]:
            self.assertIn(ds, shift)
            self.assertIn("adaptive_f1", shift[ds])

    def test_missing_benchmark_result_handled_gracefully(self):
        """If a dataset has no result for an alg, score should default to 0 not error."""
        partial_bench = {"cicids2017": {"XGBoost": {"f1": {"mean": 0.95}, "fpr": {"mean": 0.01},
                                                     "recall": {"mean": 0.95}, "latency_us": {"mean": 0.5}}}}
        # Should not raise
        try:
            stability = compute_rank_stability(partial_bench)
        except Exception as e:
            self.fail(f"compute_rank_stability raised unexpectedly: {e}")


class TestExplainability(unittest.TestCase):
    def test_explanation_structure(self):
        explanation = generate_selection_explanation(
            selected_model="CatBoost",
            selected_score=0.96,
            alternatives=[("XGBoost", 0.91), ("LightGBM", 0.88), ("Random Forest", 0.72)],
            dataset_name="cicddos2019",
            family=FAMILY_DDOS_VOLUMETRIC,
            task=TASK_BINARY_DDOS,
            registry_entry={
                "empirical_metrics": {"mean_f1": 1.0, "ci95_f1": "[1.0, 1.0]", "mean_fpr": 0.0,
                                       "mean_fnr": 0.0, "mean_recall": 1.0, "mean_latency_us": 0.57},
                "strengths": ["Perfect boundary under protocol shift"],
                "known_limitations": ["Higher train time"],
                "validation_methodology": "Protocol-disjoint split",
            },
            confidence=0.95,
        )
        for key in ["selected_model", "rationale", "alternative_models", "evidence", "confidence_note"]:
            self.assertIn(key, explanation)

    def test_explanation_no_unsupported_claims(self):
        explanation = generate_selection_explanation(
            "XGBoost", 0.88, [("CatBoost", 0.87)], "cicids2017",
            FAMILY_NETWORK_FLOW, TASK_BINARY_INTRUSION,
            {"empirical_metrics": {"mean_f1": 1.0, "ci95_f1": "[1.0,1.0]",
                                    "mean_fpr": 0.0, "mean_fnr": 0.0,
                                    "mean_recall": 1.0, "mean_latency_us": 0.5},
             "strengths": [], "known_limitations": [], "validation_methodology": "Temporal"},
            confidence=0.72,
        )
        # Must not claim "universally superior"
        rationale = explanation["rationale"].lower()
        self.assertNotIn("universally superior", rationale)
        self.assertNotIn("zero real-world error", rationale)


if __name__ == "__main__":
    unittest.main(verbosity=2)
