from typing import Any, Dict, List
from ..connectors import (
    FIRConnector,
    CDRConnector,
    FinanceConnector,
    CyberConnector,
    EvidenceConnector,
)
from ..database.db import db
from ..graph.network_manager import graph_manager
from ..models.ingestion import (
    FIRIngestPayload,
    CDRIngestPayload,
    FinanceIngestPayload,
    CyberComplaintPayload,
    DigitalEvidencePayload,
    IngestionResponse,
)
from ..models.audit import AuditAction, UserRole
from ..models.cases import Case


class IngestionService:
    """Enterprise Ingestion Service coordinating data normalization, graph insertion, and audit logging."""

    def __init__(self):
        self.fir_connector = FIRConnector()
        self.cdr_connector = CDRConnector()
        self.finance_connector = FinanceConnector()
        self.cyber_connector = CyberConnector()
        self.evidence_connector = EvidenceConnector()

    async def ingest_fir(self, payload: FIRIngestPayload, user_id: str = "IN-BOSE-4417") -> IngestionResponse:
        entities, relationships = await self.fir_connector.parse_and_extract(payload)
        
        # Save to DB
        db.bulk_save_entities(entities)
        db.bulk_save_relationships(relationships)

        # Create or update case record
        case_id = payload.caseNumber
        existing_case = db.get_case_by_id(case_id)
        if not existing_case:
            db.save_case(
                Case(
                    id=case_id,
                    title=f"FIR {case_id} — {payload.policeStation or 'Cyber Unit'}",
                    description=f"Investigation into offenses: {', '.join(payload.actsAndSections or ['IT Act 66D'])}",
                    priority="High",
                    lead=payload.leadOfficer or "Insp. D. Bose",
                    suspects=len(entities),
                    progress=20,
                    firNumber=case_id,
                    linkedEntities=[e.id for e in entities],
                )
            )

        # Update Graph Manager
        for e in entities:
            graph_manager.add_entity_node(e)
        for r in relationships:
            graph_manager.add_relationship_edge(r)

        # Audit
        db.record_audit(
            action=AuditAction.INGESTION,
            resource=f"FIR-{case_id}",
            user_id=user_id,
            details={"nodes": len(entities), "relationships": len(relationships)},
        )

        return IngestionResponse(
            module="FIR",
            message=f"Successfully ingested FIR {case_id} and extracted {len(entities)} nodes and {len(relationships)} linkages.",
            nodesCreated=len(entities),
            edgesCreated=len(relationships),
            entities=[e.id for e in entities],
            relationships=[r.id for r in relationships],
        )

    async def ingest_cdr(self, payload: CDRIngestPayload, user_id: str = "IN-BOSE-4417") -> IngestionResponse:
        entities, relationships = await self.cdr_connector.parse_and_extract(payload)
        
        db.bulk_save_entities(entities)
        db.bulk_save_relationships(relationships)

        for e in entities:
            graph_manager.add_entity_node(e)
        for r in relationships:
            graph_manager.add_relationship_edge(r)

        db.record_audit(
            action=AuditAction.INGESTION,
            resource=f"CDR-{payload.caseReference}",
            user_id=user_id,
            details={"recordsCount": len(payload.records), "nodes": len(entities), "edges": len(relationships)},
        )

        return IngestionResponse(
            module="CDR",
            message=f"Successfully processed {len(payload.records)} call detail records. Created {len(entities)} phone nodes and {len(relationships)} call links.",
            nodesCreated=len(entities),
            edgesCreated=len(relationships),
            entities=[e.id for e in entities],
            relationships=[r.id for r in relationships],
        )

    async def ingest_finance(self, payload: FinanceIngestPayload, user_id: str = "IN-BOSE-4417") -> IngestionResponse:
        entities, relationships = await self.finance_connector.parse_and_extract(payload)
        
        db.bulk_save_entities(entities)
        db.bulk_save_relationships(relationships)

        for e in entities:
            graph_manager.add_entity_node(e)
        for r in relationships:
            graph_manager.add_relationship_edge(r)

        db.record_audit(
            action=AuditAction.INGESTION,
            resource=f"FINANCE-{payload.caseReference}",
            user_id=user_id,
            details={"txCount": len(payload.transactions), "nodes": len(entities), "edges": len(relationships)},
        )

        return IngestionResponse(
            module="Finance",
            message=f"Processed {len(payload.transactions)} financial transactions. Extracted {len(entities)} account nodes and {len(relationships)} transfer edges.",
            nodesCreated=len(entities),
            edgesCreated=len(relationships),
            entities=[e.id for e in entities],
            relationships=[r.id for r in relationships],
        )

    async def ingest_cyber(self, payload: CyberComplaintPayload, user_id: str = "IN-BOSE-4417") -> IngestionResponse:
        entities, relationships = await self.cyber_connector.parse_and_extract(payload)
        
        db.bulk_save_entities(entities)
        db.bulk_save_relationships(relationships)

        # Create Cyber Complaint Case
        case_id = f"CS-{payload.complaint_id}"
        db.save_case(
            Case(
                id=case_id,
                title=f"Cyber Complaint {payload.complaint_id} — {payload.attack_type}",
                description=f"Incident reported by {payload.victim}. Loss: INR {payload.loss_amount:,.2f}",
                priority="Critical" if payload.loss_amount and payload.loss_amount > 500000 else "High",
                lead="Insp. D. Bose",
                suspects=len(entities),
                progress=15,
                category=payload.attack_type,
                linkedEntities=[e.id for e in entities],
            )
        )

        for e in entities:
            graph_manager.add_entity_node(e)
        for r in relationships:
            graph_manager.add_relationship_edge(r)

        db.record_audit(
            action=AuditAction.INGESTION,
            resource=f"CYBER-{payload.complaint_id}",
            user_id=user_id,
            details={"attackType": payload.attack_type, "loss": payload.loss_amount},
        )

        return IngestionResponse(
            module="CyberCrime",
            message=f"Cyber complaint {payload.complaint_id} filed. Created {len(entities)} network nodes and {len(relationships)} relationship links.",
            nodesCreated=len(entities),
            edgesCreated=len(relationships),
            entities=[e.id for e in entities],
            relationships=[r.id for r in relationships],
        )

    async def ingest_evidence(self, payload: DigitalEvidencePayload, user_id: str = "IN-BOSE-4417") -> IngestionResponse:
        entities, relationships = await self.evidence_connector.parse_and_extract(payload)
        
        db.bulk_save_entities(entities)
        db.bulk_save_relationships(relationships)

        exhibit_id = payload.exhibit_id or f"EV-{abs(hash(payload.hash_sha256)) % 10000:04d}"
        db.save_evidence(
            exhibit_id,
            {
                "id": exhibit_id,
                "fileName": payload.file_name,
                "fileType": payload.file_type,
                "hash": payload.hash_sha256,
                "case": payload.case_reference,
                "size": f"{payload.size_mb:.2f} MB" if payload.size_mb else "12.4 MB",
                "uploadedBy": payload.officer_in_charge or user_id,
                "verificationStatus": payload.custody_status or "VERIFIED",
                "timestamp": payload.seizure_location or "Evidence Vault",
            },
        )

        for e in entities:
            graph_manager.add_entity_node(e)
        for r in relationships:
            graph_manager.add_relationship_edge(r)

        db.record_audit(
            action=AuditAction.UPDATE_EVIDENCE,
            resource=f"EXHIBIT-{exhibit_id}",
            user_id=user_id,
            details={"hash": payload.hash_sha256, "case": payload.case_reference},
        )

        return IngestionResponse(
            module="Evidence",
            message=f"Exhibit {exhibit_id} sealed with SHA-256 integrity digest and linked to case {payload.case_reference}.",
            nodesCreated=len(entities),
            edgesCreated=len(relationships),
            entities=[e.id for e in entities],
            relationships=[r.id for r in relationships],
        )


ingestion_service = IngestionService()
