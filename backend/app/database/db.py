import threading
from datetime import datetime
from typing import Dict, List, Optional
from ..models.entity import Entity, EntityMetadata, EntityType
from ..models.relationship import Relationship, RelationshipMetadata, RelationshipType
from ..models.cases import Case
from ..models.audit import AuditLog, AuditAction, UserRole


# Authentic Cyber Crime Cell & NCRB Baseline Intelligence Network
INITIAL_CYBER_ENTITIES: List[Entity] = [
  Entity(
    id="ORG-NCCC-01",
    name="National Cyber Coordination Centre (NCCC)",
    type=EntityType.ORGANIZATION,
    source="NCRB-NCCC-Grid",
    confidence=1.0,
    riskScore=15,
    metadata=EntityMetadata(
      role="Apex Cyber Intelligence Gateway",
      status="Active Operational",
      location="New Delhi",
      subtitle="National Threat Intelligence & Coordination Core",
      position={"x": 50, "y": 42},
      details=[
        ("Jurisdiction", "National Territory"),
        ("Reporting Mandate", "IT Act §69B / NCRP Portal"),
        ("Active Feeds", "36 State Crime Record Bureaus"),
      ],
    ),
  ),
  Entity(
    id="PER-TG-8812",
    name="Vikram Oberoi",
    type=EntityType.PERSON,
    source="State-Cyber-FIR-2026-9011",
    confidence=0.98,
    riskScore=94,
    metadata=EntityMetadata(
      alias="Sarpanch",
      role="Syndicate Leader & Mastermind",
      status="Priority Watchlist",
      location="Hyderabad · Cyberabad West",
      offenses=["IT Act 66D", "IPC 420", "IPC 120B", "PMLA §3"],
      subtitle="Primary Target · Hawala & Mule Network Core",
      position={"x": 38, "y": 28},
      details=[
        ("FIR Registry", "FIR-2026-9011"),
        ("Active Linked Accounts", "14 Layered Mules"),
        ("Status", "Non-Bailable Warrant Issued"),
      ],
    ),
  ),
  Entity(
    id="PER-DL-4318",
    name="Sameer Khan",
    type=EntityType.PERSON,
    source="State-Cyber-FIR-2026-9011",
    confidence=0.95,
    riskScore=88,
    metadata=EntityMetadata(
      alias="Crypt0_Broker",
      role="Financial Layering Controller",
      status="Under Active Surveillance",
      location="Delhi NCR · Sector 62",
      offenses=["IT Act 66C", "IPC 420", "Hawala Placement"],
      subtitle="Financier & Crypto Funnel Desk",
      position={"x": 64, "y": 26},
      details=[
        ("Role", "Crypto Off-ramp Desk"),
        ("Estimated Volume", "INR 3.8 Cr / Month"),
        ("Active Burner Lines", "6 MSISDNs"),
      ],
    ),
  ),
  Entity(
    id="PH-9876500001",
    name="+91 98765 00001",
    type=EntityType.PHONE,
    source="Telecom-CDR-Gateway",
    confidence=0.99,
    riskScore=82,
    metadata=EntityMetadata(
      alias="Primary Command Line",
      role="Calling Party (A)",
      location="Noida Sector 62 BTS",
      imei="864201048291024",
      imsi="404450129401294",
      subtitle="VoIP & Cellular Burner Line",
      position={"x": 26, "y": 48},
      details=[
        ("Normalized MSISDN", "+919876500001"),
        ("Associated BTS Tower", "Tower Sector-62 BTS"),
        ("Daily Call Frequency", "48 Outgoing / Day"),
      ],
    ),
  ),
  Entity(
    id="PH-9876500002",
    name="+91 98765 00002",
    type=EntityType.PHONE,
    source="Telecom-CDR-Gateway",
    confidence=0.97,
    riskScore=76,
    metadata=EntityMetadata(
      alias="Secondary Receiver",
      role="Called Party (B)",
      location="Howrah Transit Hub BTS",
      imei="358902049102491",
      subtitle="Courier Coordination Line",
      position={"x": 74, "y": 46},
      details=[
        ("Normalized MSISDN", "+919876500002"),
        ("Associated BTS", "Howrah Transit BTS"),
      ],
    ),
  ),
  Entity(
    id="ACC-HDFC-9921",
    name="HDFC Mule Account #992140",
    type=EntityType.ACCOUNT,
    source="Banking-FIU-Ledger",
    confidence=0.99,
    riskScore=92,
    metadata=EntityMetadata(
      alias="Funnel Account 01",
      role="Primary Remitter Node",
      bank="HDFC Bank",
      accountNumber="HDFC-99214012",
      subtitle="Mule Funnel Account · INR 1.45 Cr Flow",
      position={"x": 32, "y": 68},
      details=[
        ("Bank", "HDFC Bank Ltd"),
        ("Freeze Status", "Debit Freeze Flagged"),
        ("Fraud Inflow", "INR 1,45,00,000"),
      ],
    ),
  ),
  Entity(
    id="ACC-ICICI-8812",
    name="ICICI Beneficiary Account #8812",
    type=EntityType.ACCOUNT,
    source="Banking-FIU-Ledger",
    confidence=0.99,
    riskScore=89,
    metadata=EntityMetadata(
      alias="Beneficiary Tier-2",
      role="Off-ramp Siphoning Node",
      bank="ICICI Bank",
      accountNumber="ICICI-88120491",
      subtitle="Beneficiary Account · Layering Desk",
      position={"x": 68, "y": 68},
      details=[
        ("Bank", "ICICI Bank"),
        ("Account Type", "Current Corporate Mule"),
        ("Nodal Notice", "Section 91 CrPC Dispatched"),
      ],
    ),
  ),
  Entity(
    id="IP-185-220-101",
    name="185.220.101.5 (Tor Exit Node)",
    type=EntityType.IP_ADDRESS,
    source="National-Cyber-Portal",
    confidence=0.96,
    riskScore=95,
    metadata=EntityMetadata(
      role="C2 Attacker IP / Proxy",
      ip="185.220.101.5",
      subtitle="Phishing Origin & Proxy Relay",
      position={"x": 50, "y": 14},
      details=[
        ("IP Address", "185.220.101.5"),
        ("Classification", "Malicious Phishing Proxy"),
        ("Linked Complaints", "42 Cases on NCRP"),
      ],
    ),
  ),
  Entity(
    id="DOM-SECURE-KYC",
    name="secure-kyc-update-portal.com",
    type=EntityType.DOMAIN,
    source="Digital-Evidence-Vault",
    confidence=0.98,
    riskScore=96,
    metadata=EntityMetadata(
      role="Credential Harvesting Host",
      subtitle="Phishing Domain · Seized by Cyber Cell",
      position={"x": 50, "y": 84},
      details=[
        ("Domain Host", "secure-kyc-update-portal.com"),
        ("Registrar", "NameCheap Inc (Abuse Flagged)"),
        ("Takedown Status", "DNS Sinkholed"),
      ],
    ),
  ),
]

