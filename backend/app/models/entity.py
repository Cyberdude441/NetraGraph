from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PERSON = "Person"
    PHONE = "Phone"
    ACCOUNT = "BankAccount"
    LOCATION = "Location"
    DEVICE = "Device"
    IP_ADDRESS = "IPAddress"
    DOMAIN = "Domain"
    ORGANIZATION = "Organization"
    VEHICLE = "Vehicle"


class EntityMetadata(BaseModel):
    alias: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    network: Optional[str] = None
    location: Optional[str] = None
    offenses: Optional[List[str]] = Field(default_factory=list)
    lastSeen: Optional[str] = None
    associates: Optional[int] = 0
    position: Optional[Dict[str, float]] = None
    subtitle: Optional[str] = None
    details: Optional[List[Tuple[str, str]]] = Field(default_factory=list)
    imei: Optional[str] = None
    imsi: Optional[str] = None
    ip: Optional[str] = None
    bank: Optional[str] = None
    accountNumber: Optional[str] = None
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EntityBase(BaseModel):
    name: str = Field(..., description="Name or identifier of the entity")
    type: EntityType = Field(..., description="Classification category")
    riskScore: int = Field(default=50, ge=0, le=100, description="Calculated threat risk score (0-100)")
    source: Optional[str] = Field(default="CyberCell-Direct", description="Source data origin (e.g. FIR, CDR, Bank)")
    confidence: Optional[float] = Field(default=0.95, ge=0.0, le=1.0, description="Confidence level of entity resolution")
    metadata: EntityMetadata = Field(default_factory=EntityMetadata)


class EntityCreate(EntityBase):
    id: Optional[str] = None


class Entity(EntityBase):
    id: str = Field(..., description="Unique entity ID (e.g. NG-1001, PH-9876, ACC-4412)")
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
