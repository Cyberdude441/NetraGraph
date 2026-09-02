# NetraGraph — Domain-Aware Adaptive Model Selection V2

## Overview
**Domain-Aware Adaptive Model Selection V2** is a specialized research-grade routing layer designed to select both the optimal feature representation and candidate machine learning model based on incoming cybersecurity domain signatures.

---

## Architectural Components

```
Incoming Unlabeled Payload (Flow / URL / Hash / Metadata)
                  │
                  ▼
        ┌───────────────────┐
        │  Domain Profiler  │ ──► Inspects Schema, Data Types & Signatures
        └───────────────────┘
                  │
         Domain Identification
                  ▼
        ┌───────────────────┐
        │  Feature Router   │ ──► Routes to Domain-Specific Representation:
        └───────────────────┘     • NETWORK_FLOW_V1
                  │               • MALWARE_STRUCTURAL_V2
                  │               • FALLBACK_TABULAR_V1
                  ▼
        ┌───────────────────┐
        │  Domain Selector  │ ──► Multi-Criteria Utility Function:
        └───────────────────┘     • Network Flow  ──► XGBoost / LightGBM
                  │               • DDoS Traffic  ──► CatBoost
                  │               • Malware Match ──► CatBoost + Struct Hashes
                  ▼
        ┌───────────────────┐
        │ Confidence Engine │ ──► Decision Margins & Safety Fallbacks
        └───────────────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Explainability    │ ──► Evidence-Grounded Audit Trail
        └───────────────────┘
```

---

## Domain Routing Matrix

| Security Domain | Preferred Representation | Primary Candidate Model | Fallback Model | Operational Target |
|---|---|---|---|---|
| **Network Intrusion** | `NETWORK_FLOW_V1` | XGBoost / LightGBM | Random Forest | High F1, Sub-millisecond latency |
| **DDoS Mitigation** | `NETWORK_FLOW_V1` | CatBoost | CatBoost | Zero FPR under unseen protocols |
| **URL Phishing** | `NETWORK_FLOW_V1` | XGBoost | XGBoost | High precision URL classification |
| **Malware Attribution** | `MALWARE_STRUCTURAL_V2` | CatBoost | Random Forest | High Macro F1, Minority recall |
| **Unknown Schema** | `FALLBACK_TABULAR_V1` | Random Forest | Random Forest | Crash-proof safety fallback |

---

## Safety Guarantees
1. **Production Models A–E**: Completely Untouched.
2. **Registry (`backend/models/registry/`)**: 0 modifications.
3. **No Automatic Deployment**: Research-only validation mode.
4. **Crash-Proof Routing**: Handles missing features, unknown schemas, and anomalous types via `FALLBACK_TABULAR_V1`.
