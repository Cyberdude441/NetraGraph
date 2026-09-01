"""
Publication-Quality (300 DPI) Visualisation Engine for Blind Holdout Validation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PLOTS_DIR = Path(__file__).resolve().parent / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_10_blind_validation_plots(
    seed_results: List[Dict[str, Any]],
    dataset_results: List[Dict[str, Any]],
    model_results: List[Dict[str, Any]],
    confusion_matrices: Dict[str, Any],
    calibration_data: Dict[str, Any],
    threshold_data: List[Dict[str, Any]],
    latency_data: Dict[str, Any],
) -> List[str]:
    saved: List[str] = []

    # 1. 01_f1_comparison.png (Multi-Seed F1 Comparison)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    seeds = [f"Seed {s['seed']}" for s in seed_results]
    p_f1 = [s["production_metrics"]["f1"] for s in seed_results]
    a_f1 = [s["adaptive_metrics"]["f1"] for s in seed_results]
    x = np.arange(len(seeds))
    w = 0.35
    ax.bar(x - w/2, p_f1, w, label="Production Model F1", color="#1f77b4", edgecolor="k")
    ax.bar(x + w/2, a_f1, w, label="Adaptive Model F1", color="#2ca02c", edgecolor="k")
    ax.set_xticks(x); ax.set_xticklabels(seeds, fontweight="bold")
    ax.set_ylabel("F1 Score", fontweight="bold")
    ax.set_title("Multi-Seed Blind Holdout F1 Performance Comparison", fontweight="bold")
    ax.set_ylim(0, 1.15); ax.grid(axis="y", linestyle="--", alpha=0.4); ax.legend()
    for i in range(len(seeds)):
        ax.text(x[i] - w/2, p_f1[i] + 0.02, f"{p_f1[i]:.3f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
        ax.text(x[i] + w/2, a_f1[i] + 0.02, f"{a_f1[i]:.3f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
    plt.tight_layout()
    p = PLOTS_DIR / "01_f1_comparison.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 2. 02_fpr_comparison.png (FPR across Seeds)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    p_fpr = [s["production_metrics"]["fpr"] * 100 for s in seed_results]
    a_fpr = [s["adaptive_metrics"]["fpr"] * 100 for s in seed_results]
    ax.bar(x - w/2, p_fpr, w, label="Production FPR (%)", color="#d9534f", edgecolor="k")
    ax.bar(x + w/2, a_fpr, w, label="Adaptive FPR (%)", color="#5cb85c", edgecolor="k")
    ax.set_xticks(x); ax.set_xticklabels(seeds, fontweight="bold")
    ax.set_ylabel("False Positive Rate (%)", fontweight="bold")
    ax.set_title("Multi-Seed False Positive Rate (FPR) Comparison", fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4); ax.legend()
    plt.tight_layout()
    p = PLOTS_DIR / "02_fpr_comparison.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 3. 03_fnr_comparison.png (FNR across Seeds)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    p_fnr = [s["production_metrics"]["fnr"] * 100 for s in seed_results]
    a_fnr = [s["adaptive_metrics"]["fnr"] * 100 for s in seed_results]
    ax.bar(x - w/2, p_fnr, w, label="Production FNR (%)", color="#f0ad4e", edgecolor="k")
    ax.bar(x + w/2, a_fnr, w, label="Adaptive FNR (%)", color="#5bc0de", edgecolor="k")
    ax.set_xticks(x); ax.set_xticklabels(seeds, fontweight="bold")
    ax.set_ylabel("False Negative Rate (%)", fontweight="bold")
    ax.set_title("Multi-Seed False Negative Rate (FNR) Comparison", fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4); ax.legend()
    plt.tight_layout()
    p = PLOTS_DIR / "03_fnr_comparison.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 4. 04_confusion_matrices.png
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=300)
    cm_p = np.array([[confusion_matrices["production"]["TN"], confusion_matrices["production"]["FP"]],
                     [confusion_matrices["production"]["FN"], confusion_matrices["production"]["TP"]]])
    cm_a = np.array([[confusion_matrices["adaptive"]["TN"], confusion_matrices["adaptive"]["FP"]],
                     [confusion_matrices["adaptive"]["FN"], confusion_matrices["adaptive"]["TP"]]])
    im1 = ax1.imshow(cm_p, cmap="Blues")
    ax1.set_title("Production Confusion Matrix (Total Holdout)", fontweight="bold")
    ax1.set_xticks([0, 1]); ax1.set_xticklabels(["Pred 0", "Pred 1"])
    ax1.set_yticks([0, 1]); ax1.set_yticklabels(["True 0", "True 1"])
    for i in range(2):
        for j in range(2):
            ax1.text(j, i, f"{cm_p[i,j]}", ha="center", va="center", color="white" if cm_p[i,j] > cm_p.max()/2 else "black", fontweight="bold")
    im2 = ax2.imshow(cm_a, cmap="Greens")
    ax2.set_title("Adaptive Confusion Matrix (Total Holdout)", fontweight="bold")
    ax2.set_xticks([0, 1]); ax2.set_xticklabels(["Pred 0", "Pred 1"])
    ax2.set_yticks([0, 1]); ax2.set_yticklabels(["True 0", "True 1"])
    for i in range(2):
        for j in range(2):
            ax2.text(j, i, f"{cm_a[i,j]}", ha="center", va="center", color="white" if cm_a[i,j] > cm_a.max()/2 else "black", fontweight="bold")
    plt.tight_layout()
    p = PLOTS_DIR / "04_confusion_matrices.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 5. 05_dataset_f1_delta.png
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    ds_names = [d["dataset"].upper() for d in dataset_results]
    f1_d = [d["f1_delta"] for d in dataset_results]
    cols = ["#2ca02c" if v >= 0 else "#d62728" for v in f1_d]
    bars = ax.bar(ds_names, f1_d, color=cols, edgecolor="k", width=0.5)
    ax.axhline(0, color="k", linewidth=0.8)
    ax.set_ylabel("F1 Delta (Adaptive − Production)", fontweight="bold")
    ax.set_title("Per-Dataset F1 Performance Delta on Blind Holdout", fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars, f1_d):
        offset = 0.005 if val >= 0 else -0.015
        ax.text(bar.get_x() + bar.get_width()/2, val + offset, f"{val:+.4f}", ha="center", va="bottom" if val >= 0 else "top", fontsize=9, fontweight="bold")
    plt.tight_layout()
    p = PLOTS_DIR / "05_dataset_f1_delta.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 6. 06_dataset_fpr_delta.png
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    fpr_d = [d["fpr_delta"] * 100 for d in dataset_results]
    cols = ["#2ca02c" if v <= 0 else "#d62728" for v in fpr_d]
    bars = ax.bar(ds_names, fpr_d, color=cols, edgecolor="k", width=0.5)
    ax.axhline(0, color="k", linewidth=0.8)
    ax.set_ylabel("FPR Delta (%) (Lower is Better)", fontweight="bold")
    ax.set_title("Per-Dataset False Positive Rate Delta on Blind Holdout", fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars, fpr_d):
        offset = 0.005 if val >= 0 else -0.015
        ax.text(bar.get_x() + bar.get_width()/2, val + offset, f"{val:+.4f}%", ha="center", va="bottom" if val >= 0 else "top", fontsize=9, fontweight="bold")
    plt.tight_layout()
    p = PLOTS_DIR / "06_dataset_fpr_delta.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 7. 07_model_selection.png
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    m_names = [m["algorithm"] for m in model_results]
    m_pcts = [m["selection_pct"] for m in model_results]
    bars = ax.bar(m_names, m_pcts, color=["#d95f02", "#1b9e77", "#2b5c8f", "#7570b3"][:len(m_names)], edgecolor="k", width=0.5)
    ax.set_ylabel("Selection Percentage (%)", fontweight="bold")
    ax.set_title("Adaptive Model Selection Frequency on Blind Holdout", fontweight="bold")
    ax.set_ylim(0, 100); ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars, m_pcts):
        ax.text(bar.get_x() + bar.get_width()/2, val + 2, f"{val:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
    plt.tight_layout()
    p = PLOTS_DIR / "07_model_selection.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 8. 08_calibration.png (Reliability Diagrams)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
    rc_p = calibration_data["production"]["reliability_curve"]
    rc_a = calibration_data["adaptive"]["reliability_curve"]
    ax.plot(rc_p["prob_pred"], rc_p["prob_true"], "s-", color="#1f77b4", label=f"Production (ECE={calibration_data['production']['ece']:.3f})")
    ax.plot(rc_a["prob_pred"], rc_a["prob_true"], "o-", color="#2ca02c", label=f"Adaptive (ECE={calibration_data['adaptive']['ece']:.3f})")
    ax.set_xlabel("Mean Predicted Probability", fontweight="bold")
    ax.set_ylabel("Fraction of Positives", fontweight="bold")
    ax.set_title("Reliability Calibration Curves (Blind Holdout)", fontweight="bold")
    ax.grid(linestyle="--", alpha=0.4); ax.legend()
    plt.tight_layout()
    p = PLOTS_DIR / "08_calibration.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 9. 09_threshold_robustness.png
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    t_vals = [t["threshold"] for t in threshold_data]
    p_f1s = [t["production_f1"] for t in threshold_data]
    a_f1s = [t["adaptive_f1"] for t in threshold_data]
    ax.plot(t_vals, p_f1s, "s-", color="#1f77b4", label="Production F1 across Thresholds", linewidth=2)
    ax.plot(t_vals, a_f1s, "o-", color="#2ca02c", label="Adaptive F1 across Thresholds", linewidth=2)
    ax.set_xlabel("Decision Threshold", fontweight="bold")
    ax.set_ylabel("F1 Score", fontweight="bold")
    ax.set_title("Threshold Robustness: F1 Score from 0.10 to 0.90", fontweight="bold")
    ax.grid(linestyle="--", alpha=0.4); ax.legend()
    plt.tight_layout()
    p = PLOTS_DIR / "09_threshold_robustness.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    # 10. 10_latency_distribution.png
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    stages = [
        "1. Prod Preproc", "2. Prod Infer", "3. Adapt Profile", "4. Adapt Select",
        "5. Adapt Preproc", "6. Adapt Infer", "7. Prod Total", "8. Adapt Total"
    ]
    st_keys = list(latency_data["stages"].keys())
    lat_means = [latency_data["stages"][k]["mean"] for k in st_keys]
    bars = ax.bar(stages, lat_means, color=["#4682b4", "#5bc0de", "#f0ad4e", "#d95f02", "#4682b4", "#5cb85c", "#1f77b4", "#2ca02c"], edgecolor="k")
    ax.set_ylabel("Latency (ms)", fontweight="bold")
    ax.set_title("8-Stage Latency Measurement Breakdown (CPU, 1,000 Iterations)", fontweight="bold")
    ax.set_xticks(range(len(stages)))
    ax.set_xticklabels(stages, rotation=25, ha="right", fontsize=8, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars, lat_means):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.5, f"{val:.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
    plt.tight_layout()
    p = PLOTS_DIR / "10_latency_distribution.png"
    plt.savefig(p); plt.close(); saved.append(str(p))

    return saved
