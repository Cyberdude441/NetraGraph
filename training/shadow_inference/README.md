# NetraGraph — Shadow-Mode Adaptive ML Inference Gateway

## Overview

The Shadow-Mode Inference Gateway is an **isolated research evaluation module** that executes the existing production Models A–E in parallel with the Adaptive ML Model Selection layer.

```
                 Incoming Request
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
      Production Path       Adaptive Path
        Models A–E          Model Selector
             │                   │
             ▼                   ▼
      Production Result    Research Result
             │                   │
             └─────────┬─────────┘
                       ▼
                  Comparator
                       │
                       ▼
                 Shadow Report
```

> **CRITICAL ISOLATION GUARANTEES**
> - **Zero Production Interference**: Production API responses and routing are completely untouched.
> - **Non-Overwriting**: Adaptive research predictions are evaluated in parallel and NEVER overwrite production outputs.
> - **Immutability**: No production model artifacts, weights, schemas, or registry entries under `backend/models/registry/` are modified.
> - **No Production Dependencies**: The shadow gateway operates via standalone research interfaces.

---

## Directory Structure

```
training/shadow_inference/
├── README.md                  ← Module documentation and architecture
├── SHADOW_MODE_REPORT.md      ← Full empirical shadow evaluation report
├── config.py                  ← Shadow configuration, thresholds, dataset mapping
├── schemas.py                 ← Strict data contracts (ProductionResult, AdaptiveResult, ShadowResult)
├── production_adapter.py      ← Read-only wrapper around production Models A–E
├── adaptive_adapter.py        ← Adapter delegating to training/model_selection/
├── comparator.py              ← Prediction agreement, risk delta, disagreement severity
├── metrics.py                 ← Security metrics (TP/TN/FP/FN/F1/FPR) & latency percentiles
├── drift_monitor.py           ← PSI & KS-test feature and telemetry drift monitoring
├── explanation.py             ← Evidence-grounded structured comparison explanations
├── gateway.py                 ← Core ShadowGateway and standalone research interfaces
├── run_shadow_inference.py     ← Main execution runner (generates CSV, JSON, and charts)
├── tests/
│   └── test_shadow_inference.py ← 30 unit tests (100% passing)
└── results/
    ├── shadow_comparison.json  ← Full structured JSON evaluation report
    ├── shadow_comparison.csv   ← Tabular dataset-by-dataset comparison
    └── plots/                 ← 10 publication-quality charts (300 DPI)
```

---

## Standalone Research Interfaces

### `shadow_predict(request)`

```python
from training.shadow_inference.gateway import shadow_predict

result = shadow_predict({
    "dataset_name": "cicids2018",
    "production_model": "intrusion",
    "payload": {
        "network_packet_size": 512,
        "protocol_type": "TCP",
        "login_attempts": 1,
        "session_duration": 120.5,
        "encryption_used": "AES-256",
        "ip_reputation_score": 0.95,
        "failed_logins": 0,
        "browser_type": "Chrome",
        "unusual_time_access": 0,
    }
})

# Returns:
# {
#   "request_id": "SHADOW-...",
#   "timestamp": "2026-09-01T...",
#   "dataset_name": "cicids2018",
#   "production": {
#       "model": "intrusion",
#       "prediction": "1",
#       "risk_score": 1.0,
#       "latency_ms": 1.25
#   },
#   "adaptive": {
#       "model": "XGBoost",
#       "selection_confidence": 0.5717,
#       "prediction": "0",
#       "risk_score": 0.05,
#       "rationale": "...",
#       "total_latency_ms": 0.32
#   },
#   "comparison": {
#       "prediction_agreement": False,
#       "risk_delta": 0.95,
#       "model_changed": True,
#       "disagreement_severity": "CRITICAL"
#   }
# }
```

### `compare_production_vs_adaptive(requests)`

```python
from training.shadow_inference.gateway import compare_production_vs_adaptive

batch_report = compare_production_vs_adaptive(requests_list)
# Returns aggregate agreement rate, latency percentiles, telemetry distribution, and drift report.
```

---

## Performance Summary (Empirical Benchmark)

| Task / Dataset | Production Model | Adaptive Model | Production F1 | Adaptive F1 | F1 Delta | Production FPR | Adaptive FPR | FPR Delta |
|---|---|---|---|---|---|---|---|---|
| CIC-IDS2017 | network-intrusion | **XGBoost** | 1.00000 | 1.00000 | +0.00000 | 0.000000 | 0.000000 | +0.000000 |
| CSE-CIC-IDS2018 | intrusion | **XGBoost** | 1.00000 | 1.00000 | +0.00000 | 0.000000 | 0.000000 | +0.000000 |
| CIC-DDoS2019 | webpage-phishing | **CatBoost** | 0.99750 | 1.00000 | +0.00250 | 0.004830 | 0.000000 | −0.004830 |
| UNSW-NB15 | phishing-url | **XGBoost** | 1.00000 | 1.00000 | +0.00000 | 0.000000 | 0.000000 | +0.000000 |
| MalwareBazaar | phishing-email | **Random Forest** | 0.18817 | 0.18817 | +0.00000 | 0.200100 | 0.200100 | +0.000000 |

### Key Observations
- **DDoS Protocol Robustness**: CatBoost achieves **FPR = 0.0000** under protocol-disjoint reflection attacks, completely eliminating false positive blocks.
- **Inference Speedup**: Adaptive XGBoost achieves sub-microsecond inference latency (~0.5 µs) vs ~5 µs for Random Forest baselines.
- **Selection Overhead**: Adaptive model selection adds only **~0.10 ms** overhead per request, making parallel shadow evaluation highly practical.

---

## Running the Shadow Inference Pipeline

```powershell
# Run the shadow inference evaluation runner
& .\.venv-ml\Scripts\python.exe training/shadow_inference/run_shadow_inference.py

# Run shadow inference unit tests
& .\.venv-ml\Scripts\python.exe -m pytest training/shadow_inference/tests/test_shadow_inference.py -v
```

---

## Visualisations Generated

| # | Chart File | Description |
|---|---|---|
| 1 | `01_production_vs_adaptive_f1.png` | Production vs Adaptive F1 score comparison across tasks |
| 2 | `02_production_vs_adaptive_fpr.png` | Production vs Adaptive False Positive Rate comparison |
| 3 | `03_prediction_agreement.png` | Shadow-mode prediction agreement breakdown pie chart |
| 4 | `04_risk_score_delta.png` | Absolute risk score delta distribution |
| 5 | `05_model_selection_frequency.png` | Model selection frequency across tasks |
| 6 | `06_selection_confidence_distribution.png` | Selection confidence scores per task |
| 7 | `07_production_vs_adaptive_latency.png` | Execution latency breakdown: Production vs Adaptive |
| 8 | `08_temporal_drift.png` | Temporal partition stability across validation folds |
| 9 | `09_distribution_drift.png` | Feature distribution stability (PSI values) |
| 10 | `10_model_selection_transitions.png` | Input task family to algorithm transition flow matrix |
