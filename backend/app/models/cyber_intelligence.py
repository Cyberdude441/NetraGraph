from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CyberEntityType(str, Enum):
    IP_ADDRESS = "IPAddress"
    DOMAIN = "Domain"
    URL = "URL"
    EMAIL_ADDRESS = "EmailAddress"
    MALWARE = "Malware"
    THREAT_ACTOR = "ThreatActor"
    ATTACK_TYPE = "AttackType"
    VULNERABILITY = "Vulnerability"
    HASH = "Hash"
    NETWORK_DEVICE = "NetworkDevice"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    EVENT = "Event"


class CyberRelationshipType(str, Enum):
    CONNECTED_TO = "CONNECTED_TO"
    COMMUNICATED_WITH = "COMMUNICATED_WITH"
    TARGETED = "TARGETED"
    HOSTED = "HOSTED"
    USED = "USED"
    ATTACKED = "ATTACKED"
    DISTRIBUTED = "DISTRIBUTED"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    REGISTERED_TO = "REGISTERED_TO"
    OBSERVED_IN = "OBSERVED_IN"
    RELATED_TO = "RELATED_TO"
    SENT_FROM = "SENT_FROM"
    ATTACKED_BY = "ATTACKED_BY"


class CyberEntity(BaseModel):
    id: str
    name: str
    type: CyberEntityType
    risk_score: int = Field(default=50, ge=0, le=100)
    confidence: float = Field(default=0.8, ge=0, le=1)
    source_dataset: str
    source_record_id: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class CyberRelationship(BaseModel):
    id: str
    source_id: str
    target_id: str
    type: CyberRelationshipType
    confidence: float = Field(default=0.8, ge=0, le=1)
    source_dataset: str
    source_record_id: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class DatasetIngestionResponse(BaseModel):
    dataset: str
    records_read: int
    records_processed: int
    entities_created: int
    relationships_created: int
    skipped_records: int
    warnings: List[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    entity_id: str
    risk_score: int
    reasons: List[str]
    graph_features: Dict[str, float | int]


class LinkPrediction(BaseModel):
    source_id: str
    target_id: str
    predicted_relationship: str
    confidence: float
    reasons: List[str]


class ThreatAnomaly(BaseModel):
    entity_id: str
    anomaly_score: float
    reasons: List[str]
