from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "Admin"
    SUPERVISOR = "Supervisor"
    INVESTIGATOR = "Investigator"
    ANALYST = "Analyst"


class AuditAction(str, Enum):
    INGESTION = "INGESTION"
    VIEW_GRAPH = "VIEW_GRAPH"
    VIEW_PROFILE = "VIEW_PROFILE"
    SEARCH_QUERY = "SEARCH_QUERY"
    EXPORT_DOSSIER = "EXPORT_DOSSIER"
    UPDATE_EVIDENCE = "UPDATE_EVIDENCE"
    AI_INFERENCE = "AI_INFERENCE"
    LOGIN = "LOGIN"


class AuditLog(BaseModel):
    id: str = Field(..., description="Unique audit event identifier")
    userId: str = Field(default="IN-BOSE-4417", description="Officer Service ID / Analyst Identifier")
    userRole: UserRole = Field(default=UserRole.INVESTIGATOR, description="Active RBAC clearance role")
    action: AuditAction = Field(..., description="Type of operation performed")
    resource: str = Field(..., description="Target case, entity ID, or API route accessed")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    ipAddress: Optional[str] = Field(default="127.0.0.1")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
