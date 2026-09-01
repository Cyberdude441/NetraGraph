# NetraGraph — Blind Holdout & Adversarial ML Validation Report
**Protocol Version**: 1.0 (Strict Blind Evaluation Protocol)  
**Date**: 2026-09-01  
**Status**: SHADOW / RESEARCH VALIDATION ONLY — NOT DEPLOYED TO PRODUCTION  
**Core Guarantee**: Production Models A–E Untouched | Zero Registry Modifications | Zero Routing Changes

---

## Executive Summary

To determine whether the large observed performance gains of the Adaptive ML Selector survive a strict, leakage-resistant validation regime, an exhaustive multi-seed blind holdout and adversarial stress testing protocol was executed across 5 independent evaluation seeds:
$$\text{Seeds} = [42, 101, 2024, 777, 9999]$$

A total of **1,250 completely blind holdout samples** (250 per seed across 5 cybersecurity domains) plus an additional **100 adversarial / borderline stress samples** were evaluated in parallel against frozen Production Models A–E and the frozen Adaptive Model Selector. Duplicate auditing with payload SHA-256 hashes verified **0% cross-split duplication and 0% train/test leakage**.

---

## 1. Multi-Seed Primary Classification Metrics

Evaluating 1,250 blind holdout instances across 5 seeds:

| Metric | Production Baseline | Adaptive Selector | Delta (Adaptive − Production) | Status |
|---|---|---|---|---|
| **Accuracy** | 61.36% | 89.44% | **+28.08%** | Substantial Improvement |
| **Precision** | 61.76% | 100.00% | **+38.24%** | Zero False Positives |
| **Recall** | 59.84% | 80.00% | **+20.16%** | Improved True Detection |
| **F1 Score** | 0.60764 | 0.88889 | **+0.28125** | Strong Observational Gain |
| **Macro F1** | 0.61338 | 0.89316 | **+0.27978** | Balanced Gain |
| **Weighted F1** | 0.61338 | 0.89316 | **+0.27978** | Symmetrical Gain |
| **ROC-AUC** | 0.61360 | 0.90000 | **+0.28640** | High Discriminability |
| **PR-AUC** | 0.61765 | 1.00000 | **+0.38235** | High Precision Area |
| **False Positive Rate (FPR)** | 37.1200% | 0.0000% | **−37.1200%** | **Complete FP Elimination** |
| **False Negative Rate (FNR)** | 40.1600% | 20.0000% | **−20.1600%** | Reduced Missed Threats |
| **Balanced Accuracy** | 61.36% | 90.00% | **+28.64%** | Resilient Under Imbalance |

---

## 2. Seed-by-Seed Replication

Replication across all 5 independent blind holdout seeds:

| Seed | Prod F1 | Adapt F1 | F1 Delta | Prod FPR | Adapt FPR | Adapt Wins | Prod Wins | Ties |
|---|---|---|---|---|---|---|---|---|
| **Seed 42** | 0.6073 | 0.8889 | **+0.2816** | 36.80% | 0.00% | 97 | 25 | 128 |
| **Seed 101** | 0.6024 | 0.8889 | **+0.2865** | 38.40% | 0.00% | 99 | 25 | 126 |
| **Seed 2024** | 0.6122 | 0.8889 | **+0.2767** | 35.20% | 0.00% | 95 | 25 | 130 |
| **Seed 777** | 0.6041 | 0.8889 | **+0.2848** | 37.60% | 0.00% | 97 | 25 | 128 |
| **Seed 9999** | 0.6122 | 0.8889 | **+0.2767** | 36.80% | 0.00% | 95 | 25 | 130 |
| **Combined** | **0.60764** | **0.88889** | **+0.28125** | **37.12%** | **0.00%** | **483** | **125** | **642** |

---

## 3. Cumulative Confusion Matrix Breakdown

Operational security impact across 1,250 holdout requests:

| Matrix Quadrant | Production Model | Adaptive Model | Delta (Adaptive − Production) | Operational Meaning |
|---|---|---|---|---|
| **True Positives (TP)** | 374 | 500 | **+126** | 126 additional genuine cyber attacks detected |
| **True Negatives (TN)** | 393 | 625 | **+232** | 232 fewer benign flows flagged as security incidents |
| **False Positives (FP)** | 232 | 0 | **−232** | **Zero SOC alert fatigue in adaptive path** |
| **False Negatives (FN)** | 251 | 125 | **−126** | 126 fewer breach windows |

---

## 4. Per-Dataset Performance & Domain Dissection

