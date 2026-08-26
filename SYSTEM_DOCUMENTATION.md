# NetraGraph AI: Technical Architecture & System Documentation

**Classification**: Law Enforcement Intelligence System (Synthetic Research Prototype)  
**System Status**: Production Feature-Complete (100%)  
**Target Legal / Evidentiary Compliance**: Indian Evidence Act, 1872 (§65B) · Information Technology Act, 2000 (§69B)

---

## 1. Executive Summary & Problem Statement

Modern financial and cyber crimes—such as tech-support extortion, SIM box fraud, and multi-tier hawala syndicates—operate across fragmented jurisdictions using rapid layering tactics (burner handsets, mule bank accounts, OTC cryptocurrency swaps). Traditional tabular databases struggle to detect multi-hop conduits or uncover covert syndicate kingpins.

**NetraGraph AI** transforms criminal investigations into an automated, explainable decision-support workflow by unifying:
1. **Force-Directed Knowledge Graphs** with BFS multi-hop expansion
2. **Graph Machine Learning Algorithms** (PageRank, Brandes Betweenness, Louvain Modularity)
3. **Behavioral Anomaly Engines** (4-hop circular fund recycling, IMEI-IMSI hopping)
4. **Autonomous GraphRAG AI Copilot** (Natural Language-to-Cypher reasoning with 100% evidence attribution)
5. **Spatial-Temporal Radar** (Geospatial tactical maps, cell tower triangulation, timeline replay)
6. **Forensic Evidence Vault** (Tamper-evident SHA-256 cryptographic audit chain and Section 65B certified dossiers)

---

## 2. Technology Stack & Architectural Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NetraGraph AI System Stack                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Frontend & UX: React 19 · Vite · Tailwind CSS · TanStack Router & Start SSR     │
│ Graph Visualization: @xyflow/react (Custom SVG nodes, forensic edges, minimap)  │
│ Charting & Analytics: Recharts · Lucide Icons · Sonner Notifications           │
│ Knowledge Graph Data Layer: 105+ synthetic entities, 148 links, 50+ locations  │
│ Algorithmic Layer: Brandes Centrality, Louvain Community, Dijkstra Conduits     │
│ Reasoning Engine: Netra GraphRAG (8-stage execution telemetry, Cypher synthesis)│
│ Evidence Integrity: SHA-256 Cryptographic Block Ledger (§65B Compliance)        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Deep Dive into the 7 Core Intelligence Modules

### Module 1: Intelligence Graph Core (`/network`)
- **BFS Multi-Hop Expansion**: Allows investigators to dynamically drill 1-hop, 2-hop, 3-hop, or custom-depth relationships around key suspects without page reloads.
- **Dynamic Faceted Filters**: Filter by 7 entity classifications (*Person, Phone, Location, Vehicle, Organization, Bank Account, Event*), 4 risk tiers (*Critical, High, Medium, Low*), and relationship modalities (*Financial, Communication, Association, Co-Location*).

### Module 2: Entity Explorer & Entity Resolution (`/profiles`)
- **Deterministic & Probabilistic Similarity Algorithms**: Uses Levenshtein edit distance for aliases, Jaro-Winkler for address variations, and exact match for shared identifiers (IMEI, PAN, Account Numbers).
- **Duplicate Identity Resolution Queue**: Side-by-side comparison matrix with 1-click consolidation and Section 65B reversible merge audit logging.

### Module 3: Network Analytics & Graph Algorithms (`/analytics`)
- **Brandes Betweenness Centrality**: Pinpoints critical bottleneck bridges connecting disparate syndicates.
- **PageRank Authority Scoring**: Calculates eigenvector authority to isolate covert kingpins shielding themselves behind intermediate mules.
- **Louvain Modularity Clustering**: Automatically partitions the global graph into operational cells (e.g., *Noida Call Center, Bhubaneswar SIM Farm, Mumbai Hawala Conduit, LockNet Ransomware Group*).
- **Dijkstra Shortest-Path Tracer**: Traces direct money/call conduits between arbitrary suspects.

### Module 4: Anomaly Detection & Behavioral Engine (`/anomalies`)
- **Circular Fund Recycling Loop (`ALT-2026-001`)**: Identifies closed-circuit financial laundering where funds return to origin syndicate controllers with a 9% haircut margin.
- **Burner Handset & Multi-IMSI Hop Tracker (`ALT-2026-002`)**: Flags burner devices cycling through 8+ SIM registrations within 6 days across telecom circles.
- **Nocturnal Telephony Burst Correlator (`ALT-2026-003`)**: Detects +350% VoIP surges coinciding with victim complaint filings.

