# NetraGraph Investigation Timeline & Graph Replay Engine (Phase 14)

## 1. Overview & Objective

The **Investigation Timeline & Graph Replay Engine** provides an investigator-facing temporal reconstruction layer for NetraGraph. It enables analysts to:

1. Inspect chronological forensic events across investigation lifecycles.
2. Reconstruct graph state at any arbitrary point in time ($T$).
3. Replay network topological evolution across selected time windows.
4. Inspect entity node and relationship edge additions, removals, and attribute shifts.
5. Correlate graph structure shifts with external intelligence signals (Phase 13 Emerging Threat alerts, Phase 12 Threat Fusion scores, and DT-GNN anomaly outputs).
6. Maintain transparent provenance (`SOURCE`, `DERIVED`, `CORRELATED`, `APPROXIMATED`).

---

## 2. Mandatory Non-Causal Governance Boundary

> [!IMPORTANT]
> **Decision-Support and Non-Causality Boundary**:
> This timeline and graph replay engine is strictly an analytical decision-support tool. Temporal correlation or topological changes do **not** establish causation, intent, guilt, or legal culpability. All findings require independent verification against source evidentiary records.

Every generated event, reconstructed state, and replay frame embeds the immutable governance disclaimer:
> *"This timeline and graph replay are analytical decision-support outputs based on available source data. Temporal correlation or structural change does not establish causation, intent, guilt, or criminal responsibility. Investigators must independently validate findings against source evidence."*

---

## 3. Mathematical & Deterministic Identity Guarantees

To ensure auditability across legal and intelligence proceedings, the engine enforces strict canonical determinism:

### A. Canonical Graph State Hash
$$\text{StateHash} = \text{SHA-256}\left(\text{CanonicalJSON}\left(\text{SortedNodes}, \text{SortedEdges}\right)\right)$$
- Nodes are sorted by string ID.
- Edges are canonicalized as undirected/directed tuples $(\min(u, v), \max(u, v), \text{rel\_type})$ and sorted lexicographically.
- Floats are rounded to 6 decimal places to eliminate cross-platform floating point representation variances.

### B. Deterministic Event Identity
$$\text{EventID} = \text{EVT-}\{\text{SHA-256}\left(\text{CanonicalJSON}\left(\text{network\_id}, \text{type}, t, \text{entities}, \text{edges}, \text{source}, \text{details}\right)\right)[:12]\}$$

### C. Invariant
$$\text{Identical Inputs} \implies \text{Identical Ordering} \implies \text{Identical State Hashes} \implies \text{Identical Identifiers}$$

---

## 4. Subsystem Components

```
backend/ml/investigation_timeline/
    ├── __init__.py           # Clean package exports
    ├── config.py             # Versions, thresholds, enums, SafetyLimitsConfig
    ├── models.py             # Pydantic models (Event, Frame, Manifest, ReconstructedState)
    ├── provenance.py         # Canonical JSON serialization & SHA-256 state hashing
    ├── snapshots.py          # Point-in-time state reconstruction (exact vs approximate)
    ├── changes.py            # Node/edge diff detector and DERIVED event emitter
    ├── correlation.py        # Read-only linkage with Phase 13, Threat Fusion, & DT-GNN
    ├── markers.py            # Investigator-created annotation registry
    ├── timeline.py           # Master chronological timeline builder & filtering
    ├── replay.py             # Frame-by-frame replay sequence generator
    ├── service.py            # Singleton orchestrator with limits & Prometheus telemetry
    └── README.md             # This document
```

---

## 5. Reconstruction Semantics

1. **Exact Reconstruction (`EXACT`)**: Target timestamp $|T - t_k| \le 10^{-6}$ matches an observed snapshot.
2. **Approximated Reconstruction (`APPROXIMATED`)**: No exact snapshot exists at $T$. The engine selects the nearest valid snapshot and explicitly flags the state as approximated, recording the temporal delta in `data_quality_warnings`.
3. **Empty Reconstruction (`EMPTY_INTERPOLATED`)**: Returned when no snapshots are provided.

---

## 6. Provenance Types

- `SOURCE`: Directly observed fact (raw snapshot, case entry, or human investigator marker).
- `DERIVED`: Computationally derived structural delta (node addition, edge deletion, density shift).
- `CORRELATED`: External analytical intelligence signal linked within the observation window.
- `APPROXIMATED`: State interpolated from nearest historical snapshot.

---

## 7. Safety Limits & Operational Telemetry

- **`max_snapshots`**: 100
- **`max_nodes`**: 10,000
- **`max_edges`**: 25,000
- **`max_replay_frames`**: 200
- **`max_window_duration`**: 10 years

Exceeding these limits raises a `ValueError` resulting in HTTP 413 (Payload Too Large) before expensive graph algorithms execute.
All metrics use bounded low-cardinality Prometheus labels (`status`, `reason`, `operation`). Zero entity IDs or notes are exposed in metrics.
