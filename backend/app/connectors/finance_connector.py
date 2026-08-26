import re
from typing import List, Tuple
from .base import BaseConnector
from ..models.entity import Entity, EntityMetadata, EntityType
from ..models.relationship import Relationship, RelationshipMetadata, RelationshipType
from ..models.ingestion import FinanceIngestPayload, FinanceRecord


def sanitize_account(acc: str) -> str:
    return re.sub(r"[\s-]", "", acc.strip().upper())


class FinanceConnector(BaseConnector):
    """Connector for Banking transactions, Hawala routing, and UPI payment ledgers."""

    @property
    def source_name(self) -> str:
        return "Banking-FIU-Ledger"

    async def parse_and_extract(
        self, payload: FinanceIngestPayload
    ) -> Tuple[List[Entity], List[Relationship]]:
        entities_map = {}
        relationships = []
        case_ref = payload.caseReference or "FIN-INTEL"

        for rec in payload.transactions:
            sender_clean = sanitize_account(rec.sender_account)
            receiver_clean = sanitize_account(rec.receiver_account)

            sender_id = f"ACC-{abs(hash(sender_clean)) % 1000000:06d}"
            receiver_id = f"ACC-{abs(hash(receiver_clean)) % 1000000:06d}"

            # Calculate risk based on transaction volume
            risk_score = 75 if rec.amount > 500000 else 55

            # 1. Sender Bank Account Entity
            if sender_id not in entities_map:
                s_name = rec.sender_name or f"Account {sender_clean[-4:]}"
                entities_map[sender_id] = Entity(
                    id=sender_id,
                    name=s_name,
                    type=EntityType.ACCOUNT,
                    source=self.source_name,
                    confidence=0.99,
                    riskScore=risk_score,
                    metadata=EntityMetadata(
                        alias=s_name,
                        role="Originating Account",
                        bank=rec.bank,
                        accountNumber=sender_clean,
                        subtitle=f"{rec.bank} · {sender_clean}",
                        details=[
                            ("Institution", rec.bank),
                            ("Account Identifier", sender_clean),
                            ("Type", "Remitter Node"),
                        ],
                    ),
                )

            # 2. Receiver Bank Account Entity
            if receiver_id not in entities_map:
                r_name = rec.receiver_name or f"Account {receiver_clean[-4:]}"
                entities_map[receiver_id] = Entity(
                    id=receiver_id,
                    name=r_name,
                    type=EntityType.ACCOUNT,
                    source=self.source_name,
                    confidence=0.99,
                    riskScore=risk_score,
                    metadata=EntityMetadata(
                        alias=r_name,
                        role="Beneficiary Account",
                        bank=rec.bank,
                        accountNumber=receiver_clean,
                        subtitle=f"Beneficiary Account · {receiver_clean}",
                        details=[
                            ("Destination Account", receiver_clean),
                            ("Type", "Beneficiary Node"),
                        ],
                    ),
                )

            # 3. TRANSACTION Link between Accounts
            rel_id = f"REL-FIN-{abs(hash(f'{sender_id}_{receiver_id}_{rec.timestamp}_{rec.amount}')) % 1000000:06d}"
            tx_weight = min(10, max(2, int(rec.amount / 100000) + 2))

            relationships.append(
                Relationship(
                    id=rel_id,
                    sourceId=sender_id,
                    targetId=receiver_id,
                    type=RelationshipType.TRANSACTION,
                    confidence=0.98,
                    sourceReference=case_ref,
                    metadata=RelationshipMetadata(
                        label=f"{rec.transaction_type} INR {rec.amount:,.0f}",
                        weight=tx_weight,
                        detail=f"{rec.transaction_type} transfer of INR {rec.amount:,.2f} on {rec.timestamp}",
                        amount=rec.amount,
                        bank=rec.bank,
                        sourceReference=case_ref,
                    ),
                )
            )

        return list(entities_map.values()), relationships
