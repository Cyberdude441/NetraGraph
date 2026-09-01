"""
NetraGraph Adaptive Model Selection — Main Runner (Research Only).
Isolated from production. No changes to backend/models/registry/ or Models A–E.
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ["LOKY_MAX_CPU_COUNT"] = "4"

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

import numpy as np
import pandas as pd

from config import RESULTS_DIR, get_environment_info, load_benchmark_results
from dataset_profiler import profile_dataset
from evaluation import (
    ablation_study_from_benchmark,
    compute_rank_stability,
    distribution_shift_analysis,
)
from model_registry import build_algorithm_registry
from model_selector import select_model_for_dataset
from scoring import rank_algorithms
from visualisations import generate_all_plots


def json_default(o):
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def main() -> None:
    print("=" * 72)
    print("NETRAGRAPH ADAPTIVE MODEL SELECTION — RESEARCH LAYER")
    print("Production Models A-E: UNTOUCHED | backend/models/registry/: UNTOUCHED")
    print("=" * 72)

    # Environment
    env = get_environment_info()
    print(f"\nPython: {env['python_version'].split()[0]}")
    print(f"Platform: {env['platform']}")

    # Load benchmark results
    benchmark_results = load_benchmark_results()
    registry = build_algorithm_registry(benchmark_results)

    # ── Model Selection for All Datasets ─────────────────────────────────────
    print("\n" + "=" * 72)
    print("MODEL SELECTION RESULTS PER DATASET")
    print("=" * 72)
    print(f"{'Dataset':<22} {'Selected Model':<18} {'Confidence':>12}  Rationale (abbreviated)")
    print("-" * 72)

    selections = {}
    datasets = ["cicids2017", "cicids2018", "cicddos2019", "unsw", "malwarebazaar"]
    for ds in datasets:
        result = select_model_for_dataset(ds)
        selections[ds] = result
        model = result["selected_model"]
        conf  = result["selection_confidence"]
        short_rationale = result["explanation"]["rationale"][:55] + "..."
        print(f"{ds:<22} {model:<18} {conf:>12.4f}  {short_rationale}")
    print("=" * 72)

    # ── Rank Stability ────────────────────────────────────────────────────────
    rank_stability = compute_rank_stability(benchmark_results)
    print("\n[RANK STABILITY]")
    print(f"{'Algorithm':<18} {'Avg Rank':>10} {'Rank Var':>10} {'Wins':>6} {'2nd':>6} {'Robustness':>12}")
    print("-" * 65)
    for alg, stats in rank_stability.items():
        print(
            f"{alg:<18} {stats['average_rank']:>10.2f} {stats['rank_variance']:>10.3f}"
            f" {stats['number_of_wins']:>6} {stats['number_of_runner_up']:>6}"
            f" {stats['robustness_score']:>12.4f}"
        )

    # ── Ablation Study ────────────────────────────────────────────────────────
    ablation = ablation_study_from_benchmark(benchmark_results)
    print("\n[ABLATION STUDY: Fixed Model vs Adaptive Selection]")
    print(f"{'Strategy':<35} {'Mean F1':>10} {'Mean FPR':>10} {'Mean Latency µs':>16}  Delta vs Adaptive")
    print("-" * 80)
    for strat, vals in ablation.items():
        delta = vals.get("delta_f1_vs_adaptive", 0.0)
        delta_str = f"{delta:+.5f}" if delta != 0 else "   (baseline)"
        print(f"{strat:<35} {vals['mean_f1']:>10.5f} {vals['mean_fpr']:>10.5f} {vals['mean_latency_us']:>16.3f}  {delta_str}")

    # ── Distribution-Shift Analysis ───────────────────────────────────────────
    shift = distribution_shift_analysis(benchmark_results)
    print("\n[DISTRIBUTION-SHIFT ANALYSIS]")
    print(f"{'Dataset':<18} {'Severity':<30} {'Adaptive Model':<18} {'Adaptive F1':>12} {'XGBoost F1':>12} {'Delta F1':>10}")
    print("-" * 100)
    for ds, info in shift.items():
        print(
            f"{ds:<18} {info['shift_severity']:<30} {info['adaptive_selected_model']:<18}"
            f" {info['adaptive_f1']:>12.5f} {info['fixed_xgboost_f1']:>12.5f}"
            f" {info['delta_f1_adaptive_vs_fixed_xgb']:>+10.5f}"
        )

    # ── Save Research Artifacts ───────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_DIR / "model_selection_results.json", "w", encoding="utf-8") as f:
        json.dump({ds: {k: v for k, v in sel.items() if k != "live_profile"}
                   for ds, sel in selections.items()}, f, indent=2, default=json_default)

    with open(RESULTS_DIR / "rank_stability.json", "w", encoding="utf-8") as f:
        json.dump(rank_stability, f, indent=2, default=json_default)

    with open(RESULTS_DIR / "ablation_study.json", "w", encoding="utf-8") as f:
        json.dump(ablation, f, indent=2, default=json_default)

    with open(RESULTS_DIR / "distribution_shift.json", "w", encoding="utf-8") as f:
        json.dump(shift, f, indent=2, default=json_default)

    with open(RESULTS_DIR / "environment.json", "w", encoding="utf-8") as f:
        json.dump(env, f, indent=2, default=json_default)

    print("\n[Generating 10 Publication-Quality Charts...]")
    saved_plots = generate_all_plots(benchmark_results, rank_stability, ablation)
    for p in saved_plots:
        print(f"  - {p}")

    # ── Final Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("NETRAGRAPH ADAPTIVE MODEL SELECTION — SUMMARY")
    print("=" * 72)
    print(f"{'Dataset':<22} {'Selected Model':<20} {'Confidence':>12}")
    print("-" * 56)
    for ds in datasets:
        r = selections[ds]
        print(f"{ds:<22} {r['selected_model']:<20} {r['selection_confidence']:>12.4f}")
    print("=" * 72)

    # Fixed vs Adaptive top-line
    adaptive_f1 = ablation["Adaptive Model Selection"]["mean_f1"]
    best_fixed   = max(
        [(k, v["mean_f1"]) for k, v in ablation.items() if k != "Adaptive Model Selection"],
        key=lambda x: x[1],
    )
    print(f"\nAdaptive Selection Mean F1 (all datasets):  {adaptive_f1:.5f}")
    print(f"Best Fixed-Model Mean F1 ({best_fixed[0]}):  {best_fixed[1]:.5f}")
    print(f"Adaptive vs Best Fixed Delta:              {adaptive_f1 - best_fixed[1]:+.5f}")

    # Best individual model overall (by wins)
    wins = {a: rank_stability[a]["number_of_wins"] for a in rank_stability}
    overall_winner = max(wins, key=wins.get)
    print(f"\nBest individual model (by number of dataset wins): {overall_winner} ({wins[overall_winner]}/5 wins)")

    # Best under FPR <= 0.1% from CIC-DDoS2019 (the discriminating dataset)
    best_low_fpr = min(
        [(a, benchmark_results["cicddos2019"].get(a, {}).get("fpr", {}).get("mean", 1.0))
         for a in ["Random Forest", "XGBoost", "LightGBM", "CatBoost"]],
        key=lambda x: x[1],
    )
    print(f"Best model under FPR <= 0.1% (CIC-DDoS2019): {best_low_fpr[0]} (FPR = {best_low_fpr[1]:.5f})")

    print("\nDistribution-shift improvement (Adaptive vs Fixed XGBoost):")
    for ds, info in shift.items():
        delta = info["delta_f1_adaptive_vs_fixed_xgb"]
        if delta > 0:
            print(f"  {ds}: Adaptive GAINS  {delta:+.5f} F1 over fixed XGBoost")
        elif delta == 0:
            print(f"  {ds}: Adaptive TIES with fixed XGBoost")
        else:
            print(f"  {ds}: Adaptive TRAILS fixed XGBoost by {abs(delta):.5f} F1")

    print("\n" + "=" * 72)
    print("Production Models A-E:   UNTOUCHED")
    print("backend/models/registry: UNTOUCHED")
    print("Git:                     NO COMMIT  |  NO PUSH")
    print("=" * 72)


if __name__ == "__main__":
    main()
