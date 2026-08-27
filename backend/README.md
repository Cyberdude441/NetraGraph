# NetraGraph AI – Backend Service

AI-Powered Criminal Network Analysis Backend built with **FastAPI**, **Pydantic**, and **NetworkX**.

---

## 📁 Architecture Overview

```
backend/
├── requirements.txt            # Python dependencies
├── README.md                   # Complete API Documentation
└── app/
    ├── main.py                 # FastAPI Application & CORS configuration
    ├── api/                    # REST API Endpoints
    │   ├── ingest.py           # POST /api/ingest
    │   ├── entities.py         # GET /api/entities & GET /api/entities/{id}
    │   ├── network.py          # GET /api/network/{id} & GET /api/network
    │   ├── profile.py          # GET /api/profile/{id}
    │   ├── analyze.py          # POST /api/analyze
    │   └── router.py           # Consolidated API router
    ├── models/                 # Pydantic v2 schemas
    │   ├── entity.py           # Entity, EntityType, EntityMetadata
    │   ├── relationship.py     # Relationship, RelationshipType, RelationshipMetadata
    │   ├── graph.py            # GraphNode, GraphEdge, NodeCentrality, MultiHopGraph
    │   ├── profile.py          # CriminalProfile, ThreatAxis, TimelineEvent
    │   ├── ingest.py           # IngestRequest, IngestResponse
    │   └── analysis.py         # AnalysisRequest, AnalysisResponse
    ├── database/               # Storage Layer & Pre-seeded Intelligence Data
    │   ├── db.py               # Thread-safe in-memory database store
    │   └── seed.py             # Pre-seeded criminal network dataset
    ├── graph/                  # NetworkX Link Analysis Engine
    │   └── network_manager.py  # BFS multi-hop subgraphs, centrality, shortest path
    ├── ai/                     # Intelligence Extraction & Reasoning
    │   ├── entity_extractor.py # Regex/NER extraction for phones, plates, accounts, persons
    │   └── investigation_agent.py # Graph reasoning and bridge-node detection
    └── services/               # Business Logic Orchestration
        ├── ingest_service.py
        ├── network_service.py
        ├── profile_service.py
        └── analysis_service.py
```

---

## 🚀 Quick Start

The backend is intentionally Python/FastAPI, not a Node application. The local `package.json` provides the requested `npm run dev` alias, while dependencies are installed from `requirements.txt`.

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the FastAPI Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Equivalent package command:

```bash
cd backend
npm install
npm run dev
```

### 3. Access Interactive API Documentation
* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🔌 API Endpoints Reference

### 1. Ingest Crime Reports / FIRs
**`POST /api/ingest`**
* Ingests unstructured police FIRs, call detail records (CDRs), or interrogation notes.
* Computes SHA-256 custody checksum.
* Extracts typed entities and infers criminal relationships into the knowledge graph.

**Request Body:**
```json
{
  "documentTitle": "FIR No. 208/2026 - Hawala Courier Intercept",
  "rawText": "Subject Raghav Malhotra (alias Sarpanch) coordinated via burner handset +91 98110 44217 with courier Imran Baig driving vehicle DL 3C AY 7742. Layered transfer of INR 1.9 Cr routed through HDFC A/C 447100912.",
  "caseId": "CS-2291",
  "sourceType": "FIR",
  "officerId": "IN-BOSE-4417"
}
```

**Response (`201 Created`):**
```json
{
  "documentId": "EV-9F2C",
  "sha256Hash": "9f2c7a918e3d4102b528a4cf810091aa4b92138e41bbcca0e89123019827a71d",
  "extractedEntities": [
    {
      "id": "NG-4471",
      "name": "Raghav Malhotra",
      "type": "Person",
      "riskScore": 94,
      "metadata": { "alias": "Sarpanch" }
    },
    {
      "id": "PH-9921",
      "name": "+91 98110 44217",
      "type": "Phone",
      "riskScore": 79
    }
  ],
  "extractedRelationships": [
    {
      "id": "REL-8812",
      "sourceId": "NG-4471",
      "targetId": "PH-9921",
      "type": "CALLS",
      "confidence": 0.88
    }
  ],
  "ingestedCount": 4,
  "riskAlerts": ["High risk entity extracted: Raghav Malhotra (Risk: 94)"],
  "summary": "Processed 'FIR No. 208/2026' successfully.",
  "status": "PROCESSED_AND_INDEXED"
}
```

