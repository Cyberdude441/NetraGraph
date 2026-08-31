# NETRAGRAPH AI — INVESTIGATION-GRADE KNOWLEDGE GRAPH & ANALYTICS SCHEMA

**Document Version**: 3.0.0  
**Status**: Production Formal Specification  
**Classification**: Police & Forensics Intelligence Specification (Compliant with Indian Evidence Act §65B & IT Act §69B)

---

## 1. Formal Dual-Domain Graph Partition

NetraGraph AI enforces a strict architectural partition between **Public Statistical Aggregates** and **Authorized Case Investigation Evidence**.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   NETRAGRAPH AI KNOWLEDGE GRAPH ENGINE                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│       PUBLIC NCRB DOMAIN        │   │      INVESTIGATION DOMAIN       │
│     (PUBLIC_NCRB_DATA)          │   │   (INVESTIGATION_CASE_DATA)     │
│                                 │   │                                 │
│  - Dataset       - CrimeCategory│   │  - Case         - Phone         │
│  - Year          - CrimeStat    │   │  - Person       - Email         │
│  - State         - PoliceDisp   │   │  - Organization - IPAddress     │
│  - City          - CourtOutcome │   │  - Device       - Domain        │
│  - CrimeMotive                  │   │  - BankAccount  - Evidence      │
│                                 │   │  - Transaction  - MLPrediction  │
│  STRICT RULE:                   │   │                                 │
│  NEVER contains person-level    │   │  STRICT RULE:                   │
│  identities, bank accounts, or  │   │  Every entity & edge MUST have  │
│  suspect relationships.         │   │  case_id & Section 65B memo.    │
└─────────────────────────────────┘   └─────────────────────────────────┘
```

---

## 2. Node Schema & Labels

### A. Public NCRB Domain
| Label | Description | Primary Key Format | Provenance Authority |
| :--- | :--- | :--- | :--- |
| `(:Dataset)` | Official OGD catalog feed | `DATASET-NCRB-CORE` | `data.gov.in` (Ministry of Home Affairs) |
| `(:Year)` | Annual statistical survey cycle | `YEAR-2025` | NCRB Crime in India |
| `(:State)` | States & Union Territories | `STATE-TS`, `STATE-OD` | NCRB Table 18A.1 |
| `(:City)` | Metropolitan reporting jurisdiction | `CITY-DELHI`, `CITY-MUMBAI` | NCRB Table 18A.2 |
| `(:CrimeCategory)` | Statutory legal offense head | `CAT-132405A23563` | IT Act 2000 (§66, §66C, §66D, §67) |
| `(:CrimeMotive)` | Offense motive classification | `MOTIVE-76D49195F2EA` | NCRB Motives Catalog |
| `(:PoliceDisposal)` | Police chargesheet & pendency | `POLICE-68420A` | NCRB Table 18A.4 |
| `(:CourtOutcome)` | Judicial trial convictions/acquittals | `COURT-41200B` | NCRB Table 18A.5 |
| `(:CrimeStatistic)` | Demographics & arrest counts | `ARREST-34210C` | NCRB Table 18A.6 |

### B. Investigation Domain
| Label | Description | Stable Deterministic ID Format | Mandatory Metadata |
| :--- | :--- | :--- | :--- |
| `(:Case)` | Authorized police case docket | `case:CASE-2024-DEL-0891` | `case_id`, `police_station`, `fir_number` |
| `(:Evidence)` | Certified digital/physical asset | `evidence:EV-2024-DEL-0891-01` | `sha256`, `seizure_memo`, `custody_officer` |
| `(:Person)` | Suspect, witness, or person of interest | `person:<normalized_id_hash>` | `confidence`, `verification_status`, `kyc_doc` |
| `(:Organization)` | Shell entity or front company | `organization:<cin_or_name_hash>` | `cin`, `pan`, `incorporation_source` |
| `(:Phone)` | Cellular MSISDN / SIM card | `phone:<e164_hash>` | `caf_provider`, `subpoena_ref` |
| `(:Email)` | Electronic mail address | `email:<normalized_email>` | `header_trace`, `provider_subpoena` |
| `(:IPAddress)` | IPv4 / IPv6 network address | `ip:<normalized_ip>` | `isp`, `ipdr_subpoena`, `asn` |
| `(:Domain)` | FQDN or landing page | `domain:<normalized_fqdn>` | `whois_registrar`, `dns_a_record` |
| `(:Device)` | Hardware, IMEI, or VoIP gateway | `device:<hardware_hash>` | `imei`, `mac_address`, `cfsl_report` |
| `(:BankAccount)` | Banking or escrow repository | `bank:<account_hash>` | `ifsc`, `masked_account`, `1930_freeze_id` |
| `(:Transaction)` | Financial transfer or crypto hop | `transaction:<utr_or_txid>` | `amount_inr`, `utr_number`, `timestamp` |
| `(:Location)` | Physical raid site or cell tower | `location:<geo_hash>` | `coordinates`, `jurisdiction`, `address` |
| `(:MLPrediction)` | Machine learning inference node | `prediction:PRED-<id>` | `model_name`, `artifact_sha256`, `prediction` |

---

## 3. Relationship Semantics & Provenance Matrix

Every relational edge in the investigation graph carries strict forensic provenance:

```text
(Case)-[:CONTAINS {confidence: 1.0, doc: "FIR-2024-DEL-0891"}]->(Evidence)
  │
  ├─[:REFERENCES]->(IPAddress)
  ├─[:REFERENCES]->(Domain)
  └─[:REFERENCES]->(BankAccount)

