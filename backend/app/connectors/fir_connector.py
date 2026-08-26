import re
from typing import List, Tuple
from .base import BaseConnector
from ..models.entity import Entity, EntityMetadata, EntityType
from ..models.relationship import Relationship, RelationshipMetadata, RelationshipType
from ..models.ingestion import FIRIngestPayload


class FIRConnector(BaseConnector):
    """Connector for First Information Reports (FIR) and Law Enforcement Case Dossiers."""

    @property
    def source_name(self) -> str:
        return "State-Crime-Records-FIR"

    async def parse_and_extract(
        self, payload: FIRIngestPayload
    ) -> Tuple[List[Entity], List[Relationship]]:
        entities = []
        relationships = []
        fir_no = payload.caseNumber

        # 1. Primary Organization / Police Station Node
        ps_name = payload.policeStation or "Cyber Crime Police Station"
        ps_id = f"ORG-{abs(hash(ps_name)) % 1000000:06d}"
        entities.append(
            Entity(
                id=ps_id,
                name=ps_name,
                type=EntityType.ORGANIZATION,
                source=self.source_name,
                confidence=1.0,
                riskScore=10,
                metadata=EntityMetadata(
                    role="Law Enforcement Jurisdiction",
                    subtitle=f"Jurisdiction · {ps_name}",
                    details=[
                        ("Station", ps_name),
                        ("FIR No", fir_no),
                        ("Officer", payload.leadOfficer or "Assigned"),
                    ],
                ),
            )
        )

        # 2. Extracted Suspects / Persons
        person_nodes = []
        persons = payload.extractedPersons or []

        # If raw text contains persons and extractedPersons is empty, do a fast regex extract
        if not persons and payload.rawText:
            # Look for lines mentioning Suspect, Accused, or person names
            matches = re.findall(r"(?:accused|suspect|named)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", payload.rawText, re.IGNORECASE)
            persons = list(set(matches)) if matches else ["Primary Suspect"]

        for idx, person_name in enumerate(persons):
            p_id = f"PER-{abs(hash(person_name.strip())) % 1000000:06d}"
            p_node = Entity(
                id=p_id,
                name=person_name.strip(),
                type=EntityType.PERSON,
                source=self.source_name,
                confidence=0.94,
                riskScore=82 + (idx * 3) if idx < 5 else 75,
                metadata=EntityMetadata(
                    role="Named Suspect",
                    status="Named in FIR",
                    offenses=payload.actsAndSections or ["IPC 420"],
                    subtitle=f"FIR Named Accused · {fir_no}",
                    details=[
                        ("FIR Registration", fir_no),
                        ("Sections", ", ".join(payload.actsAndSections or [])),
                        ("Incident Date", payload.dateOfIncident or "Under Investigation"),
                    ],
                ),
            )
            entities.append(p_node)
            person_nodes.append(p_node)

            # Link Suspect -> Police Station (ASSOCIATED_WITH)
            relationships.append(
                Relationship(
                    id=f"REL-FIR-PS-{abs(hash(f'{p_id}_{ps_id}')) % 1000000:06d}",
                    sourceId=p_id,
                    targetId=ps_id,
                    type=RelationshipType.ASSOCIATED_WITH,
                    confidence=0.98,
                    sourceReference=fir_no,
                    metadata=RelationshipMetadata(
                        label="REGISTERED_IN_FIR",
                        weight=8,
                        detail=f"Named under sections {', '.join(payload.actsAndSections or [])}",
                        sourceReference=fir_no,
                    ),
                )
            )

        # Connect multi-suspects in same FIR to each other
        if len(person_nodes) > 1:
            for i in range(len(person_nodes) - 1):
                p1 = person_nodes[i]
                p2 = person_nodes[i + 1]
                relationships.append(
                    Relationship(
                        id=f"REL-FIR-CO-{abs(hash(f'{p1.id}_{p2.id}_{fir_no}')) % 1000000:06d}",
                        sourceId=p1.id,
                        targetId=p2.id,
                        type=RelationshipType.ASSOCIATED_WITH,
                        confidence=0.92,
                        sourceReference=fir_no,
                        metadata=RelationshipMetadata(
                            label="CO_ACCUSED",
                            weight=9,
                            detail=f"Co-accused named in common FIR {fir_no}",
                            sourceReference=fir_no,
                        ),
                    )
                )

        # 3. Extracted Locations
        for loc in (payload.extractedLocations or []):
            loc_id = f"LOC-{abs(hash(loc.strip())) % 1000000:06d}"
            entities.append(
                Entity(
                    id=loc_id,
                    name=loc.strip(),
                    type=EntityType.LOCATION,
                    source=self.source_name,
                    confidence=0.95,
                    riskScore=40,
                    metadata=EntityMetadata(
                        role="Crime Scene / Seizure Point",
                        subtitle=f"Location · {loc.strip()}",
                    ),
                )
            )
            # Link PS to Location
            relationships.append(
                Relationship(
                    id=f"REL-FIR-LOC-{abs(hash(f'{ps_id}_{loc_id}')) % 1000000:06d}",
                    sourceId=ps_id,
                    targetId=loc_id,
                    type=RelationshipType.LOCATED_AT,
                    confidence=0.95,
                    sourceReference=fir_no,
                    metadata=RelationshipMetadata(
                        label="INCIDENT_SITE",
                        weight=6,
                        detail=f"Location referenced in FIR {fir_no}",
                        sourceReference=fir_no,
                    ),
                )
            )

        return entities, relationships
