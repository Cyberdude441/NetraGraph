# NetraGraph Dynamic Temporal Graph Neural Network (DT-GNN) Layer

## 1. Overview & Motivation
In digital forensics and complex cyber threat investigations, criminal syndicates, intrusion operations, and phishing infrastructures evolve dynamically over time. Traditional machine learning models (such as tabular classifiers Models A–E) score individual isolated sessions, URLs, emails, or flows at a single moment in time. However, coordinated attacks exhibit distinct topological signatures—such as infrastructure reuse, multi-hop money laundering hops, and credential proxy chains—that manifest across a sequence of interactions.

The **Dynamic Temporal Graph Neural Network (DT-GNN)** provides an additive, high-order relational analytical layer that operates over evolving graph topology $[G(t_0) \to G(t_1) \to \dots \to G(t_k)]$, generating:
1. **Network-level Threat Embeddings**: Continuous dense representations of the entire case investigation graph.
2. **Node-level Threat Risk Scores**: Calibrated continuous risk metrics $\in [0, 1]$ identifying prioritized suspicious entities.
3. **Edge-level Anomaly Scores**: Quantifying suspicious, high-velocity, or anomalous relationship bridges.
4. **Model-derived Explainability Attributions**: Attributing risk elevations to specific influential nodes, edges, and subgraphs without claiming legal culpability or deterministic causality.

---

## 2. Architectural Blueprint

```
Investigative Evidence / CDR / Financial Logs / Threat Telemetry
                           │
                           ▼
                  Neo4j / NetworkX Graph
              (Entities, Relationships, Time)
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
     Existing Models A–E          Graph Topology
   (Independent Binaries)        (Nodes, Edges, Time)
             │                           │
             │ (Optional Preds)          │
             └─────────────┬─────────────┘
                           ▼
              Temporal Graph Constructor
               (DynamicGraphSequence)
                           │
                           ▼
          Dynamic Temporal GNN (DT-GNN)
     ┌─────────────────────────────────────────┐
     │ 1. Multi-Modal Categorical Embeddings   │
     │ 2. Bochner Harmonic Time Encodings      │
     │ 3. Spatial Relational Graph Convolution │
     │ 4. Temporal Sequence Gating (T-GRU)     │
     │ 5. Multi-Scale Readout Heads            │
     └─────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Node Threat      Edge Anomaly    Network Embedding
     Risk Scores       Link Scores     & Graph Anomaly
          │                │                │
          └────────────────┼────────────────┘
                           ▼
              Attribution & Explainability
         (Influential Nodes, Links, Subgraphs)
                           │
                           ▼
              Decision Support & REST APIs
```

---

## 3. Mathematical Formulation

### A. Multi-Modal Node & Edge Encoding
Each entity $v$ is characterized by its categorical classification $c_v \in \mathcal{C}$ (e.g., `Person`, `BankAccount`, `IPAddress`) and continuous attribute vector $x_v \in \mathbb{R}^{d_{\text{cont}}}$:
$$h_v^{(0)} = \text{LayerNorm}\left( W_{\text{type}} \mathbf{e}(c_v) + W_{\text{cont}} x_v + W_{\text{fusion}} p_v \right)$$
where $p_v \in \mathbb{R}^5$ is the optional prediction vector from Models A–E.

Each relationship $e_{uv}$ is characterized by interaction type $r_{uv} \in \mathcal{R}$ and interaction weight/duration/amount $a_{uv}$:
$$e_{uv} = \text{LayerNorm}\left( W_{\text{rel}} \mathbf{e}(r_{uv}) + W_{\text{attr}} a_{uv} \right)$$