### Module 5: Netra AI Copilot & GraphRAG Engine (`/assistant`)
- **Natural Language-to-Cypher Query Synthesis**: Converts plain-text investigator questions (e.g., *"Show connections between Vikramaditya and Arjun Menon"*) into deterministic Cypher traversal plans.
- **Visual 8-Stage GraphRAG Pipeline**: Exposes real-time execution steps (*Intent $\rightarrow$ NER $\rightarrow$ Subgraph Retrieval $\rightarrow$ Traversal $\rightarrow$ Ingestion $\rightarrow$ Synthesis $\rightarrow$ Confidence Calibration $\rightarrow$ Section 65B Assertion*).
- **Zero-Hallucination 6-Tier Output Standard**: Strictly separates Observed Facts, Graph Evidence, Analytical Inference, and Human Review Requirements.

### Module 6: Geographic & Timeline Intelligence (`/geo-timeline`)
- **Tactical Geospatial Map**: Interactive dark command-center canvas projecting tactical facilities across Delhi NCR, Bhubaneswar, Mumbai, Kolkata, and Bengaluru.
- **Hotspot Heat Density & Vector Arcs**: Visualizes financial transfer vectors and physical co-location clusters.
- **Chronological Playback Scrubber**: Interactive replay with 1x, 2x, and 5x speed controls.
- **Spatial-Temporal Lag Correlation**: Analyzes time lag between physical meetings and subsequent financial transfers (e.g., 18-hour lag correlation with 89% confidence).

### Module 7: Case Workspace, Evidence Integrity & Report System (`/cases`, `/reports`)
- **Case Lifecycle Management**: Tracks docket status, priorities, lead investigator, and lifecycle progress.
- **Blockchain-Inspired SHA-256 Evidence Chain**: Validates tamper-evident cryptographic block linkages (Block 001 $\rightarrow$ 002 $\rightarrow$ 003 $\rightarrow$ 004).
- **Judicial Intelligence Report Builder**: Document-style report preview with Section 65B statutory certificate and one-click PDF/JSON export.
- **Role-Based Access Control (RBAC)**: Enforces access restrictions across Administrator, Investigator, Analyst, and Auditor roles under IT Act Section 69B.

---

## 4. 9-Step Hackathon & Evaluation Demo Script

1. **Step 1 (`/cases`)**: Open active docket **CASE-2026-N09 (Operation Netra-Vigil)**.
2. **Step 2 (`/dashboard`)**: Inspect real-time KPIs, threat severity distributions, and syndicate breakdown.
3. **Step 3 (`/network`)**: Launch the knowledge graph, perform a 2-hop BFS expansion on *Vikramaditya Rawat*, and isolate financial links to *Apex Global Infotech*.
4. **Step 4 (`/analytics`)**: Open network analytics to confirm *Vikramaditya Rawat* as Rank #1 in PageRank (24.8%) and *Arjun Menon* as the cross-community Hawala bridge.
5. **Step 5 (`/anomalies`)**: Investigate anomaly `ALT-2026-001` (4-hop circular fund recycling loop) and burner phone IMEI hopping.
6. **Step 6 (`/geo-timeline`)**: Replay the timeline scrubber and inspect the *Sector 62 Noida Call Center* nocturnal co-location cluster.
7. **Step 7 (`/assistant`)**: Prompt Netra AI with *"Show connections between Vikramaditya and Arjun Menon"* and observe the 8-stage GraphRAG execution telemetry.
8. **Step 8 (`/cases`)**: Click *Validate Chain Hashes* in the Evidence Chain tab to verify the SHA-256 cryptographic chain of custody.
9. **Step 9 (`/reports`)**: Preview and export the court-admissible Section 65B certified judicial intelligence dossier.

---

## 5. Synthetic Research Prototype & Statutory Safeguards

- **Synthetic Telemetry**: All phone numbers, IMEI codes, bank account details, and geographical facilities are fictional synthetic data generated for research and demonstration purposes.
- **Judicial Grounding**: In compliance with Indian Evidence Act §65B and Information Technology Act §69B, every AI inference is stamped as an algorithmic observation requiring certified human investigator corroboration before court submission.
