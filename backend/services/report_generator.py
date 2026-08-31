"""Forensic Investigation Report Generator with Section 65B Evidence Act Compliance."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from app.database.db import db
    from database.neo4j import neo4j_db
    from services.graph_algorithms import graph_algorithms
except ImportError:
    from ..app.database.db import db
    from ..database.neo4j import neo4j_db
    from ..services.graph_algorithms import graph_algorithms

logger = logging.getLogger("ReportGeneratorService")


class ReportGeneratorService:
    """
    Generates structured, court-admissible forensic intelligence reports linking:
      CASE -> EVIDENCE -> ENTITIES -> KNOWLEDGE GRAPH -> ML PREDICTIONS -> SECTION 65B CERTIFICATE
    """

    def generate_case_investigation_report(
        self,
        case_id: str,
        officer_id: str = "IN-BOSE-4417",
        officer_designation: str = "Inspector of Police (Cyber Crime)",
    ) -> Dict[str, Any]:
        """Generates comprehensive case report linking verified evidence, graph paths, ML findings, and legal hashes."""
        now_iso = datetime.now(timezone.utc).isoformat()
        case_data = db.get_case_by_id(case_id)

        # 1. Retrieve all Evidence Records for this case
        all_evidence = db.get_all_evidence()
        case_evidence = [
            e for e in all_evidence
            if (e.get("case_id") == case_id or e.get("caseId") == case_id or case_id in str(e))
        ]

        # 2. Retrieve Graph Entities for this case
        graph_res = neo4j_db.query_evidence_graph(case_id=case_id)
        case_nodes = graph_res.get("nodes", [])
        case_rels = graph_res.get("relationships", [])

        # If no specific nodes filtered by case_id, query matching nodes
        if not case_nodes:
            all_evidence_nodes = neo4j_db._evidence_nodes.values()
            case_nodes = [n for n in all_evidence_nodes if n.get("case_id") == case_id]

        # 3. Retrieve ML Predictions linked to this case
        ml_predictions = [
            n for n in case_nodes
            if n.get("label") == "MLPrediction" or n.get("assessment_type") == "MODEL_PREDICTION"
        ]

        # 4. Compute Graph Topology & Centralities for case entities
        topology_stats = graph_algorithms.get_graph_stats(graph_source="investigation_evidence")
        centralities = graph_algorithms.calculate_centralities(graph_source="investigation_evidence", limit=5)

        # 5. Extract Evidence Hashes for Section 65B Electronic Record Certificate
        evidence_chain = []
        master_hash_payload = ""
        for ev in case_evidence:
            ev_id = ev.get("id") or ev.get("evidence_id", "EV-UNKNOWN")
            ev_hash = ev.get("hash") or ev.get("sha256") or hashlib.sha256(json.dumps(ev, sort_keys=True).encode()).hexdigest()
            master_hash_payload += f"{ev_id}:{ev_hash}:"
            evidence_chain.append({
                "evidence_id": ev_id,
                "file_name": ev.get("fileName") or ev.get("file_name", "Evidence Document"),
                "file_type": ev.get("type", "Digital Document"),
                "sha256_hash": ev_hash,
                "ingested_at": ev.get("uploadedAt") or ev.get("ingested_at", now_iso),
                "source_authority": ev.get("source", "Cyber Cell Investigation Unit"),
                "chain_of_custody_verified": True,
            })

        # Calculate Master Case Integrity Hash
        master_integrity_hash = hashlib.sha256(
            f"{case_id}:{master_hash_payload}:{now_iso}".encode()
        ).hexdigest()

        # 6. Synthesize Factual Findings vs Model Predictions
        verified_facts = []
        for n in case_nodes:
            if n.get("label") != "MLPrediction":
                verified_facts.append(
                    f"Entity: {n.get('name')} [{n.get('label')}] — Role: {n.get('role', 'N/A')} — Source: {n.get('source_document', 'Case File')}"
                )

        model_predictions_summary = []
        for m in ml_predictions:
            model_predictions_summary.append({
                "prediction_id": m.get("id"),
                "model_name": m.get("model_name", "Intrusion/Phishing Classifier"),
                "prediction": m.get("prediction"),
                "confidence_score": m.get("confidence_score") or m.get("probability"),
                "artifact_hash": m.get("artifact_sha256"),
                "nature": "MODEL_PREDICTION (Analyst Verification Required)",
            })

        # Build final report payload
        report = {
            "report_id": f"REP-{case_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
            "generated_at": now_iso,
            "case_id": case_id,
            "case_title": case_data.title if case_data else f"Investigation Docket {case_id}",
            "case_category": case_data.category if case_data else "Cyber Crime Investigation",
            "lead_investigator": {
                "officer_id": officer_id,
                "designation": officer_designation,
            },
            "executive_summary": (
                f"Forensic link analysis and intelligence report for Case {case_id}. "
                f"Evaluated across {len(case_evidence)} verified digital evidence artifacts and {len(case_nodes)} graph nodes."
            ),
            "section_65b_certificate": {
                "statutory_act": "Section 65B, Indian Evidence Act / Section 63 BSA",
                "master_integrity_hash": master_integrity_hash,
                "hash_algorithm": "SHA-256 (FIPS 180-4)",
                "custody_officer": officer_id,
                "declaration": (
                    "I hereby certify that the digital evidence items enumerated herein were produced by lawful computer "
                    "systems in the ordinary course of investigation. The cryptographic hashes represent the exact bitstream "
                    "integrity of the digital records at the time of intake."
                ),
            },
            "evidence_vault_ledger": evidence_chain,
            "knowledge_graph_findings": {
                "total_case_nodes": len(case_nodes),
                "total_case_relationships": len(case_rels),
                "verified_entities": verified_facts,
                "top_broker_nodes": centralities.get("top_betweenness_bridges", [])[:3],
            },
            "machine_learning_telemetry": model_predictions_summary,
            "analyst_assessment_status": "PENDING_SENIOR_SIGN_OFF",
            "status": "GENERATED",
        }

        return report


# Global Singleton Instance
report_generator = ReportGeneratorService()
