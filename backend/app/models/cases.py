from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(..., description="Investigation title")
    description: str = Field(..., description="Case synopsis and incident details")
    priority: str = Field(default="High", description="Critical, High, Medium, Low")
    lead: str = Field(default="Insp. D. Bose", description="Assigned lead officer")
    suspects: Optional[int] = Field(default=0, ge=0)
    progress: Optional[int] = Field(default=15, ge=0, le=100)
    category: Optional[str] = Field(default="Cyber Fraud", description="Crime category")
    firNumber: Optional[str] = None


class Case(CaseCreate):
    id: str = Field(..., description="Unique case file number (e.g. CS-2291)")
    opened: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    linkedEntities: List[str] = Field(default_factory=list)