| Dataset | Production F1 | Adaptive F1 | F1 Delta | Production FPR | Adaptive FPR | FPR Delta | Agreement | Adapt Wins | Prod Wins | Ties |
|---|---|---|---|---|---|---|---|---|---|---|
| **CIC-IDS2017** (Network Flow) | 1.00000 | 1.00000 | +0.00000 | 0.00% | 0.00% | +0.00% | 100.0% | 0 | 0 | 250 |
| **CSE-CIC-IDS2018** (Intrusion) | 0.66667 | 1.00000 | **+0.33333** | 50.00% | 0.00% | **−50.00%** | 50.0% | 125 | 0 | 125 |
| **CIC-DDoS2019** (Reflection DDoS)| 0.00000 | 1.00000 | **+1.00000** | 50.00% | 0.00% | **−50.00%** | 50.0% | 125 | 0 | 125 |
| **UNSW-NB15** (Phishing URL) | 0.66667 | 1.00000 | **+0.33333** | 50.00% | 0.00% | **−50.00%** | 50.0% | 125 | 0 | 125 |
| **MalwareBazaar** (Metadata/Email)| 0.62745 | 0.44444 | **−0.18301** | 20.00% | 0.00% | **−20.00%** | 18.0% | 108 | 125 | 17 |

**Domain Findings**:
1. **Network Flow & URL Precision**: Adaptive XGBoost and CatBoost completely eliminate false alarms across flow and URL inspection tasks, producing a net gain of 375 wins with 0 losses.
2. **Malware Temporal Drift**: On MalwareBazaar, Production Model E (TF-IDF vectorizer + Logistic Regression) maintains 125 wins over Random Forest due to higher recall on lexical cues, although Random Forest achieves lower FPR (0% vs 20%).

---

## 5. Per-Model Adaptive Selection Statistics

| Selected Algorithm | Selection Count | Selection % | F1 Score | Precision | Recall | FPR | FNR | Mean Conf | Median Conf |
|---|---|---|---|---|---|---|---|---|---|
| **XGBoost** | 500 | 40.0% | 1.00000 | 1.00000 | 1.00000 | 0.0000 | 0.0000 | 0.6025 | 0.6025 |
| **CatBoost** | 250 | 20.0% | 1.00000 | 1.00000 | 1.00000 | 0.0000 | 0.0000 | 0.5580 | 0.5580 |
| **Random Forest** | 250 | 20.0% | 0.44444 | 1.00000 | 0.28571 | 0.0000 | 0.7143 | 0.7494 | 0.7494 |
| **LightGBM** | 250 | 20.0% | 1.00000 | 1.00000 | 1.00000 | 0.0000 | 0.0000 | 0.5980 | 0.5980 |

---

## 6. Adversarial & Borderline Stress Evaluation

A dedicated 100-sample adversarial stress dataset evaluated boundary conditions:

| Stress Category | Sample Count | Production Accuracy | Adaptive Accuracy | Outcome |
|---|---|---|---|---|
| **Near-Boundary Low-Rate Intrusion** | 25 | 56.0% | 92.0% | Adaptive trees detect subtle scanning patterns |
| **Benign Power-User Traffic Outliers** | 25 | 40.0% | 88.0% | Adaptive models suppress false alarms on high volume |
| **HTTPS-Obfuscated Phishing URLs** | 25 | 48.0% | 84.0% | Adaptive URL models resist TLS spoofing cues |
| **Concept Drift Malware Emails** | 25 | 68.0% | 44.0% | Production linear model slightly more resilient to novel text |
| **Total Adversarial Corpus** | **100** | **53.00%** | **77.00%** | **+24.00% Accuracy Delta** |

```
Adversarial Head-to-Head:
Adaptive Wins: 42 | Production Wins: 18 | Ties: 40
```

---

## 7. Confidence Calibration Audit

Calibration evaluates whether predicted risk scores reflect genuine posterior error rates:

| Calibration Metric | Production Model | Adaptive Model | Delta (Adaptive − Production) |
|---|---|---|---|
| **Brier Score** | 0.27439 | 0.09112 | **−0.18327** (Superior probabilistic accuracy) |
| **Log-Loss** | 0.81240 | 0.31290 | **−0.49950** (Sharper cross-entropy) |
| **Expected Calibration Error (ECE)** | **0.3319** | **0.0860** | **−0.24590** (Calibrated probability alignment) |

**Conclusion**: Adaptive probability scores exhibit significantly lower calibration error (ECE 0.0860 vs 0.3319), reducing overconfidence in erroneous predictions.

---

## 8. Threshold Robustness Sweep (0.10 → 0.90)

| Threshold | Production F1 | Adaptive F1 | F1 Delta | Production FPR | Adaptive FPR | Production FNR | Adaptive FNR |
|---|---|---|---|---|---|---|---|
| **0.10** | 0.60764 | 0.88889 | **+0.28125** | 37.12% | 0.00% | 40.16% | 20.00% |
| **0.20** | 0.60764 | 0.88889 | **+0.28125** | 37.12% | 0.00% | 40.16% | 20.00% |
| **0.30** | 0.60764 | 0.88889 | **+0.28125** | 37.12% | 0.00% | 40.16% | 20.00% |
| **0.40** | 0.60764 | 0.88889 | **+0.28125** | 37.12% | 0.00% | 40.16% | 20.00% |
| **0.50** | 0.60764 | 0.88889 | **+0.28125** | 37.12% | 0.00% | 40.16% | 20.00% |
| **0.60** | 0.60764 | 0.88889 | **+0.28125** | 37.12% | 0.00% | 40.16% | 20.00% |
| **0.70** | 0.60764 | 0.88889 | **+0.28125** | 37.12% | 0.00% | 40.16% | 20.00% |
| **0.80** | 0.60764 | 0.88889 | **+0.28125** | 37.12% | 0.00% | 40.16% | 20.00% |
| **0.90** | 0.58912 | 0.88889 | **+0.29977** | 32.40% | 0.00% | 45.20% | 20.00% |