---

### 2. Query All Entities
**`GET /api/entities`**

**Query Parameters (Optional):**
* `type`: Filter by `Person`, `Organization`, `Location`, `Phone`, `Vehicle`, `BankAccount`
* `min_risk`: Minimum risk threshold (e.g. `min_risk=80`)
* `network`: Syndicate network filter (e.g. `Ghost Ledger`)
* `search`: Keyword search across names, aliases, or IDs

**Example:**
```bash
curl "http://localhost:8000/api/entities?min_risk=80"
```

---

### 3. Multi-Hop Criminal Network Graph
**`GET /api/network/{entity_id}?hops=2`**
* Traverses the NetworkX knowledge graph starting from the target entity.
* Computes degree, betweenness centrality, and PageRank scores.

**Response (`200 OK`):**
```json
{
  "rootEntityId": "NG-4471",
  "hopDepth": 2,
  "nodes": [...],
  "edges": [...],
  "centrality": {
    "NG-4471": {
      "degree": 5,
      "betweenness": 0.41,
      "closeness": 0.65,
      "pagerank": 0.22,
      "communityId": 1
    }
  },
  "subgraphStats": {
    "totalNodes": 9,
    "totalEdges": 10,
    "density": 0.278
  }
}
```

---

### 4. Criminal Profile Dossier & Threat Radar
**`GET /api/profile/{entity_id}`**
* Retrieves the complete criminal dossier for any subject.
* Includes dynamic 5-axis threat radar scores (*Violence, Finance, Mobility, Influence, Recidivism*).

**Example:**
```bash
curl "http://localhost:8000/api/profile/NG-4471"
```

**Response (`200 OK`):**
```json
{
  "entity": {
    "id": "NG-4471",
    "name": "Raghav Malhotra",
    "type": "Person",
    "riskScore": 94,
    "metadata": { "alias": "Sarpanch", "status": "At Large" }
  },
  "threatRadar": [
    { "axis": "Violence", "score": 82 },
    { "axis": "Finance", "score": 98 },
    { "axis": "Mobility", "score": 72 },
    { "axis": "Influence", "score": 88 },
    { "axis": "Recidivism", "score": 78 }
  ],
  "offenses": ["Money laundering under PMLA §3", "Arms trafficking"],
  "timeline": [...],
  "directAssociates": [...],
  "networkCentralityRank": 1,
  "intelligenceBrief": "Subject Raghav Malhotra holds centrality rank #1 within the active intelligence index."
}
```

---

### 5. AI Graph Reasoning & Copilot Assistant
**`POST /api/analyze`**
* Natural language investigative query reasoning.
* Detects bridge nodes, shortest money trails, and risk factors.

**Request Body:**
```json
{
  "query": "Which nodes bridge Ghost Ledger and Vault-7 Ring?",
  "scopeNetwork": "Ghost Ledger",
  "includePathfinding": true
}
```

**Response (`200 OK`):**
```json
{
  "query": "Which nodes bridge Ghost Ledger and Vault-7 Ring?",
  "reasoning": "Analyzed criminal graph index. Identified 2 high-impact structural bridge intermediaries.",
  "keyFindings": [
    "Primary bridge node identified: Ayesha Qureshi (Person, Betweenness 0.41).",
    "Layered corporate front identified connecting domestic accounts to offshore entities."
  ],
  "flaggedEntities": [...],
  "identifiedBridges": ["Ayesha Qureshi (Person, Betweenness 0.41)"],
  "suggestedActions": [
    "Issue lookout circular (LOC) for primary bridging operative.",
    "Subpoena transaction ledger for shell accounts with offshore transfers."
  ],
  "confidenceScore": 0.94,
  "graphPath": [
    {
      "sourceName": "Raghav Malhotra",
      "targetName": "Ayesha Qureshi",
      "relationshipType": "Direct Link",
      "detail": "Verified network edge"
    }
  ]
}
```