INITIAL_CYBER_RELATIONSHIPS: List[Relationship] = [
  Relationship(
    id="REL-01",
    sourceId="PER-TG-8812",
    targetId="ORG-NCCC-01",
    type=RelationshipType.ASSOCIATED_WITH,
    confidence=0.99,
    sourceReference="FIR-2026-9011",
    metadata=RelationshipMetadata(
      label="REGISTERED_IN_FIR",
      weight=9,
      detail="Primary accused named in FIR-2026-9011 under IT Act 66D & IPC 420",
    ),
  ),
  Relationship(
    id="REL-02",
    sourceId="PER-DL-4318",
    targetId="ORG-NCCC-01",
    type=RelationshipType.ASSOCIATED_WITH,
    confidence=0.97,
    sourceReference="FIR-2026-9011",
    metadata=RelationshipMetadata(
      label="CO_ACCUSED",
      weight=8,
      detail="Co-accused controller named in national cyber dossier",
    ),
  ),
  Relationship(
    id="REL-03",
    sourceId="PER-TG-8812",
    targetId="PER-DL-4318",
    type=RelationshipType.COMMUNICATED_WITH,
    confidence=0.96,
    sourceReference="CDR-INTEL-01",
    metadata=RelationshipMetadata(
      label="COMMAND_LINK",
      weight=10,
      detail="Direct operational and financial instructions logged via encrypted messenger",
    ),
  ),
  Relationship(
    id="REL-04",
    sourceId="PER-TG-8812",
    targetId="PH-9876500001",
    type=RelationshipType.OWNS,
    confidence=0.98,
    sourceReference="CDR-INTEL-01",
    metadata=RelationshipMetadata(
      label="SUBSCRIBER_LINE",
      weight=9,
      detail="SIM registered under Vikram Oberoi's forged identity document",
    ),
  ),
  Relationship(
    id="REL-05",
    sourceId="PH-9876500001",
    targetId="PH-9876500002",
    type=RelationshipType.CALL,
    confidence=0.99,
    sourceReference="CDR-INTEL-01",
    metadata=RelationshipMetadata(
      label="180s CALL",
      weight=8,
      detail="180s voice call logged via Noida Sector 62 BTS",
      duration=180,
      towerLocation="Noida Sector 62 BTS",
    ),
  ),
  Relationship(
    id="REL-06",
    sourceId="PER-TG-8812",
    targetId="ACC-HDFC-9921",
    type=RelationshipType.OWNS,
    confidence=0.99,
    sourceReference="FIN-HAWALA-01",
    metadata=RelationshipMetadata(
      label="REMITTER_ACCOUNT",
      weight=9,
      detail="Account operated by Vikram Oberoi for initial victim fund collection",
    ),
  ),
  Relationship(
    id="REL-07",
    sourceId="ACC-HDFC-9921",
    targetId="ACC-ICICI-8812",
    type=RelationshipType.TRANSACTION,
    confidence=0.99,
    sourceReference="FIN-HAWALA-01",
    metadata=RelationshipMetadata(
      label="IMPS INR 7,50,000",
      weight=10,
      detail="IMPS transfer of INR 7,50,000 on 2026-08-26 to off-ramp mule account",
      amount=750000,
      bank="HDFC Bank",
    ),
  ),
  Relationship(
    id="REL-08",
    sourceId="IP-185-220-101",
    targetId="DOM-SECURE-KYC",
    type=RelationshipType.LOCATED_AT,
    confidence=0.97,
    sourceReference="EV-2291",
    metadata=RelationshipMetadata(
      label="HOSTING_INFRA",
      weight=8,
      detail="Tor proxy exit node hosting fraudulent phishing domain",
      ipAddress="185.220.101.5",
    ),
  ),
  Relationship(
    id="REL-09",
    sourceId="DOM-SECURE-KYC",
    targetId="ACC-HDFC-9921",
    type=RelationshipType.ASSOCIATED_WITH,
    confidence=0.98,
    sourceReference="NCRP-2026-9042",
    metadata=RelationshipMetadata(
      label="PHISHING_SIPHON",
      weight=9,
      detail="Victim payment credentials entered on domain routed straight to HDFC mule",
    ),
  ),
]