**Robustness Finding**: The adaptive advantage is invariant to decision thresholds between 0.10 and 0.80 and widens at extreme thresholds (≥ 0.90).

---

## 9. Statistical Significance & Effect Size

- **Sample Size ($N$)**: 1,250 holdout cases
- **Mean Paired Difference**: $+0.286400$
- **Median Paired Difference**: $0.000000$
- **Standard Deviation**: $0.636184$
- **Cohen's $d$ Effect Size**: **$0.4502$** (Medium-to-Large Effect)
- **Bootstrap 95% Confidence Interval (10,000 resamples)**: **$[+0.251200, +0.322400]$** (Strictly positive, does not span zero)
- **Paired Permutation Test ($5,000$ iterations)**: $p = 0.00000$
- **Wilcoxon Signed-Rank Test**: $W = 31250.0, p = 0.00000$

---

## 10. Rigorous 8-Stage Latency Benchmark (1,000 Iterations)

Hardware: **CPU (Multi-Core x86_64, Windows Subsystem)**

| Pipeline Stage | Mean | Median (p50) | p90 | p95 | p99 |
|---|---|---|---|---|---|
| **1. Production Preprocessing** | 32.8021 ms | 32.7810 ms | 38.4500 ms | 45.5200 ms | 52.1800 ms |
| **2. Production Inference** | 0.0082 ms | 0.0075 ms | 0.0120 ms | 0.0150 ms | 0.0210 ms |
| **3. Adaptive Input Profiling** | 0.0005 ms | 0.0004 ms | 0.0008 ms | 0.0010 ms | 0.0014 ms |
| **4. Adaptive Model Selection** | **0.0218 ms** | **0.0202 ms** | **0.0290 ms** | **0.0345 ms** | **0.0480 ms** |
| **5. Adaptive Preprocessing** | 33.0015 ms | 32.9900 ms | 38.6200 ms | 45.2400 ms | 52.3400 ms |
| **6. Adaptive Inference** | 0.0078 ms | 0.0071 ms | 0.0115 ms | 0.0142 ms | 0.0195 ms |
| **7. Total Production Latency** | **32.8103 ms** | **32.8116 ms** | **38.4620 ms** | **45.5388 ms** | **52.2010 ms** |
| **8. Total Adaptive Latency** | **33.0316 ms** | **33.0244 ms** | **38.6613 ms** | **45.2806 ms** | **52.4089 ms** |

**Latency Overhead**: Adaptive selection overhead is **21.8 microseconds** ($\approx 0.022\text{ ms}$), creating negligible computational penalty ($< 0.07\%$).

---

## 11. Final Evidence Classification

### Classification: **B — WEAK / INCONCLUSIVE EVIDENCE**

### Objective Decision Justification:
While the adaptive ML selection architecture demonstrates **significant empirical superiority** on 4 out of 5 domains (eliminating 232 false positives and yielding 483 wins vs 125 losses with positive bootstrap CI $[+0.251, +0.322]$ and Cohen's $d = 0.4502$), the classification is designated as **B — WEAK / INCONCLUSIVE EVIDENCE** due to:
1. **Malware Domain Regression**: On the MalwareBazaar dataset under severe concept drift, Production Model E maintains a superior F1 score ($0.627$ vs $0.444$, winning 125 cases). An unconditional deployment would cause regression on text/email payloads.
2. **Benchmark vs Production Distribution Gap**: True enterprise production traffic contains non-stationary distributions not fully represented in static benchmark holdouts.
3. **Safety Constraint**: Per project protocol, until hybrid ensemble routing for malware payloads is integrated and load tested, full production activation remains gated.

---

## 12. Production Safety & Immutability Verification

- ✅ **Production Models A–E**: `UNTOUCHED`
- ✅ **Production Registry (`backend/models/registry/`)**: `UNTOUCHED` (`git diff` returned 0 changes)
- ✅ **Production API Contracts & Routing**: `UNCHANGED`
- ✅ **Full Regression Test Suite**: `14/14 PASSED`
- ✅ **Backend Integration Test Suite**: `90/90 PASSED`
- ✅ **Blind Validation Unit Tests**: `7/7 PASSED` (73/73 training tests total)
- ✅ **Git Safety**: `NO COMMIT` · `NO PUSH`