(Person)-[:USES {confidence: 0.95, doc: "CAF Subpoena"}]->(Phone)
(Person)-[:USES {confidence: 0.94, doc: "Asterisk Log"}]->(Device)
(Person)-[:OWNS {confidence: 0.99, doc: "Bank Mandate"}]->(BankAccount)
(Person)-[:ASSOCIATED_WITH {confidence: 0.96, doc: "MCA Portal"}]->(Organization)
(Person)-[:APPEARS_IN {confidence: 0.98, doc: "FIR Docket"}]->(Case)
(Person)-[:COMMUNICATED_WITH {confidence: 0.92, doc: "CDR Dialing Log"}]->(Person)
(Organization)-[:TRANSFERRED_TO {confidence: 0.98, doc: "Wire Escrow"}]->(BankAccount)
(Evidence)-[:ANALYZED_BY {confidence: 1.0, doc: "Model Registry"}]->(MLPrediction)
```

---

## 4. Stable Entity Resolution & Deterministic IDs

Entities use collision-resistant identifiers derived from normalized properties:

| Entity Type | Resolution Formula | Example Normalized Identifier |
| :--- | :--- | :--- |
| **IPAddress** | `f"ip:{ip.strip().lower()}"` | `ip:103.145.22.18` |
| **Domain** | `f"domain:{fqdn.strip().lower()}"` | `domain:support-helpdesk-msft.com` |
| **Email** | `f"email:{email.strip().lower()}"` | `email:billing@techglobalsupport.com` |
| **Phone** | `f"phone:{sha256(e164)[:10]}"` | `phone:9a88bf0122` |
| **BankAccount** | `f"bank:{sha256(account)[:10]}"` | `bank:1849ad0912` |
| **Person** | `f"person:{sha256(aadhaar_or_kyc)[:10]}"` | `person:ad1f990310` |

### Alias Resolution Rules
- Textual variations (e.g. `"R. Kumar"`, `"Raj Kumar"`, `"Rajesh Kumar"`) remain **separate unresolved entities** until biometric, PAN, or CAF corroboration resolves them into a unified identifier.
- Explicit resolution states:
  - `VERIFIED`: Confirmed by official subpoena, KYC, or physical seizure.
  - `PROBABLE`: Supported by multi-source probabilistic linkage.
  - `UNRESOLVED`: Single uncorroborated mention.

---

## 5. Ethical Graph Centrality & Role Analytics

> [!IMPORTANT]
> Graph centrality indicates topological structural positioning, NOT criminal guilt or legal liability.

| Algorithm | Topological Meaning | Ethical Terminology Used | Prohibited Terminology |
| :--- | :--- | :--- | :--- |
| **Betweenness Centrality** | Quantifies information brokerage along shortest paths. | `"Network bridge"` / `"Structural broker"` | `Kingpin`, `Mastermind`, `Boss` |
| **PageRank Centrality** | Measures recursive relational density & incoming links. | `"High-centrality entity"` / `"Focal node"` | `Gang leader`, `Crime chief` |
| **Degree Centrality** | Quantifies total immediate direct connections. | `"Structural hub"` / `"High-degree node"` | `Cartel commander` |

---

## 6. Multi-Hop Traversal & Shortest Path Engine

- **Traversal Control**: Multi-hop neighborhood expansion is strictly capped at `1` to `4` hops (`default: 2`) via `GET /api/graph/entities/{entity_id}/neighbors?hops=2` to prevent unbounded subgraph expansion.
- **Shortest Path Analysis**: `POST /api/graph/path` executes Dijkstra / BFS pathfinding, returning the sequence of intermediate nodes, relationship types, and supporting Section 65B evidence citations for every edge.
- **Negative Path Safety**: If no verified path exists between two entities, the API returns:
  ```json
  {
    "found": false,
    "reason": "No verified path exists in the available graph.",
    "source_entity_id": "ip:103.145.22.18",
    "target_entity_id": "nonexistent_entity_xyz"
  }
  ```

---

## 7. Edge Explainability Protocol ("Why Does This Edge Exist?")

Investigative usability requires immediate explainability for any relational link:

```json
{
  "relationship_id": "REL-person:ad1f990310-organization:b06dede7da",
  "relationship_type": "ASSOCIATED_WITH",
  "source_id": "person:ad1f990310",
  "target_id": "organization:b06dede7da",
  "explanation": {
    "source_document": "MCA Shareholding Ledger / CIN U72900DL2021PTC381920",
    "source_evidence_id": "CASE-2024-DEL-0891",
    "observed_at": "2024-03-16T15:30:00Z",
    "confidence": 0.96,
    "verification_status": "VERIFIED",
    "detail": "100% Shareholder / Managing Director"
  },
  "provenance": "Cryptographically auditable evidence edge under Indian Evidence Act §65B."
}
```

---

## 8. Verified API Endpoints

| Endpoint | Method | Parameter Scope | Description |
| :--- | :---: | :--- | :--- |
| `/api/graph/cases/{case_id}` | `GET` | `case_id` | Isolated evidence subgraph for a police case file. |
| `/api/graph/entities/{entity_id}` | `GET` | `entity_id` | Full entity attributes, confidence, and KYC provenance. |
| `/api/graph/entities/{entity_id}/neighbors` | `GET` | `hops` (1–4) | Controlled ego-network expansion. |
| `/api/graph/entities/{entity_id}/subgraph` | `GET` | `entity_id` | Connected component containing the focal entity. |
| `/api/graph/path` | `POST` / `GET` | `source_id`, `target_id`, `max_hops` | Shortest path with edge evidence linkage. |
| `/api/graph/search` | `GET` | `q`, `entity_type`, `case_id`, `min_confidence` | Multi-dimensional filtered entity search. |
| `/api/graph/statistics` | `GET` | None | Real-time counts, verified edges, and structural centralities. |
| `/api/graph/relationships/{id}/explain` | `GET` | `relationship_id` | Forensic edge explainability. |

---

## 9. Security & Chain of Custody

1. **Section 65B Cryptographic Hashes**: All evidence artifacts maintain SHA-256 bitstream checksums.
2. **Access Control & Masking**: Sensitive identifiers (bank account numbers, phone numbers) are masked in general responses (`XXXX-XXXX-0192`) and unmasked only in authorized case reports.
3. **Audit Logged**: Every graph expansion and path search is recorded in the immutable audit log with officer user IDs (`X-User-ID: IN-BOSE-4417`).
