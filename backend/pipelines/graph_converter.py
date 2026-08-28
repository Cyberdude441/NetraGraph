from typing import Dict, Iterable, List

from app.models.cyber_intelligence import (
    CyberEntity,
    CyberRelationship,
    CyberRelationshipType,
)


def build_relationships(entities: Iterable[CyberEntity], dataset: str, record_id: str) -> List[CyberRelationship]:
    items = list(entities)
    relationships: List[CyberRelationship] = []
    for index, source in enumerate(items):
        for target in items[index + 1 :]:
            rel_type = CyberRelationshipType.RELATED_TO
            pair = {source.type.value, target.type.value}
            if "URL" in pair and "Domain" in pair:
                rel_type = CyberRelationshipType.HOSTED
            elif "IPAddress" in pair and "Domain" in pair:
                rel_type = CyberRelationshipType.CONNECTED_TO
            elif "EmailAddress" in pair and "Domain" in pair:
                rel_type = CyberRelationshipType.SENT_FROM
            elif "Vulnerability" in pair and "Malware" in pair:
                rel_type = CyberRelationshipType.RELATED_TO
            elif "AttackType" in pair:
                rel_type = CyberRelationshipType.TARGETED
            relationships.append(
                CyberRelationship(
                    id=f"CYBER-REL-{dataset}-{record_id}-{index}",
                    source_id=source.id,
                    target_id=target.id,
                    type=rel_type,
                    confidence=min(source.confidence, target.confidence),
                    source_dataset=dataset,
                    source_record_id=record_id,
                    attributes={"builder": "co-occurrence"},
                )
            )
    return relationships
