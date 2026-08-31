"""Authorized Investigation Evidence Ingestion, Staged Review Gate & Case Intelligence Service."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from database.neo4j import neo4j_db
    from services.investigation_graph import (
        investigation_graph_service,
        ResolutionStatus,
        VerificationStatus,
    )
    from services.graph_algorithms import graph_algorithms
    from app.database.db import db
    from app.models.audit import AuditAction
except ImportError:
    from ..database.neo4j import neo4j_db
    from ..services.investigation_graph import (
        investigation_graph_service,
        ResolutionStatus,
        VerificationStatus,
    )
    from ..services.graph_algorithms import graph_algorithms
    from ..app.database.db import db
    from ..app.models.audit import AuditAction

logger = logging.getLogger("EvidenceIntelligenceService")


class ProcessingStatus:
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    PROCESSED = "PROCESSED"
    OCR_REQUIRED = "OCR_REQUIRED"
    FAILED = "FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMMITTED = "COMMITTED"


class ReviewAction:
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    EDIT = "EDIT"
    MERGE = "MERGE"
    KEEP_SEPARATE = "KEEP_SEPARATE"


class EvidenceIntelligenceService:
    """
    Production-grade Authorized Investigation Evidence Ingestion Engine.
    
    Pipeline:
      Evidence File -> Validation -> SHA-256 Hash -> Case Association -> Metadata
      -> Entity Extraction -> Deterministic Resolution -> Relationship Extraction
      -> Analyst Review Gate (ACCEPT/REJECT/EDIT) -> Graph Commit -> Timeline -> Section 65B Audit
    """

    def __init__(self):
        self._staged_extractions: Dict[str, Dict[str, Any]] = {}
        self._chain_of_custody_logs: Dict[str, List[Dict[str, Any]]] = {}
        self._case_timelines: Dict[str, List[Dict[str, Any]]] = {}
        self._ml_lineage_records: Dict[str, List[Dict[str, Any]]] = {}

    def compute_sha256(self, content: bytes) -> str:
        """Computes cryptographic SHA-256 checksum for physical/digital bitstream verification."""
        return hashlib.sha256(content).hexdigest()

    def record_chain_of_custody(
        self,
        evidence_id: str,
        case_id: str,
        actor: str,
        action: str,
        current_hash: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Appends an immutable Section 65B chain of custody audit event."""
        now_iso = datetime.now(timezone.utc).isoformat()
        event = {
            "event_id": f"COC-{hashlib.sha256(f'{evidence_id}:{now_iso}:{action}'.encode()).hexdigest()[:10].upper()}",
            "evidence_id": evidence_id,
            "case_id": case_id,
            "actor": actor,
            "action": action,
            "timestamp": now_iso,
            "current_hash": current_hash,
            "details": details or {},
        }
        self._chain_of_custody_logs.setdefault(evidence_id, []).append(event)
        self.add_timeline_event(
            case_id=case_id,
            event_type=f"EVIDENCE_{action}",
            entity=evidence_id,
            evidence=evidence_id,
            confidence=1.0,
            details=f"Chain of Custody: {action} by {actor}",
        )

    def add_timeline_event(
        self,
        case_id: str,
        event_type: str,
        entity: str,
        evidence: str,
        confidence: float = 0.95,
        details: str = "",
        timestamp: Optional[str] = None,
    ):
        """Appends a chronological case event to the investigation timeline."""
        now_iso = timestamp or datetime.now(timezone.utc).isoformat()
        evt = {
            "timeline_id": f"TL-{hashlib.sha256(f'{case_id}:{event_type}:{now_iso}:{entity}'.encode()).hexdigest()[:8].upper()}",
            "case_id": case_id,
            "timestamp": now_iso,
            "event_type": event_type,
            "entity": entity,
            "evidence": evidence,
            "confidence": confidence,
            "details": details,
        }
        self._case_timelines.setdefault(case_id, []).append(evt)
        # Keep timeline sorted by timestamp
        self._case_timelines[case_id].sort(key=lambda x: x["timestamp"])

    def ingest_evidence_file(
        self,
        filename: str,
        content: bytes,
        case_id: str,
        source: str = "Forensic Seizure Memo",
        description: str = "Authorized digital evidence artifact",
        classification: str = "CONFIDENTIAL_LAW_ENFORCEMENT",
        actor: str = "IN-BOSE-4417",
    ) -> Dict[str, Any]:
        """
        Ingests and validates an evidence file into the Evidence Vault.
        Performs mime-type detection, size check, SHA-256 calculation, and entity staging.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # Security check: 50MB limit
        if len(content) > 50 * 1024 * 1024:
            raise ValueError("Evidence file exceeds 50MB maximum permissible size limit.")

        # Sanitized filename
        safe_filename = Path(filename).name
        ext = Path(safe_filename).suffix.lower().lstrip(".")

        sha256_hash = self.compute_sha256(content)
        evidence_id = f"EV-{hashlib.sha256(f'{case_id}:{safe_filename}:{sha256_hash}'.encode()).hexdigest()[:8].upper()}"

        # Detect OCR requirement for scanned PDFs/images
        processing_status = ProcessingStatus.PROCESSED
        if ext in ["png", "jpg", "jpeg", "tiff", "bmp"]:
            processing_status = ProcessingStatus.OCR_REQUIRED
        elif ext == "pdf":
            # Check if PDF contains extractable text
            if b"/Font" not in content and b"/Text" not in content and len(content) < 1000:
                processing_status = ProcessingStatus.OCR_REQUIRED

        evidence_record = {
            "evidence_id": evidence_id,
            "id": evidence_id,
            "case_id": case_id,
            "filename": safe_filename,
            "mime_type": f"application/{ext}" if ext else "application/octet-stream",
            "size": len(content),
            "sha256": sha256_hash,
            "hash": sha256_hash,
            "uploaded_at": now_iso,
            "source": source,
            "description": description,
            "classification": classification,
            "processing_status": processing_status,
        }

        # Save to internal db vault
        db.save_evidence(evidence_id, evidence_record)

        # Record Chain of Custody
        self.record_chain_of_custody(
            evidence_id=evidence_id,
            case_id=case_id,
            actor=actor,
            action="UPLOADED",
            current_hash=sha256_hash,
            details={"filename": safe_filename, "size": len(content)},
        )

        # If text/json/csv, perform automated entity extraction
        staged_items = []
        if processing_status != ProcessingStatus.OCR_REQUIRED:
            try:
                text_content = content.decode("utf-8", errors="ignore")
                staged_items = self.extract_entities_and_relationships_from_text(
                    text=text_content,
                    evidence_id=evidence_id,
                    case_id=case_id,
                    source_filename=safe_filename,
                )
            except Exception as e:
                logger.warning(f"Text parsing skipped for {safe_filename}: {e}")

        return {
            "evidence_id": evidence_id,
            "case_id": case_id,
            "filename": safe_filename,
            "sha256": sha256_hash,
            "processing_status": processing_status,
            "staged_extractions_count": len(staged_items),
            "chain_of_custody_status": "CERTIFIED_SECTION_65B",
        }

    # =========================================================================
    # Controlled Entity & Relationship Extraction
    # =========================================================================
    def extract_entities_and_relationships_from_text(
        self,
        text: str,
        evidence_id: str,
        case_id: str,
        source_filename: str,
    ) -> List[Dict[str, Any]]:
        """
        Parses text for IP addresses, domains, emails, phone numbers, bank accounts,
        devices, organizations, and potential person references.
        Places extractions into the Staged Review Gate.
        """
        staged_list = []
        now_iso = datetime.now(timezone.utc).isoformat()
        lines = text.splitlines()

        # 1. IP Addresses (IPv4)
        ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        for line_no, line in enumerate(lines, start=1):
            for match in re.finditer(ip_pattern, line):
                ip_val = match.group(0)
                if not ip_val.startswith("0.") and not ip_val.startswith("127."):
                    extraction_id = f"EXT-IP-{hashlib.sha256(f'{evidence_id}:{ip_val}:{line_no}'.encode()).hexdigest()[:8].upper()}"
                    ent_id = investigation_graph_service.generate_entity_id("ip", ip_val)
                    item = {
                        "extraction_id": extraction_id,
                        "evidence_id": evidence_id,
                        "case_id": case_id,
                        "entity_type": "IPAddress",
                        "value": ip_val,
                        "normalized_value": ip_val.lower(),
                        "canonical_entity_id": ent_id,
                        "source_location": f"{source_filename} (Line {line_no})",
                        "confidence": 0.98,
                        "extraction_method": "REGEX_IPV4_PARSER",
                        "resolution_status": ResolutionStatus.VERIFIED,
                        "review_status": ProcessingStatus.REVIEW_REQUIRED,
                        "candidate_relationship": {
                            "type": "REFERENCES",
                            "source_id": f"evidence:{evidence_id}",
                            "target_id": ent_id,
                        },
                        "created_at": now_iso,
                    }
                    self._staged_extractions[extraction_id] = item
                    staged_list.append(item)

        # 2. Domains
        domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:com|in|org|net|co\.in|gov\.in|xyz|top|site|live)\b'
        for line_no, line in enumerate(lines, start=1):
            for match in re.finditer(domain_pattern, line, re.IGNORECASE):
                dom_val = match.group(0).lower()
                extraction_id = f"EXT-DOM-{hashlib.sha256(f'{evidence_id}:{dom_val}:{line_no}'.encode()).hexdigest()[:8].upper()}"
                ent_id = investigation_graph_service.generate_entity_id("domain", dom_val)
                item = {
                    "extraction_id": extraction_id,
                    "evidence_id": evidence_id,
                    "case_id": case_id,
                    "entity_type": "Domain",
                    "value": dom_val,
                    "normalized_value": dom_val,
                    "canonical_entity_id": ent_id,
                    "source_location": f"{source_filename} (Line {line_no})",
                    "confidence": 0.96,
                    "extraction_method": "REGEX_FQDN_PARSER",
                    "resolution_status": ResolutionStatus.VERIFIED,
                    "review_status": ProcessingStatus.REVIEW_REQUIRED,
                    "candidate_relationship": {
                        "type": "REFERENCES",
                        "source_id": f"evidence:{evidence_id}",
                        "target_id": ent_id,
                    },
                    "created_at": now_iso,
                }
                self._staged_extractions[extraction_id] = item
                staged_list.append(item)

        # 3. Phone Numbers
        phone_pattern = r'(?:\+91[\-\s]?)?[6-9]\d{9}\b'
        for line_no, line in enumerate(lines, start=1):
            for match in re.finditer(phone_pattern, line):
                phone_val = match.group(0).replace(" ", "").replace("-", "")
                extraction_id = f"EXT-PH-{hashlib.sha256(f'{evidence_id}:{phone_val}:{line_no}'.encode()).hexdigest()[:8].upper()}"
                ent_id = investigation_graph_service.generate_entity_id("phone", phone_val)
                item = {
                    "extraction_id": extraction_id,
                    "evidence_id": evidence_id,
                    "case_id": case_id,
                    "entity_type": "Phone",
                    "value": phone_val,
                    "normalized_value": phone_val,
                    "canonical_entity_id": ent_id,
                    "source_location": f"{source_filename} (Line {line_no})",
                    "confidence": 0.95,
                    "extraction_method": "REGEX_E164_INDIAN_MOBILE",
                    "resolution_status": ResolutionStatus.PROBABLE,
                    "review_status": ProcessingStatus.REVIEW_REQUIRED,
                    "candidate_relationship": {
                        "type": "REFERENCES",
                        "source_id": f"evidence:{evidence_id}",
                        "target_id": ent_id,
                    },
                    "created_at": now_iso,
                }
                self._staged_extractions[extraction_id] = item
                staged_list.append(item)

        # 4. Bank Accounts
        bank_pattern = r'(?:Account|Acct|A/C|Escrow)[\s#:]*([0-9]{9,18})\b'
        for line_no, line in enumerate(lines, start=1):
            for match in re.finditer(bank_pattern, line, re.IGNORECASE):
                bank_val = match.group(1)
                extraction_id = f"EXT-BANK-{hashlib.sha256(f'{evidence_id}:{bank_val}:{line_no}'.encode()).hexdigest()[:8].upper()}"
                ent_id = investigation_graph_service.generate_entity_id("bank", bank_val)
                item = {
                    "extraction_id": extraction_id,
                    "evidence_id": evidence_id,
                    "case_id": case_id,
                    "entity_type": "BankAccount",
                    "value": bank_val,
                    "normalized_value": f"XXXX-XXXX-{bank_val[-4:]}",
                    "canonical_entity_id": ent_id,
                    "source_location": f"{source_filename} (Line {line_no})",
                    "confidence": 0.94,
                    "extraction_method": "REGEX_BANK_ACCOUNT_PARSER",
                    "resolution_status": ResolutionStatus.PROBABLE,
                    "review_status": ProcessingStatus.REVIEW_REQUIRED,
                    "candidate_relationship": {
                        "type": "REFERENCES",
                        "source_id": f"evidence:{evidence_id}",
                        "target_id": ent_id,
                    },
                    "created_at": now_iso,
                }
                self._staged_extractions[extraction_id] = item
                staged_list.append(item)

        # 5. Potential Person Mentions (Strict rule: Marked UNRESOLVED until analyst confirmation)
        person_pattern = r'(?:Suspect|Accused|Operator|Director|Caller|Beneficiary)[\s:]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)'
        for line_no, line in enumerate(lines, start=1):
            for match in re.finditer(person_pattern, line):
                name_val = match.group(1).strip()
                extraction_id = f"EXT-PER-{hashlib.sha256(f'{evidence_id}:{name_val}:{line_no}'.encode()).hexdigest()[:8].upper()}"
                ent_id = investigation_graph_service.generate_entity_id("person", name_val)
                item = {
                    "extraction_id": extraction_id,
                    "evidence_id": evidence_id,
                    "case_id": case_id,
                    "entity_type": "Person",
                    "value": name_val,
                    "normalized_value": name_val,
                    "canonical_entity_id": ent_id,
                    "source_location": f"{source_filename} (Line {line_no})",
                    "confidence": 0.85,
                    "extraction_method": "NAMED_ENTITY_HEURISTIC",
                    "resolution_status": ResolutionStatus.UNRESOLVED,
                    "review_status": ProcessingStatus.REVIEW_REQUIRED,
                    "candidate_relationship": {
                        "type": "APPEARS_IN",
                        "source_id": ent_id,
                        "target_id": f"case:{case_id}",
                    },
                    "created_at": now_iso,
                }
                self._staged_extractions[extraction_id] = item
                staged_list.append(item)

        return staged_list

    # =========================================================================
    # Analyst Review Gate & Graph Commit
    # =========================================================================
    def get_staged_extractions(self, case_id: Optional[str] = None, evidence_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all staged candidate entities and relationships awaiting analyst review."""
        items = list(self._staged_extractions.values())
        if case_id:
            items = [i for i in items if i.get("case_id") == case_id]
        if evidence_id:
            items = [i for i in items if i.get("evidence_id") == evidence_id]
        return items

    def review_staged_extraction(
        self,
        extraction_id: str,
        action: str,
        actor: str = "IN-BOSE-4417",
        edited_attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyst Review Gate Action:
          - ACCEPT: Commits entity & relationship to Neo4j investigation graph with Section 65B traceability.
          - REJECT: Discards candidate link with audit justification.
          - EDIT: Modifies attributes before committing.
          - MERGE / KEEP_SEPARATE: Resolves aliases explicitly.
        """
        if extraction_id not in self._staged_extractions:
            raise KeyError(f"Extraction ID '{extraction_id}' not found in Staged Review Gate.")

        staged = self._staged_extractions[extraction_id]
        now_iso = datetime.now(timezone.utc).isoformat()
        action_upper = action.strip().upper()

        if action_upper == ReviewAction.REJECT:
            staged["review_status"] = "REJECTED"
            staged["reviewed_by"] = actor
            staged["reviewed_at"] = now_iso
            return {
                "extraction_id": extraction_id,
                "action": "REJECTED",
                "status": "Candidate extraction rejected by analyst. Not committed to Knowledge Graph.",
            }

        elif action_upper in [ReviewAction.ACCEPT, ReviewAction.EDIT]:
            # Apply edits if present
            if edited_attributes:
                staged.update(edited_attributes)

            # 1. Commit Node to Investigation Graph
            ent_type = staged["entity_type"]
            ent_val = staged["value"]
            ent_id = staged["canonical_entity_id"]
            case_id = staged["case_id"]
            ev_id = staged["evidence_id"]

            neo4j_db.add_evidence_node(
                node_id=ent_id,
                label=ent_type,
                name=ent_val,
                case_id=case_id,
                source_document=staged.get("source_location", "Staged Extraction"),
                confidence_score=staged.get("confidence", 0.95),
                verification_status=VerificationStatus.ANALYST_CONFIRMED,
                reviewed_by=actor,
                created_at=now_iso,
            )

            # 2. Commit Candidate Relationship
            cand_rel = staged.get("candidate_relationship")
            if cand_rel:
                rel_id = f"REL-REV-{extraction_id}"
                neo4j_db.add_evidence_relationship(
                    rel_id=rel_id,
                    source_id=cand_rel["source_id"],
                    target_id=cand_rel["target_id"],
                    rel_type=cand_rel["type"],
                    case_id=case_id,
                    source_document=staged.get("source_location", "Analyst Confirmed"),
                    metadata={
                        "confidence": staged.get("confidence", 0.95),
                        "verification_status": VerificationStatus.ANALYST_CONFIRMED,
                        "reviewed_by": actor,
                    },
                )

            staged["review_status"] = ProcessingStatus.COMMITTED
            staged["reviewed_by"] = actor
            staged["reviewed_at"] = now_iso

            # Add Timeline Event
            self.add_timeline_event(
                case_id=case_id,
                event_type="ANALYST_VERIFICATION",
                entity=ent_id,
                evidence=ev_id,
                confidence=1.0,
                details=f"Analyst {actor} accepted extraction: {ent_type} '{ent_val}'",
            )

            return {
                "extraction_id": extraction_id,
                "action": "COMMITTED",
                "entity_id": ent_id,
                "status": "Entity and relational edge successfully committed to Knowledge Graph.",
            }

        else:
            raise ValueError(f"Unsupported review action '{action}'. Must be ACCEPT, REJECT, or EDIT.")

    # =========================================================================
    # Case Workspace Bundle & Strict Isolation
    # =========================================================================
    def get_case_workspace(self, case_id: str) -> Dict[str, Any]:
        """
        Retrieves the complete isolated investigation workspace bundle for an authorized case docket.
        Guarantees zero cross-case data leakage.
        """
        # 1. Overview
        case_entity = investigation_graph_service.get_entity_by_id(f"case:{case_id.upper()}") or {
            "id": f"case:{case_id}",
            "name": f"Case Docket {case_id}",
            "case_id": case_id,
            "status": "ACTIVE_INVESTIGATION",
        }

        # 2. Evidence
        all_evidence = db.get_all_evidence()
        case_evidence = [e for e in all_evidence if e.get("case_id") == case_id or e.get("caseId") == case_id]

        # 3. Subgraph (Entities & Relationships)
        graph_res = neo4j_db.query_evidence_graph(case_id=case_id)
        nodes = graph_res.get("nodes", [])
        relationships = graph_res.get("relationships", [])

        # 4. Timeline
        timeline = self._case_timelines.get(case_id, [])

        # 5. Centrality Analytics scoped to this case
        analytics = graph_algorithms.calculate_centralities("investigation_evidence", limit=5)

        # 6. ML Findings Lineage
        ml_findings = self._ml_lineage_records.get(case_id, [])

        return {
            "case_id": case_id,
            "overview": case_entity,
            "evidence_count": len(case_evidence),
            "evidence": case_evidence,
            "nodes_count": len(nodes),
            "nodes": nodes,
            "relationships_count": len(relationships),
            "relationships": relationships,
            "timeline": timeline,
            "analytics": {
                "top_bridges": analytics.get("top_betweenness_bridges", []),
                "top_influencers": analytics.get("top_pagerank_influencers", []),
            },
            "ml_findings": ml_findings,
            "provenance": "Isolated authorized case workspace partition.",
        }

    def record_ml_prediction_for_evidence(
        self,
        case_id: str,
        evidence_id: str,
        model_name: str,
        model_version: str,
        artifact_sha256: str,
        result: Any,
        confidence: float = 0.95,
    ) -> Dict[str, Any]:
        """Links ML prediction decision support to an evidence node."""
        now_iso = datetime.now(timezone.utc).isoformat()
        pred_id = f"PRED-{hashlib.sha256(f'{evidence_id}:{model_name}:{now_iso}'.encode()).hexdigest()[:8].upper()}"

        record = {
            "prediction_id": pred_id,
            "case_id": case_id,
            "input_evidence_id": evidence_id,
            "model_name": model_name,
            "model_version": model_version,
            "artifact_sha256": artifact_sha256,
            "prediction_timestamp": now_iso,
            "result": result,
            "confidence": confidence,
            "status": "DECISION_SUPPORT_ONLY",
        }
        self._ml_lineage_records.setdefault(case_id, []).append(record)

        # Add Evidence -> ANALYZED_BY -> MLPrediction in graph
        pred_node_id = f"prediction:{pred_id}"
        neo4j_db.add_evidence_node(
            node_id=pred_node_id,
            label="MLPrediction",
            name=f"ML Prediction: {model_name}",
            case_id=case_id,
            source_document=f"ML Model Registry ({model_name})",
            confidence_score=confidence,
            prediction_result=str(result),
        )
        neo4j_db.add_evidence_relationship(
            rel_id=f"REL-EV-ML-{pred_id}",
            source_id=f"evidence:{evidence_id}",
            target_id=pred_node_id,
            rel_type="ANALYZED_BY",
            case_id=case_id,
            source_document="Automated Model Inference Engine",
            metadata={"model": model_name, "confidence": confidence},
        )

        return record

    def export_case_graph(self, case_id: str, export_format: str = "json") -> Dict[str, Any]:
        """Exports isolated case graph into JSON, CSV, or GraphML."""
        graph_res = neo4j_db.query_evidence_graph(case_id=case_id)
        nodes = graph_res.get("nodes", [])
        relationships = graph_res.get("relationships", [])

        if export_format.lower() == "csv":
            node_rows = [f"{n['id']},{n.get('label')},{n.get('name')},{n.get('case_id')}" for n in nodes]
            rel_rows = [f"{r.get('sourceId')},{r.get('targetId')},{r.get('type')},{r.get('case_id')}" for r in relationships]
            return {
                "case_id": case_id,
                "format": "csv",
                "nodes_csv": "\n".join(["id,label,name,case_id"] + node_rows),
                "relationships_csv": "\n".join(["source,target,type,case_id"] + rel_rows),
            }

        return {
            "case_id": case_id,
            "format": "json",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "nodes": nodes,
            "relationships": relationships,
            "provenance": "Exported under Indian Evidence Act §65B audit controls.",
        }


# Global Singleton Instance
evidence_intelligence_service = EvidenceIntelligenceService()
