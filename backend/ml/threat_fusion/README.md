# NetraGraph Phase 12: Neuro-Symbolic Threat Fusion & Explainable Intelligence Engine

## 1. Overview & Purpose
In digital investigations, cyber intelligence analysts face multiple fragmented analytical signals—ranging from tabular machine learning predictions (Models A–E) and dynamic graph neural network risks (DT-GNN) to graph centrality metrics, structural anomaly indicators, and temporal burst patterns.

The **Neuro-Symbolic Threat Fusion & Explainable Intelligence Engine** provides an additive, high-order reasoning layer that deterministically synthesizes these disparate signals into a single, provenance-aware, and explainable **Threat Assessment**.

> [!IMPORTANT]
> **Decision Support Governance Disclaimer**:
> NetraGraph is decision-support software for authorized forensic investigators. All outputs produced by the Threat Fusion Engine are **model-derived statistical correlations and analytical indicators**. They must **strictly NEVER** be represented, stated, or implied as establishing legal culpability, intent, guilt, or causality.

---

## 2. Architectural Blueprint

```
Models A–E (Forensic ML)        DT-GNN (Temporal Risks)       Graph Analytics (Topology)
         │                               │                               │
         └───────────────────────────────┼───────────────────────────────┘
                                         ▼
                            1. Signal Normalization
                             (Range [0, 1], Typed)
                                         │
                                         ▼
                             2. Temporal Decay Weighter
                             (w_i = w0 * (1/2)^(dt/tau))
                                         │
                                         ▼
                            3. Conflict / Disagreement
                             (Variance & Confidence Penalty)
                                         │
                                         ▼
                             4. Deterministic Fusion
                             (Fused Risk != Confidence)
                                         │
                        ┌────────────────┴────────────────┐
                        ▼                                 ▼
             5. Symbolic Rule Engine           6. Provenance & Evidence Chain
              (Transparent Heuristics)           (Audit DAG & Fact Traceability)
                        │                                 │
                        └────────────────┬────────────────┘
                                         ▼
                             7. Explainability Engine
                             (Reproducible Attributions)
                                         │
                                         ▼
                           8. Unified Threat Assessment
```

---

## 3. Mathematical Fusion Formulation

### A. Temporal Decay Weighting
To reflect signal recency without discarding historical evidence, each signal $s_i$ with base source weight $w_i^{(0)}$ is weighted by:
$$w_i(t) = w_i^{(0)} \cdot \max\left( \omega_{\text{floor}}, \left(\frac{1}{2}\right)^{\frac{\max(0, t_{\text{ref}} - t_i)}{\tau_{\text{half-life}}}} \right)$$
where $\omega_{\text{floor}} = 0.10$ guarantees that historical records remain auditable in the evidence chain.

### B. Weighted Fused Risk
$$\bar{R} = \frac{\sum_{i=1}^n w_i \cdot s_i}{\sum_{i=1}^n w_i}, \quad \bar{R} \in [0.0, 1.0]$$

### C. Conflict & Disagreement Metric
Disagreement across analytical inputs is quantified via weighted sample standard deviation:
$$\text{Disagreement} = \sqrt{\frac{\sum_{i=1}^n w_i \cdot (s_i - \bar{R})^2}{\sum_{i=1}^n w_i}}, \quad \text{Disagreement} \in [0.0, 1.0]$$

### D. Independent Confidence Modeling
A critical invariant of the NetraGraph Threat Fusion Engine is that **high risk does not imply high confidence**:
$$\bar{C} = \frac{\sum_{i=1}^n w_i \cdot c_i}{\sum_{i=1}^n w_i}$$
$$\text{Confidence} = \max\left( C_{\text{min}}, \min\left(1.0, \bar{C} \cdot \left(1.0 - \gamma \cdot \text{Disagreement}\right) \cdot \text{Completeness}\right) \right)$$
Where severe analytical disagreement or sparse single-source reporting triggers an explicit confidence penalty.

---

## 4. Transparent Symbolic Rule Engine

Rules are explicit, deterministic, and versioned (`RULE_SET_VERSION = "1.0.0"`):
1. **`RULE_RAPID_CONNECTIVITY_SURGE_V1`**: Triggers when direct connections expand rapidly ($\ge 5$ in $< 6$ hours).
2. **`RULE_TEMPORAL_BURST_V1`**: Triggers on interaction bursts ($\ge 10$ events in $\le 300$ seconds).
3. **`RULE_MULTI_SOURCE_CONVERGENCE_V1`**: Triggers when $\ge 2$ independent subsystems report high threat ($\ge 0.70$).
4. **`RULE_INFRASTRUCTURE_REUSE_V1`**: Triggers when network infrastructure is shared across multiple cases or exhibits bridge betweenness.
5. **`RULE_DISCORDANT_INTELLIGENCE_V1`**: Triggers when endpoint ML and network GNN scores diverge significantly ($|s_1 - s_2| \ge 0.45$).

---

## 5. Bidirectional Evidence & Provenance Traceability
Every assessment produces an `EvidenceChain` answering:
- *"What caused this score?"* $\to$ `supporting_evidence`
- *"What contradicts this conclusion?"* $\to$ `contradicting_evidence`

Each signal links to an immutable `ProvenanceRecord` detailing data source, timestamp, transformation applied, and parent lineage DAG. Lineage is never fabricated.

---

## 6. API Endpoints
Mounted under `/api/threat-fusion`:
- `GET /api/threat-fusion/health`: Operational readiness and rule registry catalog.
- `POST /api/threat-fusion/analyze`: Evaluates explicit threat signals and returns a validated `ThreatAssessment`.
- `POST /api/threat-fusion/entity/{entity_id}`: Evaluates threat fusion for a specific entity using active case evidence.

---

## 7. Versioning & Immutability
- Fusion Algorithm: `FUSION_VERSION = "1.0.0"`
- Symbolic Ruleset: `RULE_SET_VERSION = "1.0.0"`
- Evidence Schema: `EVIDENCE_SCHEMA_VERSION = "1.0.0"`
- Assessment Schema: `ASSESSMENT_SCHEMA_VERSION = "1.0.0"`
