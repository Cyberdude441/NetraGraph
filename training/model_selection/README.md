# NetraGraph — Adaptive Model Selection Research Layer

## Overview

This directory contains the **research-only** adaptive model-selection and ensemble decision layer for the NetraGraph cybersecurity intelligence platform. It is **completely isolated** from the production backend.

> **IMPORTANT ISOLATION BOUNDARIES**
> - This module does NOT modify `backend/models/registry/` or production Models A–E.
> - It does NOT alter any existing API behaviour.
> - It does NOT delete or overwrite previous benchmark results under `training/benchmark/`.
> - It must NOT be called from production API routes.

---

## Directory Structure

```
training/model_selection/
├── config.py                  ← Paths, seeds, ranking weights, benchmark loader
├── model_registry.py          ← Research model registry (empirical + metadata)
├── dataset_profiler.py        ← Label-leakage-free structural dataset profiler
├── scoring.py                 ← Composite operational scoring and confidence engine
├── model_selector.py          ← select_model_for_dataset() / predict_with_selected_model()
├── ensemble.py                ← Hard voting / Soft voting / Weighted soft voting
├── calibration.py             ← Platt scaling / Isotonic regression / ECE
├── evaluation.py              ← Rank stability, ablation study, distribution-shift, threshold optimisation
├── explainability.py          ← Evidence-grounded structured explanations
├── visualisations.py          ← 10 publication-quality matplotlib charts
├── run_model_selection.py     ← Main runner (produces all results + plots)
├── tests/
│   └── test_model_selection.py ← 36 unit tests (all passing)
├── results/
│   ├── model_selection_results.json
│   ├── rank_stability.json
│   ├── ablation_study.json
│   ├── distribution_shift.json
│   ├── environment.json
│   └── plots/                 ← 10 publication-quality PNG charts
└── README.md                  ← This file
```

---

## Research Interfaces

### select_model_for_dataset()

```python
from model_selector import select_model_for_dataset

result = select_model_for_dataset("cicddos2019")

# Returns:
# {
#   "selected_model":       "CatBoost",          # Empirically best for this dataset
#   "operational_score":    0.59203,             # Composite score
#   "selection_confidence": 0.5580,              # Evidence strength (NOT prediction probability)
#   "alternatives":         [...],               # Ranked other algorithms
#   "explanation":          {...},               # Structured evidence-grounded rationale
# }
```

**IMPORTANT**: `selection_confidence` is the strength of evidence favouring this model for the task. It is **NOT** a probability that the model's prediction is correct.

### predict_with_selected_model()

```python
from model_selector import predict_with_selected_model

result = predict_with_selected_model("cicddos2019", X_train, y_train)
# Selects best model per evidence, trains on X/y, returns metrics.
# Does NOT affect production Models A–E.
```

---

## Model Selection Results (Empirical)

| Dataset | Selected Model | Confidence | Validation Method |
|---|---|---|---|
| CIC-IDS2017 | **XGBoost** | 0.6067 | Temporal day-based 3-fold |
| CSE-CIC-IDS2018 | **XGBoost** | 0.5717 | Temporal multi-day 3-fold |
| CIC-DDoS2019 | **CatBoost** | 0.5580 | Protocol-disjoint 3-fold |
| UNSW-NB15 | **XGBoost** | 0.6333 | Official partition 3-fold |
| MalwareBazaar | **Random Forest** | 0.7494 | Temporal submission-window 3-fold |

### Key Finding
CatBoost is selected for CIC-DDoS2019 **specifically** because it achieves **FPR = 0.0000** under unseen reflection attack protocols — a critical operational property for avoiding false-positive traffic blocks. XGBoost achieves near-perfect F1 (0.9997) but incurs FPR = 0.062%.

Random Forest is selected for MalwareBazaar because it achieves the **highest Macro F1 (0.1882)** under temporal concept drift across September–October submission windows. The task is VERY HARD — all four algorithms perform near-random, with the best model achieving only ~19% Macro F1.

---

## Ablation Study Summary

| Strategy | Mean F1 | Mean FPR | Delta vs Adaptive |
|---|---|---|---|
| **Adaptive Selection** | **0.83763** | 0.03998 | (baseline) |
| Fixed Random Forest | 0.83714 | 0.04095 | −0.00049 |
| Fixed XGBoost | 0.83372 | 0.04005 | −0.00391 |
| Fixed LightGBM | 0.83240 | 0.04505 | −0.00523 |
| Fixed CatBoost | 0.82717 | 0.03997 | −0.01046 |

Adaptive selection consistently matches or exceeds any single fixed model. The largest gains are on dataset-specific tasks (malware: +1.92% over fixed XGBoost, DDoS: +0.03% over fixed XGBoost with zero FPR).

---

## Statistical Validity Note

> Results are based on N=3 folds per dataset. With N=3, paired Wilcoxon signed-rank tests have a mathematical minimum p-value of 0.25. All comparisons should be described as **empirical observational margins**, not statistically significant asymptotic claims.

---

## Running the Research Layer

```powershell
# From the project root:
& .\.venv-ml\Scripts\python.exe training/model_selection/run_model_selection.py
```

### Running Unit Tests

```powershell
& .\.venv-ml\Scripts\python.exe -m pytest training/model_selection/tests/test_model_selection.py -v
```

Expected: **36/36 PASSED**

---

## Visualisations Generated

| # | Chart | Description |
|---|---|---|
| 1 | `01_model_ranking_across_datasets.png` | Grouped bar: algorithm F1 across all 5 datasets |
| 2 | `02_performance_heatmap.png` | F1 heatmap (algorithms × datasets) |
| 3 | `03_f1_vs_fpr.png` | Security operating point scatter (F1 vs FPR%) |
| 4 | `04_f1_vs_latency.png` | Quality vs real-time latency scatter |
| 5 | `05_rank_stability.png` | Cross-dataset robustness scores |
| 6 | `06_fixed_vs_adaptive.png` | Fixed model vs adaptive selection ablation |
| 7 | `07_ensemble_vs_individual.png` | Ensemble modes vs best individual |
| 8 | `08_calibration_curves.png` | Reliability diagram (Platt / Isotonic) |
| 9 | `09_threshold_fpr_tradeoff.png` | F1 vs decision threshold sweep |
| 10 | `10_distribution_shift_degradation.png` | Performance under shift severity |

---

## Safety Guarantees

- ✅ Production Models A–E: **UNTOUCHED**
- ✅ `backend/models/registry/`: **UNTOUCHED**
- ✅ Existing benchmark results: **PRESERVED**
- ✅ No raw datasets committed
- ✅ No large model artifacts committed
- ✅ All experiments isolated under `training/model_selection/`
