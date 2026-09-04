# NetraGraph Phase 16: Graph & Model Drift Observatory

## 1. Overview & Forensic Objective
The **Graph & Model Drift Observatory** is an investigator- and developer-facing decision-support and observability subsystem designed to **detect, measure, explain, record, and report drift** across five critical operational domains in NetraGraph:
1. **Graph Structural & Topological Drift**
2. **Feature & Input Distribution Drift**
3. **Model Output & Probability Drift (Models A–E)**
4. **Threat Intelligence / OSINT Source Behavior Drift**
5. **Data Quality & Ingestion Pipeline Drift**

---

## 2. Mandatory Non-Causal Boundary & Architectural Invariants
1. **Non-Causal Principle:** Drift is an operational telemetry and data-quality signal indicating statistical divergence from a reference baseline. **It does not establish criminality, guilt, culpability, or malicious intent.**
2. **Zero Automated Intervention:** The observatory strictly measures and advises. It **never automatically** retrains models, changes weights, alters decision thresholds, rewrites entity resolution, modifies graph structures, or alters case conclusions. Human analysts and investigators remain the exclusive decision gate.
3. **Model Performance Boundary:** In the absence of verified ground-truth labels, the observatory reports **output distribution and confidence drift**; it **never claims accuracy, precision, recall, or F1 degradation**.
4. **Real Data Availability:** If real historical feature or ingestion data is absent for an arbitrary operational window, the system explicitly returns `DATA_UNAVAILABLE` or `INSUFFICIENT_DATA`. **No synthetic operational data is manufactured.**

---

## 3. Metric-Specific Computational Complexity Bounds
Graph metrics are strictly bounded to prevent CPU exhaustion:
- **Node / Edge Count Delta:** $O(1)$
- **Graph Density Delta:** $O(1)$
- **Node Type Categorical Distribution (JSD):** $O(|V|)$
- **Relationship Type Categorical Distribution (JSD):** $O(|E|)$
- **Degree Distribution Shift (Wasserstein):** $O(|V| + |E| + |V| \log |V|)$
- **Connected Components Delta:** $O(|V| + |E|)$ via linear BFS/DFS
- **Optional Bounded PageRank:** $O(I \cdot (|V| + |E|))$ with power iterations capped at $I \le 30$

### Prohibited Computations
- **All-Pairs Shortest Paths:** $O(|V|^3)$ — Strictly forbidden in observatory routines.
- **Unbounded Betweenness Centrality:** $O(|V| \cdot |E|)$ — Excluded from default evaluations.

---

## 4. Statistical Divergence Primitives
All calculations are deterministic and numerically reproducible within $\pm 10^{-7}$ floating-point tolerance:
- **Population Stability Index (PSI):**
  $$\text{PSI} = \sum_{i=1}^k (P_i - Q_i) \times \ln\left(\frac{P_i}{Q_i}\right)$$
  Evaluated across 10 quantile bins with Laplace smoothing ($\epsilon = 10^{-4}$).
- **Jensen-Shannon Divergence (JSD):**
  $$\text{JSD}(P \parallel Q) = \frac{1}{2} D_{\text{KL}}(P \parallel M) + \frac{1}{2} D_{\text{KL}}(Q \parallel M), \quad M = \frac{1}{2}(P + Q)$$
  Symmetric, bounded in $[0.0, 1.0]$ using base-2 logarithm.
- **Wasserstein Distance (1D):**
  $$W_1(u, v) = \int_{-\infty}^{\infty} |U(t) - V(t)| \, dt$$
- **Kolmogorov-Smirnov Statistic (2-sample KS test):**
  $$D = \sup_x |F_{\text{ref}}(x) - F_{\text{curr}}(x)|$$
- **Missingness Rate Delta:**
  $$\Delta_m = |\text{Rate}_{\text{curr}} - \text{Rate}_{\text{ref}}|$$

---

## 5. Threshold Policy (`DriftThresholdPolicy` v1.0.0)
Thresholds represent **initial configurable policy defaults**, not objective truth:
- **PSI:** WATCH = 0.10, ELEVATED = 0.20, CRITICAL = 0.35
- **JSD:** WATCH = 0.15, ELEVATED = 0.30, CRITICAL = 0.50
- **Missingness Delta:** WATCH = 0.05, ELEVATED = 0.15, CRITICAL = 0.30
- **Minimum Sample Size ($N_{\text{min}}$):** 30 observations
- **Maximum Samples per Compute:** 50,000 observations (deterministic striding)

---

## 6. Cryptographic Provenance & Analytical Identity
Analytical observation IDs **do not depend on computation timestamp**:
$$\text{drift\_observation\_id} = \text{drf}:\{\text{domain}\}:\{\text{target}\}:\{\text{ref\_id[:8]}\}:\{\text{hash}[:16]\}$$
where:
$$\text{hash} = \text{sha256}\Big(\text{domain} \parallel \text{target} \parallel \text{ref\_id} \parallel \text{cmp\_digest} \parallel \text{metric} \parallel \text{alg\_ver} \parallel \text{policy\_ver}\Big)$$
Identical analytical inputs produce the exact same analytical observation ID. `computed_at` is tracked as a separate execution timestamp.

---

## 7. Bounded Persistence Architecture
Persistence uses **bounded thread-safe in-memory state with atomic JSON serialization** (`backend/models/drift_baselines.json`) and has **no PostgreSQL schema or migration impact**.

---

## 8. API Endpoints
All endpoints mounted under `/api/drift` with RBAC authorization:
- `GET  /api/drift/health` (ANALYST, INVESTIGATOR, ADMIN)
- `GET  /api/drift/baselines` (ANALYST, INVESTIGATOR, ADMIN)
- `GET  /api/drift/baselines/{baseline_id}` (ANALYST, INVESTIGATOR, ADMIN)
- `POST /api/drift/baselines` (INVESTIGATOR, ADMIN)
- `POST /api/drift/compute` (INVESTIGATOR, ADMIN)
- `GET  /api/drift/observations` (ANALYST, INVESTIGATOR, ADMIN)
- `GET  /api/drift/observations/{observation_id}` (ANALYST, INVESTIGATOR, ADMIN)
- `GET  /api/drift/summary` (ANALYST, INVESTIGATOR, ADMIN)
- `GET  /api/drift/graph` (ANALYST, INVESTIGATOR, ADMIN)
- `GET  /api/drift/models` (ANALYST, INVESTIGATOR, ADMIN)
