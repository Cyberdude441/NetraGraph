from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    CALL = "CALL"
    TRANSACTION = "TRANSACTION"
    LOGIN = "LOGIN"
    OWNS = "OWNS"
    LOCATED_AT = "LOCATED_AT"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    COMMUNICATED_WITH = "COMMUNICATED_WITH"
    # Legacy alias support for backward compatibility with existing frontends
    CALLS = "CALL"
    TRANSACTS = "TRANSACTION"
    MEETS = "COMMUNICATED_WITH"


class RelationshipMetadata(BaseModel):
    label: Optional[str] = None
    weight: Optional[int] = Field(default=5, ge=1, le=10)
    detail: Optional[str] = None
    sourceReference: Optional[str] = None
    duration: Optional[int] = None  # in seconds for calls
    amount: Optional[float] = None  # for financial transactions
    bank: Optional[str] = None
    towerLocation: Optional[str] = None
    ipAddress: Optional[str] = None
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RelationshipBase(BaseModel):
    sourceId: str = Field(..., description="Origin node identifier")
    targetId: str = Field(..., description="Destination node identifier")
    type: RelationshipType = Field(..., description="Classification category of linkage")
    confidence: float = Field(default=0.90, ge=0.0, le=1.0, description="Verification confidence score")
    sourceReference: Optional[str] = Field(default="CyberCell-Evidence", description="Case / Ingestion reference ID")
    metadata: RelationshipMetadata = Field(default_factory=RelationshipMetadata)


class RelationshipCreate(RelationshipBase):
    id: Optional[str] = None


class Relationship(RelationshipBase):
    id: str = Field(..., description="Unique link ID (e.g. REL-7701)")
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
