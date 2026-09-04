# NetraGraph Phase 15: Threat Intelligence / OSINT Fusion with Provenance

## Architectural Overview

NetraGraph Phase 15 introduces an isolated, forensic-grade external threat intelligence (CTI) and open-source intelligence (OSINT) ingestion, correlation, and lineage engine. It enables investigators to correlate case entities (IPs, Domains, Hashes, Phones, Accounts) against verified external cyber threat telemetry while strictly maintaining chain-of-custody, multi-dimensional confidence, and decision-support boundaries.

---

## Mandatory Governance & Legal Disclaimer

> **IMPORTANT REGULATORY & FORENSIC NOTICE:**  
> External threat intelligence and OSINT are analytical decision-support inputs. They do not constitute definitive proof of culpability, criminal intent, or guilt under law. Correlations represent technical associations between indicators and external threat reports; they must be independently validated by certified investigative officers against direct evidentiary records.

---

## Core Architectural Invariants

1. **Option C + D + E Graph Safety Strategy:**
   - **C (Evidence-Only Representation):** External CTI is indexed in an isolated data store (`domain_tag: EXTERNAL_THREAT_INTEL`) and attached to cases as supplementary evidence records.
   - **D (Temporal Annotation):** Correlated matches emit non-causal timeline markers into Phase 14 Investigation Timeline & Graph Replay.
   - **E (Human Review Gate):** External indicators **NEVER** mutate the authoritative knowledge graph or create criminal/syndicate membership edges automatically. Graph enrichment requires explicit `ACCEPTED` review from an authorized investigator.
2. **Multi-Dimensional Confidence Independence:**
   - The 6 confidence dimensions (`source_reliability`, `content_confidence`, `extraction_confidence`, `entity_match_confidence`, `temporal_confidence`, and `threat_relevance`) are preserved independently.
   - NetraGraph strictly prohibits silently collapsing these dimensions into a single lossy scalar in persistent storage or analytical records.
3. **Immutable Observations (Zero Overwriting):**
   - Ingested intelligence is append-only.
   - If Source A reports an indicator as `MALICIOUS` and Source B reports it as `BENIGN`, both raw observations are preserved in full with their cryptographic SHA-256 payload checksums.
4. **Deterministic Identity Generation:**
   - Primary identifiers are computed using canonical SHA-256 hashing. Random UUIDs are strictly prohibited as primary keys.
   - Provenance identities incorporate microsecond timestamps, source record IDs, batch sequence indices, and payload hashes to guarantee collision resistance even for multiple observations within the same second.
5. **Zero Database Schema Changes:**
   - Phase 15 operates entirely in-memory with existing case workspace structures, existing Postgres models, and existing Neo4j nodes. No database migrations or DDL changes are introduced.

---

## The 6-Dimensional Confidence Profile

| Dimension | Range | Description |
|---|---|---|
| `source_reliability` | `[0.0, 1.0]` | Institutional trustworthiness of the reporting source (e.g. CERT-In = 0.95, unverified forum = 0.30). |
| `content_confidence` | `[0.0, 1.0]` | The reporting source's self-asserted confidence in the indicator's malice. |
| `extraction_confidence`| `[0.0, 1.0]` | Fidelity of the extraction parser (1.0 for regex, 0.70 for NLP). |
| `entity_match_confidence` | `[0.0, 1.0]` | Match fidelity between case entity and external indicator (1.0 for exact, 0.85 for CIDR/phone, 0.65 for alias). |
| `temporal_confidence` | `[0.0, 1.0]` | Exponential decay multiplier accounting for time elapsed since last observed. None if timestamp absent. |
| `threat_relevance` | `[0.0, 1.0]` | Effective operational threat score combining baseline reputation and temporal decay. |

---

## Source Trust Tiers

- **Tier 1 (CERT & Law Enforcement):** CERT-In, NCTX, NCIIPC, Interpol Cyber. Default reliability: `0.95`.
- **Tier 2 (Established Security Providers):** VirusTotal, AbuseIPDB, OpenPhish. Default reliability: `0.85`.
- **Tier 3 (Commercial Threat Feeds):** Commercial threat telemetry feeds. Default reliability: `0.80`.
- **Tier 4 (Community OSINT):** AlienVault OTX Community, URLhaus, ThreatFox. Default reliability: `0.65`.
- **Tier 5 (Unverified Feeds):** Paste sites, darknet dumps, scraping. Default reliability: `0.30`.

---

## Subsystem Integration

- **Threat Fusion (`backend/ml/threat_fusion/`):**
  - Consumes external CTI via the existing `SignalSource.EXTERNAL` enum.
  - Phase 15 constructs compliant `ThreatSignal` adapters preserving the full 6-dimensional breakdown in `metadata`.
  - Zero modifications to Threat Fusion scoring rules or weights.
- **Phase 13 Emerging Threat Engine (`backend/ml/emerging_threat/`):**
  - Receives supplementary external CTI context without modifying topological early-warning algorithms.
- **Phase 14 Investigation Timeline (`backend/ml/investigation_timeline/`):**
  - Generates `InvestigationTimelineEvent` instances with `TimelineEventType.THREAT_FUSION_SIGNAL` and `ProvenanceType.CORRELATED`.

---

## Safety & Resource Bounds

- Maximum payload size: **10 MB**
- Maximum indicators per batch: **5,000**
- Maximum candidate entities correlated: **1,000**
- Maximum correlation results returned: **200**
- Maximum provenance traversal depth: **10**
- Maximum execution timeout: **5.0 seconds**
- Telemetry: Low-cardinality endpoint normalization via `normalize_endpoint`.
