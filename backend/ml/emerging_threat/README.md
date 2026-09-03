# NetraGraph Phase 13: Emerging Threat & Early-Warning Intelligence Engine

## 1. Overview & Operational Purpose
In ongoing forensic and financial cybercrime investigations, static threat scores do not capture the **velocity**, **acceleration**, or **restructuring** of evolving threat syndicates.

The **Emerging Threat & Early-Warning Intelligence Engine** introduces a dedicated temporal intelligence layer that analyzes sequences of graph snapshots ($S_0 \to S_1 \to \dots \to S_k$) to detect:
- Rapid topology expansion and relationship churn
- Accelerating risk trajectories and sudden risk spikes
- Dynamic centrality shifts and bridge node emergence
- Syndicate community mergers, growth, and fragmentation
- Concentrated temporal bursts of interactions
- Emerging candidate subgraphs warranting human investigative review

> [!IMPORTANT]
> **Legal Governance & Decision-Support Disclaimer**:
> NetraGraph is decision-support software for authorized law enforcement and forensic investigators. All signals and early-warning events produced by this engine are **analytical indicators based on temporal and structural patterns**. They must **strictly NEVER** be represented, stated, or implied as establishing legal culpability, criminal guilt, intent, or legal causality.

---

## 2. Key Architectural Invariants

### A. Early-Warning Score $\neq$ Threat Risk
- **Threat Risk** (from Models A–E, DT-GNN, and Phase 12 Threat Fusion) measures current estimated threat probability or severity.
- **Early-Warning Score** measures the **rate of structural and behavioral change** over time.
- *Example*: A network with low static risk can generate a high early-warning score if its degree or edge velocity suddenly accelerates by 300%. Conversely, a static, unchanging high-risk syndicate produces a stable, low early-warning score.

### B. Early-Warning Score $\neq$ Confidence
- A high early-warning score does not automatically mean high confidence.
- Confidence is modeled independently based on temporal span, number of historical snapshot observations, and source diversity.

### C. Non-Causal Terminology
- Newly forming network clusters are strictly classified as *"emerging high-risk analytical subgraphs"* or *"network patterns requiring human investigation"*, never "criminal syndicates" or "guilty entities".

### D. Deterministic Deduplication
- Every event receives a deterministic SHA-256 fingerprint:
  $$\text{Fingerprint} = \text{SHA256}\left(\text{network\_id} \mathbin{\Vert} \text{sorted(entity\_ids)} \mathbin{\Vert} \lfloor t_{\text{start}} \rfloor \mathbin{\Vert} \lfloor t_{\text{end}} \rfloor \mathbin{\Vert} \text{event\_type}\right)$$
  Identical observations yield identical event identities, preventing alert duplication.

---

## 3. Mathematical & Algorithmic Formulations

### A. Topology Evolution
For snapshot pair $(S_{k-1}, S_k)$ with node counts $(N_{k-1}, N_k)$ and edge counts $(E_{k-1}, E_k)$:
- **Node Growth Rate**: $\Delta_N = \frac{N_k - N_{k-1}}{\max(1, N_{k-1})}$
- **Edge Growth Rate**: $\Delta_E = \frac{E_k - E_{k-1}}{\max(1, E_{k-1})}$
- **Node Churn**: $\chi_N = \frac{|V_k \setminus V_{k-1}| + |V_{k-1} \setminus V_k|}{|V_k \cup V_{k-1}|}$
- **Edge Churn**: $\chi_E = \frac{|E_k \setminus E_{k-1}| + |E_{k-1} \setminus E_k|}{|E_k \cup E_{k-1}|}$
- **Topology Velocity Score**:
  $$V_{\text{topo}} = 0.30 \cdot \min(1, \Delta_N^+) + 0.30 \cdot \min(1, \Delta_E^+) + 0.20 \cdot \chi_N + 0.20 \cdot \chi_E$$

### B. Risk Trajectories
Analyzes chronological risk series $[(t_0, r_0), (t_1, r_1), \dots, (t_k, r_k)]$:
- Velocity: $\bar{v} = \frac{1}{k} \sum_{i=1}^k (r_i - r_{i-1})$
- Acceleration: $\bar{a} = \frac{1}{k-1} \sum_{i=2}^k (v_i - v_{i-1})$
- Trajectory Categories: `RAPID_ESCALATION` ($\bar{v} \ge 0.15$), `SUDDEN_SPIKE` ($\max \Delta r \ge 0.30$), `SUSTAINED_ELEVATION` (all $r_i \ge 0.70$), `VOLATILE` ($\text{Var}(r) \ge 0.08$), `STABLE`, `DE_ESCALATING`.

### C. Centrality Shifts & Bridge Emergence
Calculates $\Delta \text{Betweenness}(v) = B_k(v) - B_{k-1}(v)$. If $B_k(v) \ge 0.35$ and $\Delta B(v) \ge 0.20$, entity $v$ is flagged as an emerging structural bridge broker.

### D. Community Restructuring
Uses NetworkX greedy modularity clustering and pairwise Jaccard matching $J(C_p, C_c) = \frac{|C_p \cap C_c|}{|C_p \cup C_c|}$ to flag:
- Emerging communities ($J < 0.20$ for all prior clusters)
- Community mergers ($\ge 2$ prior clusters coalescing into 1 current cluster)
- Community fragmentation (1 prior cluster splitting into $\ge 2$ current clusters)

### E. Temporal Bursts
Sliding window ($\Delta t = 300$s) across interaction events. If interactions $\ge 8$, flags a high-density operational burst.

---

## 4. API Endpoints
Mounted under `/api/emerging-threat`:
- `GET /api/emerging-threat/health`: Readiness, versioning, loaded detectors.
- `POST /api/emerging-threat/analyze`: Evaluates snapshot sequences and returns `EmergingThreatEvent`.
- `POST /api/emerging-threat/network/{network_id}`: Evaluates early warnings for a specific network.
- `GET /api/emerging-threat/events`: Lists active events with optional severity filtering.
- `GET /api/emerging-threat/events/{event_id}`: Retrieves event by UUID or SHA-256 fingerprint.

---

## 5. Versioning
- Engine Version: `DETECTOR_VERSION = "1.0.0"`
- Event Contract: `EVENT_SCHEMA_VERSION = "1.0.0"`
- Snapshot Contract: `SNAPSHOT_SCHEMA_VERSION = "1.0.0"`