### B. Bochner Harmonic Time Positional Encoding
To represent continuous time intervals $\Delta t_{uv} = t_{\text{ref}} - t_{uv}$ without treating time merely as an ordinary linear scalar, we leverage continuous harmonic kernel mapping based on Bochner's theorem:
$$\Phi(\Delta t) = \left[ \cos(\omega_1 \Delta t), \sin(\omega_1 \Delta t), \dots, \cos(\omega_k \Delta t), \sin(\omega_k \Delta t) \right]^T$$
where $\omega_i = \exp\left(-\frac{2i}{d} \ln(10000)\right)$.

### C. Relational Spatial Message Passing
Within each temporal snapshot $t$, spatial message passing aggregates information from adjacent nodes conditioned on relational link attributes and time differences:
$$m_{uv} = \text{LeakyReLU}\left( W_{\text{src}} h_u + W_{\text{dst}} h_v + W_{\text{edge}} e_{uv} + W_{\text{time}} \Phi(\Delta t_{uv}) \right)$$
$$\alpha_{uv} = \frac{\exp(a^T m_{uv})}{\sum_{w \in \mathcal{N}(v)} \exp(a^T m_{wv})}$$
$$h_v^{(l+1)} = \text{LayerNorm}\left( h_v^{(l)} + \text{Dropout}\left(\text{GELU}\left(W_{\text{upd}} \left[ h_v^{(l)} \,\|\, \sum_{u \in \mathcal{N}(v)} \alpha_{uv} W_{\text{val}} h_u^{(l)} \right]\right)\right)\right)$$

### D. Temporal Sequence Recurrence
Given a sequence of spatial snapshot representations $\left[ H^{(0)}, H^{(1)}, \dots, H^{(T-1)} \right]$, temporal recurrence is computed via a Temporal Gated Recurrent Unit (T-GRU):
$$H^{(t)} = \text{GRUCell}\left( H_{\text{spatial}}^{(t)}, H^{(t-1)} \right)$$
capturing cumulative structural evolution, sudden surges in activity, and behavioral drifts.

---

## 4. Models A–E Integration Contract
The DT-GNN is strictly **additive**. It does not replace or modify Models A–E:
- Model A: Session Intrusion Detection (`intrusion`)
- Model B: Network Intrusion Detection (`network-intrusion`)
- Model C: Phishing URL Detection (`phishing-url`)
- Model D: Web Page Phishing Detection (`webpage-phishing`)
- Model E: Phishing Email Detection (`phishing-email`)

When available, model prediction probabilities (e.g., `{'phishing-url': 0.95}`) are projected through `model_fusion_proj` into node space. When absent, the feature vector is zero-padded, allowing the DT-GNN to operate with 100% functionality on graph-native topology alone.

---

## 5. Prevention of Temporal Data Leakage
In dynamic network analysis, training models using future graph interactions to predict past events constitutes critical temporal leakage. The DT-GNN pipeline enforces **strict chronological partitioning**:
- **Past ($\le 70\%$ of observation time)**: Training Set.
- **Intermediate ($70\% - 85\%$)**: Validation Set (Hyperparameter tuning, early stopping).
- **Future ($> 85\%$)**: Out-of-Time Test Set.

---

## 6. Explainability & Governance Principles
Attribution outputs provide investigative transparency:
- **Influential Nodes**: Entities with highest threat attribution scores.
- **Influential Relationships**: Edges with highest attention coefficients.
- **Critical Risk Subgraph**: The connected component responsible for elevated risk.

> [!NOTE]
> **Governance Disclaimer**: All DT-GNN outputs are statistical attributions and anomaly indicators for investigative prioritization. They must strictly **NEVER** be presented as legal determinations of culpability, intent, or causality.

---

## 7. Performance & Resource Constraints
- **Hardware**: Default CPU inference; optional CUDA auto-detection.
- **Scalability Safety Limits**:
  - Maximum nodes per snapshot: 10,000.
  - Maximum edges per snapshot: 50,000.
  - Requests exceeding limits return HTTP 413 to prevent algorithmic complexity attacks.
- **Lifecycle**: Thread-safe singleton service (`dt_gnn_service`) eliminates redundant model loading overhead.
