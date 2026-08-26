from typing import List, Tuple
from .base import BaseConnector
from ..models.entity import Entity, EntityMetadata, EntityType
from ..models.relationship import Relationship, RelationshipMetadata, RelationshipType
from ..models.ingestion import DigitalEvidencePayload


class EvidenceConnector(BaseConnector):
    """Connector for Digital Forensic Exhibits and Cryptographic Chain of Custody."""

    @property
    def source_name(self) -> str:
        return "Digital-Evidence-Vault"

    async def parse_and_extract(
        self, payload: DigitalEvidencePayload
    ) -> Tuple[List[Entity], List[Relationship]]:
        entities = []
        relationships = []
        exhibit_id = payload.exhibit_id or f"EV-{abs(hash(payload.hash_sha256)) % 10000:04d}"
        case_ref = payload.case_reference

        # 1. Device or Evidence Artifact Node
        ent_type = EntityType.DEVICE if payload.device_model else EntityType.ORGANIZATION
        if payload.file_type in ["Audio", "Video", "Document", "Image", "Data"]:
            ent_type = EntityType.ORGANIZATION

        artifact_id = f"ART-{abs(hash(payload.hash_sha256)) % 1000000:06d}"
        entities.append(
            Entity(
                id=artifact_id,
                name=payload.file_name,
                type=ent_type,
                source=self.source_name,
                confidence=0.99,
                riskScore=70,
                metadata=EntityMetadata(
                    role=f"Forensic Exhibit ({payload.file_type})",
                    status=payload.custody_status or "VERIFIED",
                    location=payload.seizure_location or "Evidence Lockup",
                    subtitle=f"{exhibit_id} · SHA-256 Verified",
                    details=[
                        ("Exhibit Tag", exhibit_id),
                        ("SHA-256 Digest", f"{payload.hash_sha256[:16]}..."),
                        ("Case Anchor", case_ref),
                        ("Custodian", payload.officer_in_charge or "Lead Officer"),
                    ],
                ),
            )
        )

        # 2. Extract linked Domain or IP if provided in metadata
        if payload.domain:
            domain_id = f"DOM-{abs(hash(payload.domain)) % 1000000:06d}"
            entities.append(
                Entity(
                    id=domain_id,
                    name=payload.domain,
                    type=EntityType.DOMAIN,
                    source=self.source_name,
                    confidence=0.98,
                    riskScore=80,
                    metadata=EntityMetadata(
                        role="Investigated Domain",
                        subtitle=f"Domain Artifact · {payload.domain}",
                        details=[
                            ("Domain Name", payload.domain),
                            ("Exhibit Reference", exhibit_id),
                        ],
                    ),
                )
            )

            relationships.append(
                Relationship(
                    id=f"REL-EV-DOM-{abs(hash(f'{artifact_id}_{domain_id}')) % 1000000:06d}",
                    sourceId=artifact_id,
                    targetId=domain_id,
                    type=RelationshipType.ASSOCIATED_WITH,
                    confidence=0.98,
                    sourceReference=case_ref,
                    metadata=RelationshipMetadata(
                        label="EXTRACTED_FROM",
                        weight=8,
                        detail=f"Domain {payload.domain} extracted from exhibit {payload.file_name}",
                        sourceReference=case_ref,
                    ),
                )
            )

        if payload.ip_address:
            ip_id = f"IP-{abs(hash(payload.ip_address)) % 1000000:06d}"
            entities.append(
                Entity(
                    id=ip_id,
                    name=payload.ip_address,
                    type=EntityType.IP_ADDRESS,
                    source=self.source_name,
                    confidence=0.98,
                    riskScore=75,
                    metadata=EntityMetadata(
                        role="Evidence IP",
                        ip=payload.ip_address,
                        subtitle=f"Forensic IP · {payload.ip_address}",
                    ),
                )
            )

            relationships.append(
                Relationship(
                    id=f"REL-EV-IP-{abs(hash(f'{artifact_id}_{ip_id}')) % 1000000:06d}",
                    sourceId=artifact_id,
                    targetId=ip_id,
                    type=RelationshipType.LOCATED_AT,
                    confidence=0.95,
                    sourceReference=case_ref,
                    metadata=RelationshipMetadata(
                        label="NETWORK_CONNECTION",
                        weight=7,
                        detail=f"IP {payload.ip_address} recorded in forensic artifact",
                        sourceReference=case_ref,
                    ),
                )
            )

        return entities, relationships
