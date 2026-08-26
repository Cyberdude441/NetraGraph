from typing import List, Tuple
from .base import BaseConnector
from ..models.entity import Entity, EntityMetadata, EntityType
from ..models.relationship import Relationship, RelationshipMetadata, RelationshipType
from ..models.ingestion import CyberComplaintPayload


class CyberConnector(BaseConnector):
    """Connector for National Cyber Crime Reporting Portal complaints and digital forensic intakes."""

    @property
    def source_name(self) -> str:
        return "National-Cyber-Portal"

    async def parse_and_extract(
        self, payload: CyberComplaintPayload
    ) -> Tuple[List[Entity], List[Relationship]]:
        entities = []
        relationships = []
        comp_id = payload.complaint_id

        # 1. Victim Person Node
        victim_id = f"VIC-{abs(hash(payload.victim)) % 1000000:06d}"
        entities.append(
            Entity(
                id=victim_id,
                name=payload.victim,
                type=EntityType.PERSON,
                source=self.source_name,
                confidence=0.99,
                riskScore=20,
                metadata=EntityMetadata(
                    role="Complainant / Victim",
                    status="Protected Witness",
                    subtitle=f"Victim ({payload.attack_type})",
                    details=[
                        ("Complaint Reference", comp_id),
                        ("Incident Classification", payload.attack_type),
                        ("Reported Date", payload.date),
                        ("Financial Loss", f"INR {payload.loss_amount:,.2f}" if payload.loss_amount else "None"),
                    ],
                ),
            )
        )

        # 2. Malicious IP Node (if present)
        if payload.ip_address:
            ip_id = f"IP-{abs(hash(payload.ip_address)) % 1000000:06d}"
            entities.append(
                Entity(
                    id=ip_id,
                    name=payload.ip_address,
                    type=EntityType.IP_ADDRESS,
                    source=self.source_name,
                    confidence=0.96,
                    riskScore=85,
                    metadata=EntityMetadata(
                        role="Attacker IP / Proxy",
                        ip=payload.ip_address,
                        subtitle=f"Malicious Origin · {payload.ip_address}",
                        details=[
                            ("IP Address", payload.ip_address),
                            ("Attack Vector", payload.attack_type),
                            ("Flagged in Complaint", comp_id),
                        ],
                    ),
                )
            )

            # Link Victim -> IP (LOGIN or COMMUNICATED_WITH)
            rel_ip_id = f"REL-CYBER-IP-{abs(hash(f'{victim_id}_{ip_id}_{comp_id}')) % 1000000:06d}"
            relationships.append(
                Relationship(
                    id=rel_ip_id,
                    sourceId=victim_id,
                    targetId=ip_id,
                    type=RelationshipType.COMMUNICATED_WITH,
                    confidence=0.92,
                    sourceReference=comp_id,
                    metadata=RelationshipMetadata(
                        label=f"{payload.attack_type} Origin",
                        weight=7,
                        detail=f"Victim targeted from IP {payload.ip_address}",
                        ipAddress=payload.ip_address,
                        sourceReference=comp_id,
                    ),
                )
            )

        # 3. Suspect Bank Account (if present)
        if payload.suspect_account:
            acc_clean = payload.suspect_account.strip().upper()
            acc_id = f"ACC-{abs(hash(acc_clean)) % 1000000:06d}"
            entities.append(
                Entity(
                    id=acc_id,
                    name=f"Suspect Account {acc_clean[-4:]}",
                    type=EntityType.ACCOUNT,
                    source=self.source_name,
                    confidence=0.97,
                    riskScore=90,
                    metadata=EntityMetadata(
                        role="Mule / Fraud Account",
                        accountNumber=acc_clean,
                        subtitle=f"Suspect Account · {acc_clean}",
                        details=[
                            ("Account Number", acc_clean),
                            ("Fraud Report", comp_id),
                            ("Status", "Freeze Recommended"),
                        ],
                    ),
                )
            )

            # Link Victim -> Suspect Account (TRANSACTION)
            rel_tx_id = f"REL-CYBER-TX-{abs(hash(f'{victim_id}_{acc_id}_{comp_id}')) % 1000000:06d}"
            relationships.append(
                Relationship(
                    id=rel_tx_id,
                    sourceId=victim_id,
                    targetId=acc_id,
                    type=RelationshipType.TRANSACTION,
                    confidence=0.98,
                    sourceReference=comp_id,
                    metadata=RelationshipMetadata(
                        label=f"Fraud Loss INR {payload.loss_amount:,.0f}" if payload.loss_amount else "Fraud Diversion",
                        weight=9,
                        detail=f"Reported financial siphoning of INR {payload.loss_amount:,.2f}",
                        amount=payload.loss_amount,
                        sourceReference=comp_id,
                    ),
                )
            )

        # 4. Suspect Phone (if present)
        if payload.suspect_phone:
            ph_clean = payload.suspect_phone.strip()
            ph_id = f"PH-{abs(hash(ph_clean)) % 1000000:06d}"
            entities.append(
                Entity(
                    id=ph_id,
                    name=ph_clean,
                    type=EntityType.PHONE,
                    source=self.source_name,
                    confidence=0.95,
                    riskScore=88,
                    metadata=EntityMetadata(
                        role="Caller / Impersonator",
                        subtitle=f"Cyber Fraud Line · {ph_clean}",
                        details=[
                            ("Fraud MSISDN", ph_clean),
                            ("Linked Complaint", comp_id),
                        ],
                    ),
                )
            )

            # Link Victim -> Suspect Phone (CALL / COMMUNICATED_WITH)
            rel_ph_id = f"REL-CYBER-PH-{abs(hash(f'{victim_id}_{ph_id}_{comp_id}')) % 1000000:06d}"
            relationships.append(
                Relationship(
                    id=rel_ph_id,
                    sourceId=victim_id,
                    targetId=ph_id,
                    type=RelationshipType.CALL,
                    confidence=0.95,
                    sourceReference=comp_id,
                    metadata=RelationshipMetadata(
                        label="Phishing Call / SMS",
                        weight=8,
                        detail=f"Victim contacted by suspect on {ph_clean}",
                        sourceReference=comp_id,
                    ),
                )
            )

        return entities, relationships
