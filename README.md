# 🛡️ NetraGraph AI: Criminal Network Analysis & Investigative Intelligence Platform

[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square)](https://github.com/)
[![React](https://img.shields.io/badge/React-19-blue?style=flat-square)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.1-646CFF?style=flat-square)](https://vitejs.dev/)
[![Compliance](https://img.shields.io/badge/Evidentiary%20Standard-IEA%20§65B%20%7C%20IT%20Act%20§69B-purple?style=flat-square)](https://indiankanoon.org/)

**NetraGraph AI** is an enterprise-grade Graph Intelligence and Investigative Decision Support Platform designed for law enforcement agencies, cyber crime cells, and financial intelligence units (FIU). It unifies force-directed knowledge graphs, mathematical centrality algorithms, autonomous behavioral anomaly engines, and a zero-hallucination GraphRAG AI assistant into a seamless judicial investigation workflow.

---

## ⚡ Key Capabilities Across All 7 Modules

1. **Intelligence Graph Core (`/network`)**: Force-directed multi-modal graph visualization with 1 to 4-hop BFS expansion, dynamic node spotlighting, and multi-factor filtering across entities, risk tiers, and relationship types.
2. **Entity Explorer & Resolution Engine (`/profiles`)**: Deterministic & probabilistic similarity matching (Levenshtein, Jaro-Winkler), side-by-side suspect comparison matrix, and 1-click duplicate identity resolution with Section 65B forensic audit logs.
3. **Network Analytics & Graph Algorithms (`/analytics`)**: PageRank authority scoring, Brandes Betweenness bottleneck detection, Louvain Modularity syndicate clustering, and Dijkstra shortest-path conduit tracing.
4. **Behavioral Anomaly Detection Engine (`/anomalies`)**: 4-hop circular fund recycling loops with return haircut calculations, burner device multi-IMSI hopping tracker, and nocturnal telephony burst correlators.
5. **Netra AI Copilot & GraphRAG Reasoning (`/assistant`)**: Natural Language-to-Cypher query plan synthesis with visual 8-stage GraphRAG execution telemetry and 6-tier structured responses with clickable citations.
6. **Geographic & Timeline Intelligence (`/geo-timeline`)**: Tactical geospatial map with India hub coordinates, transfer vector arcs, threat hotspot heat density circles, and interactive timeline playback scrubber (1x, 2x, 5x).
7. **Case Workspace & Evidence Vault (`/cases`, `/reports`)**: Docket lifecycle management, blockchain-inspired SHA-256 evidence chain with tamper verification validator, and Section 65B certified judicial report builder with PDF/JSON export.

---

## 🏗️ System Architecture

The repository is split into independent application boundaries:

```
frontend/
├── src/                  # React routes, UI components, hooks, services, and styles
├── package.json          # Frontend-local scripts
├── vite.config.ts
└── tsconfig.json

backend/
├── api/                  # Compatibility API modules
├── app/api/              # FastAPI routes and controllers
├── app/models/           # Request/response schemas
├── app/services/         # Business logic orchestration
├── app/database/         # Persistence and seed data
├── app/graph/            # Graph processing
├── app/ai/               # Extraction and investigation reasoning
└── Dockerfile
```

The React client owns presentation, client state, and API calls through `frontend/src/services/api.ts`. The Python service owns authentication integration points, API handling, data models, business services, graph processing, AI reasoning, and evidence workflows. Root `npm` scripts delegate to `frontend/` for backward-compatible local development.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              NetraGraph AI Architecture                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Enterprise Dark Command-Center Theme & Responsive AppShell                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. Investigation Workspace & Case Lifecycle Management (Docket CASE-2026-N09)          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. Core Analytical Engines:                                                            │
│    • Graph Centrality (Brandes, PageRank, Louvain Modularity, Dijkstra)                │
│    • Behavioral Anomaly Pipeline (Cycles, Multi-IMSI Hopping, CDR Bursts)              │
│    • Spatial-Temporal Radar (Geospatial Grid, Timeline Playback, Lag Correlation)      │
│    • GraphRAG Reasoning (Cypher Synthesis, 8-Stage Pipeline, Evidence Attribution)    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. Forensic Evidence & Integrity Layer:                                                │
│    • Tamper-Evident SHA-256 Cryptographic Block Ledger                                 │
│    • Section 65B Indian Evidence Act Compliance & Audit Trail                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. Synthetic Telemetry Data Layer:                                                     │
│    • 105+ Verified Entities · 148 Multi-Modal Graph Links                              │
│    • 50+ Tactical Facilities · 200+ Multi-Source Chronological Events                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Node.js**: v18.0 or higher
- **npm**: v9.0 or higher

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-org/netragraph-ai.git
cd netragraph-ai
npm install
```

For independent application setup:

```bash
cd frontend
npm install
npm run dev
```

In a second terminal, install and run the FastAPI service:

```bash
cd backend
pip install -r requirements.txt
npm run dev
```

### 2. Run Live Development Server
```bash
npm run dev
```
Open **[http://localhost:3000/](http://localhost:3000/)** in your web browser.

### 3. Production Build & Preview
```bash
npm run build
npx vite preview
```

---

## 🎯 9-Step Guided Investigation Demo Workflow

NetraGraph AI includes a pre-configured investigation docket **`CASE-2026-N09 (Operation Netra-Vigil)`** and an interactive **Demo Tour** modal accessible from the top header:

1. **Step 1: Case Workspace (`/cases`)** — Inspect docket metadata, priority, lead investigator, and 85% lifecycle progress.
2. **Step 2: Operational Dashboard (`/dashboard`)** — Review high-level KPIs, real-time alert feeds, and syndicate breakdown.
3. **Step 3: Intelligence Graph (`/network`)** — Perform a 2-hop BFS expansion on *Vikramaditya Rawat* and isolate financial transfer conduits.
4. **Step 4: Network Analytics (`/analytics`)** — Review PageRank authority scores (Vikramaditya Rawat #1, 24.8%) and identify *Arjun Menon* as the Hawala cross-community bridge.
5. **Step 5: Behavioral Anomalies (`/anomalies`)** — Detect the 4-hop circular fund recycling loop (`ALT-2026-001`) and burner phone IMEI hopping.
6. **Step 6: Geospatial & Timeline Radar (`/geo-timeline`)** — Replay the timeline scrubber and inspect the Sector 62 Noida call-center nocturnal co-location cluster.
7. **Step 7: Netra AI Copilot (`/assistant`)** — Query *"Show connections between Vikramaditya and Arjun Menon"* to inspect the 8-stage GraphRAG execution telemetry and evidence citations.
8. **Step 8: Validate Evidence Chain (`/cases`)** — Click *Validate Chain Hashes* to verify cryptographic integrity across all sealed exhibits.
9. **Step 9: Judicial Dossier Export (`/reports`)** — Preview and export the court-admissible Section 65B certified judicial intelligence dossier as PDF.

---

## ⚖️ Statutory & Evidentiary Safeguards

- **Indian Evidence Act, 1872 (§65B)**: Every electronic record, phone log, and banking ledger is cryptographically hashed with SHA-256 and sealed with an immutable chain of custody.
- **Information Technology Act, 2000 (§69B)**: Role-Based Access Control (RBAC) enforces strict authorization across Administrator, Investigator, Analyst, and Auditor roles.
- **Zero-Hallucination Policy**: All AI outputs strictly separate empirical observations, graph evidence, analytical inferences, and mandatory human review requirements.
- **Synthetic Research Prototype**: All individuals, phone numbers, IMEI codes, bank accounts, and addresses are fictional synthetic data created for intelligence demonstration.

---

## 📄 License
Licensed under the Apache-2.0 License.