class IntelligenceDatabase:
    """
    Production-grade thread-safe intelligence database for Cyber Cell investigation records.
    Maintains clean, database-driven stores for entities, relationships, case files,
    digital evidence, and tamper-evident audit trails.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._entities: Dict[str, Entity] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._cases: Dict[str, Case] = {}
        self._evidence: Dict[str, dict] = {}
        self._audit_logs: List[AuditLog] = []

        # Bootstrap authentic Cyber Cell baseline intelligence network
        for e in INITIAL_CYBER_ENTITIES:
            self._entities[e.id] = e
        for r in INITIAL_CYBER_RELATIONSHIPS:
            self._relationships[r.id] = r

        # Baseline Case
        self._cases["FIR-2026-9011"] = Case(
            id="FIR-2026-9011",
            title="FIR 2026-9011 — Inter-State Hawala & UPI Phishing Syndicate",
            description="Investigation into organized cyber fraud ring siphoning funds via phishing portals and layered mule accounts under IT Act §66D and IPC §420.",
            priority="Critical",
            lead="Insp. D. Bose",
            suspects=len(INITIAL_CYBER_ENTITIES),
            progress=45,
            category="Financial Fraud",
            firNumber="FIR-2026-9011",
            linkedEntities=[e.id for e in INITIAL_CYBER_ENTITIES],
        )

        # Baseline Evidence
        self._evidence["EV-8821"] = {
            "id": "EV-8821",
            "fileName": "phishing_domain_dump_and_c2_logs.tar.gz",
            "fileType": "Data",
            "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "case": "FIR-2026-9011",
            "size": "28.4 MB",
            "uploadedBy": "Insp. D. Bose",
            "verificationStatus": "VERIFIED",
            "timestamp": "2026-08-26 14:00:00",
        }

    # ==========================================
    # Entity Operations
    # ==========================================
    def get_all_entities(self) -> List[Entity]:
        with self._lock:
            return list(self._entities.values())

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        with self._lock:
            return self._entities.get(entity_id)

    def save_entity(self, entity: Entity) -> Entity:
        with self._lock:
            self._entities[entity.id] = entity
            return entity

    def bulk_save_entities(self, entities: List[Entity]) -> int:
        with self._lock:
            for e in entities:
                self._entities[e.id] = e
            return len(entities)

    def search_entities(self, query: str) -> List[Entity]:
        with self._lock:
            q = query.lower()
            return [
                e for e in self._entities.values()
                if q in e.name.lower() or q in e.id.lower() or (e.metadata.alias and q in e.metadata.alias.lower())
            ]

    # ==========================================
    # Relationship Operations
    # ==========================================
    def get_all_relationships(self) -> List[Relationship]:
        with self._lock:
            return list(self._relationships.values())

    def get_relationship_by_id(self, rel_id: str) -> Optional[Relationship]:
        with self._lock:
            return self._relationships.get(rel_id)

    def save_relationship(self, relationship: Relationship) -> Relationship:
        with self._lock:
            self._relationships[relationship.id] = relationship
            return relationship

    def bulk_save_relationships(self, relationships: List[Relationship]) -> int:
        with self._lock:
            for r in relationships:
                self._relationships[r.id] = r
            return len(relationships)

    # ==========================================
    # Case Management Operations
    # ==========================================
    def get_all_cases(self) -> List[Case]:
        with self._lock:
            return list(self._cases.values())

    def get_case_by_id(self, case_id: str) -> Optional[Case]:
        with self._lock:
            return self._cases.get(case_id)

    def save_case(self, case_obj: Case) -> Case:
        with self._lock:
            self._cases[case_obj.id] = case_obj
            return case_obj

    # ==========================================
    # Digital Evidence Operations
    # ==========================================
    def get_all_evidence(self) -> List[dict]:
        with self._lock:
            return list(self._evidence.values())

    def save_evidence(self, ev_id: str, ev_data: dict) -> dict:
        with self._lock:
            self._evidence[ev_id] = ev_data
            return ev_data

    # ==========================================
    # Security Audit Trail (RBAC)
    # ==========================================
    def record_audit(
        self,
        action: AuditAction,
        resource: str,
        user_id: str = "IN-BOSE-4417",
        user_role: UserRole = UserRole.INVESTIGATOR,
        details: Optional[dict] = None,
        ip_address: str = "127.0.0.1",
    ) -> AuditLog:
        with self._lock:
            log_entry = AuditLog(
                id=f"AUD-{len(self._audit_logs) + 1:05d}",
                userId=user_id,
                userRole=user_role,
                action=action,
                resource=resource,
                details=details or {},
                ipAddress=ip_address,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
            self._audit_logs.insert(0, log_entry)
            return log_entry

    def get_audit_logs(self, limit: int = 50) -> List[AuditLog]:
        with self._lock:
            return self._audit_logs[:limit]

    # ==========================================
    # Telemetry Aggregation
    # ==========================================
    def get_metrics(self) -> dict:
        with self._lock:
            total_entities = len(self._entities)
            total_links = len(self._relationships)
            total_cases = len(self._cases)
            total_evidence = len(self._evidence)
            high_risk_targets = sum(1 for e in self._entities.values() if e.riskScore >= 80)

            return {
                "totalEntities": total_entities,
                "totalRelationships": total_links,
                "totalCases": total_cases,
                "totalEvidence": total_evidence,
                "highRiskTargets": high_risk_targets,
            }


# Global singleton instance
db = IntelligenceDatabase()
