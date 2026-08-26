import re
import hashlib
import random
from typing import List, Tuple
from ..models.entity import Entity, EntityType, EntityMetadata
from ..models.relationship import Relationship, RelationshipType, RelationshipMetadata


class AIEntityExtractor:
    """Rule-based & Pattern NLP Entity Extraction Pipeline for Crime Ingestion."""

    # Regex patterns for intelligence entities
    PHONE_REGEX = re.compile(r'(?:\+91[\-\s]?)?[6789]\d{9}\b')
    IMEI_REGEX = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
    VEHICLE_REGEX = re.compile(r'\b[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}\b')
    BANK_REGEX = re.compile(r'\b(?:A\/C|Account|Acc)\s*(?:No\.?)?\s*([A-Za-z0-9\*]{6,16})\b', re.IGNORECASE)
    AMOUNT_REGEX = re.compile(r'(?:₹|Rs\.?|INR)\s*([\d\.]+\s*(?:Cr|Lakh|Crore|K|M)?)', re.IGNORECASE)
    PERSON_ALIAS_REGEX = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*(?:\(alias\s*[“"]?([^”"]+)[”"]?\))?', re.IGNORECASE)

    def extract_from_text(self, text: str, case_id: str = "CS-2291") -> Tuple[List[Entity], List[Relationship]]:
        """Extract structured entities and inferred relationships from unstructured text."""
        extracted_entities: List[Entity] = []
        extracted_relationships: List[Relationship] = []
        seen_names = set()

        # 1. Extract Phone Numbers
        phones = self.PHONE_REGEX.findall(text)
        for phone in phones:
            clean_phone = phone.strip()
            if clean_phone not in seen_names:
                seen_names.add(clean_phone)
                phone_id = f"PH-{hashlib.md5(clean_phone.encode()).hexdigest()[:4].upper()}"
                extracted_entities.append(
                    Entity(
                        id=phone_id,
                        name=clean_phone,
                        type=EntityType.PHONE,
                        riskScore=random.randint(65, 85),
                        metadata=EntityMetadata(
                            role="Suspect Handset",
                            status="Active",
                            network="Ghost Ledger",
                            subtitle=f"Extracted from {case_id} report",
                        ),
                    )
                )

        # 2. Extract Vehicles
        vehicles = self.VEHICLE_REGEX.findall(text)
        for veh in vehicles:
            if veh not in seen_names:
                seen_names.add(veh)
                veh_id = f"VEH-{hashlib.md5(veh.encode()).hexdigest()[:4].upper()}"
                extracted_entities.append(
                    Entity(
                        id=veh_id,
                        name=f"{veh} (Flagged Vehicle)",
                        type=EntityType.VEHICLE,
                        riskScore=random.randint(60, 78),
                        metadata=EntityMetadata(
                            role="Transit Vehicle",
                            status="Flagged",
                            location="Checkpoint Intercept",
                        ),
                    )
                )

        # 3. Extract Bank Accounts
        banks = self.BANK_REGEX.findall(text)
        for bank in banks:
            if bank not in seen_names:
                seen_names.add(bank)
                bank_id = f"BANK-{hashlib.md5(bank.encode()).hexdigest()[:4].upper()}"
                extracted_entities.append(
                    Entity(
                        id=bank_id,
                        name=f"A/C {bank}",
                        type=EntityType.BANK_ACCOUNT,
                        riskScore=random.randint(75, 95),
                        metadata=EntityMetadata(
                            role="Transaction Node",
                            status="Flagged",
                            subtitle="Layered funding account",
                        ),
                    )
                )

        # 4. Extract Named Persons
        for match in self.PERSON_ALIAS_REGEX.finditer(text):
            full_name = match.group(1).strip()
            alias = match.group(2) if match.group(2) else None
            # Filter common words
            if full_name.lower() in ["the accused", "police station", "high risk", "district court", "criminal network"]:
                continue
            if full_name not in seen_names:
                seen_names.add(full_name)
                p_id = f"NG-{hashlib.md5(full_name.encode()).hexdigest()[:4].upper()}"
                extracted_entities.append(
                    Entity(
                        id=p_id,
                        name=full_name,
                        type=EntityType.PERSON,
                        riskScore=random.randint(70, 92),
                        metadata=EntityMetadata(
                            alias=alias,
                            role="Investigative Subject",
                            status="Under Surveillance",
                            network="Ghost Ledger",
                            offenses=["Financial fraud", "Conspiracy"],
                        ),
                    )
                )

        # 5. Inferred Relationships between extracted entities
        if len(extracted_entities) >= 2:
            for i in range(len(extracted_entities) - 1):
                src = extracted_entities[i]
                tgt = extracted_entities[i + 1]

                rel_type = RelationshipType.ASSOCIATED_WITH
                if src.type == EntityType.PERSON and tgt.type == EntityType.PHONE:
                    rel_type = RelationshipType.CALLS
                elif src.type == EntityType.PERSON and tgt.type == EntityType.BANK_ACCOUNT:
                    rel_type = RelationshipType.TRANSACTS
                elif src.type == EntityType.PERSON and tgt.type == EntityType.VEHICLE:
                    rel_type = RelationshipType.LOCATED_AT

                rel_id = f"REL-{hashlib.md5(f'{src.id}-{tgt.id}'.encode()).hexdigest()[:4].upper()}"
                extracted_relationships.append(
                    Relationship(
                        id=rel_id,
                        sourceId=src.id,
                        targetId=tgt.id,
                        type=rel_type,
                        confidence=0.88,
                        metadata=RelationshipMetadata(
                            weight=random.randint(5, 9),
                            label=rel_type.value.lower(),
                            detail=f"Inferred co-occurrence in {case_id}",
                        ),
                    )
                )

        return extracted_entities, extracted_relationships


extractor = AIEntityExtractor()
