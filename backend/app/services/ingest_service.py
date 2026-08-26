import hashlib
from typing import List
from ..models.ingest import IngestRequest, IngestResponse
from ..ai.entity_extractor import extractor
from ..database.db import db
from ..graph.network_manager import graph_manager


class IngestService:
    """Service to process unstructured crime reports and update Knowledge Graph."""

    def process_ingest(self, req: IngestRequest) -> IngestResponse:
        # Calculate SHA-256 Checksum for chain of custody
        sha256 = hashlib.sha256(req.rawText.encode("utf-8")).hexdigest()
        doc_id = f"EV-{sha256[:4].upper()}"

        # Run AI entity extraction
        extracted_entities, extracted_relationships = extractor.extract_from_text(
            req.rawText, case_id=req.caseId or "CS-2291"
        )

        # Save to DB and update Graph
        for entity in extracted_entities:
            db.save_entity(entity)
            graph_manager.add_entity_node(entity)

        for rel in extracted_relationships:
            db.save_relationship(rel)
            graph_manager.add_relationship_edge(rel)

        # Document record in database
        db.save_document_record(doc_id, {
            "title": req.documentTitle,
            "hash": sha256,
            "officerId": req.officerId,
            "entitiesExtracted": len(extracted_entities),
            "relationshipsExtracted": len(extracted_relationships),
        })

        risk_alerts: List[str] = []
        for e in extracted_entities:
            if e.riskScore >= 85:
                risk_alerts.append(f"High risk entity extracted: {e.name} (Risk: {e.riskScore})")

        return IngestResponse(
            documentId=doc_id,
            sha256Hash=sha256,
            extractedEntities=extracted_entities,
            extractedRelationships=extracted_relationships,
            ingestedCount=len(extracted_entities),
            riskAlerts=risk_alerts,
            summary=f"Processed '{req.documentTitle}' successfully. Extracted {len(extracted_entities)} entities and {len(extracted_relationships)} verified relationships.",
            status="PROCESSED_AND_INDEXED",
        )


ingest_service = IngestService()
