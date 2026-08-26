import re
import uuid
from typing import List, Tuple
from .base import BaseConnector
from ..models.entity import Entity, EntityMetadata, EntityType
from ..models.relationship import Relationship, RelationshipMetadata, RelationshipType
from ..models.ingestion import CDRIngestPayload, CDRRecord


def sanitize_phone(phone_str: str) -> str:
    """Normalize phone numbers to standard E.164-like clean string."""
    cleaned = re.sub(r"[^\d+]", "", phone_str.strip())
    if not cleaned.startswith("+") and len(cleaned) == 10:
        cleaned = "+91" + cleaned
    return cleaned


class CDRConnector(BaseConnector):
    """Connector for telecom Call Detail Records (CDR) from Lawful Interception Gateways."""

    @property
    def source_name(self) -> str:
        return "Telecom-CDR-Gateway"

    async def parse_and_extract(
        self, payload: CDRIngestPayload
    ) -> Tuple[List[Entity], List[Relationship]]:
        entities_map = {}
        relationships = []
        case_ref = payload.caseReference or "CDR-INTEL"

        for idx, rec in enumerate(payload.records):
            caller_clean = sanitize_phone(rec.caller_number)
            receiver_clean = sanitize_phone(rec.receiver_number)

            caller_id = f"PH-{abs(hash(caller_clean)) % 1000000:06d}"
            receiver_id = f"PH-{abs(hash(receiver_clean)) % 1000000:06d}"

            # 1. Caller Phone Entity
            if caller_id not in entities_map:
                caller_name = rec.caller_name or f"Subscriber {caller_clean[-4:]}"
                entities_map[caller_id] = Entity(
                    id=caller_id,
                    name=caller_clean,
                    type=EntityType.PHONE,
                    source=self.source_name,
                    confidence=0.98,
                    riskScore=65,
                    metadata=EntityMetadata(
                        alias=caller_name,
                        role="Calling Party (A)",
                        location=rec.tower_location or "Cell Tower Grid",
                        imei=rec.imei,
                        imsi=rec.imsi,
                        subtitle=f"CDR Node · {caller_name}",
                        details=[
                            ("Normalized MSISDN", caller_clean),
                            ("Last BTS Tower", rec.tower_location or "Unknown"),
                            ("IMEI", rec.imei or "N/A"),
                        ],
                    ),
                )

            # 2. Receiver Phone Entity
            if receiver_id not in entities_map:
                receiver_name = rec.receiver_name or f"Subscriber {receiver_clean[-4:]}"
                entities_map[receiver_id] = Entity(
                    id=receiver_id,
                    name=receiver_clean,
                    type=EntityType.PHONE,
                    source=self.source_name,
                    confidence=0.98,
                    riskScore=60,
                    metadata=EntityMetadata(
                        alias=receiver_name,
                        role="Called Party (B)",
                        location=rec.tower_location or "Cell Tower Grid",
                        imei=rec.imei,
                        imsi=rec.imsi,
                        subtitle=f"CDR Node · {receiver_name}",
                        details=[
                            ("Normalized MSISDN", receiver_clean),
                            ("Associated BTS", rec.tower_location or "Unknown"),
                        ],
                    ),
                )

            # 3. CALL Link between Caller and Receiver
            rel_id = f"REL-CDR-{abs(hash(f'{caller_id}_{receiver_id}_{rec.timestamp}')) % 1000000:06d}"
            call_weight = min(10, max(1, int(rec.duration / 30) + 1))

            relationships.append(
                Relationship(
                    id=rel_id,
                    sourceId=caller_id,
                    targetId=receiver_id,
                    type=RelationshipType.CALL,
                    confidence=0.95,
                    sourceReference=case_ref,
                    metadata=RelationshipMetadata(
                        label="CALL",
                        weight=call_weight,
                        detail=f"{rec.duration}s call via {rec.tower_location or 'BTS'}",
                        duration=rec.duration,
                        towerLocation=rec.tower_location,
                        sourceReference=case_ref,
                    ),
                )
            )

        return list(entities_map.values()), relationships
