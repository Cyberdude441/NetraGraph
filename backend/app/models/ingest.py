from typing import List, Optional
from pydantic import BaseModel, Field
from .entity import Entity
from .relationship import Relationship


class IngestRequest(BaseModel):
    documentTitle: str = Field(..., description="Title or reference number of the incident report / FIR / CDR")
    rawText: str = Field(..., description="Unstructured narrative or surveillance transcript")
    caseId: Optional[str] = Field(default="CS-2291", description="Associated case file ID")
    sourceType: Optional[str] = Field(default="FIR", description="Source format: FIR, Interrogation, CDR, Financial")
    officerId: Optional[str] = Field(default="IN-BOSE-4417", description="Submitting officer clearance ID")


class IngestResponse(BaseModel):
    documentId: str
    sha256Hash: str
    extractedEntities: List[Entity]
    extractedRelationships: List[Relationship]
    ingestedCount: int
    riskAlerts: List[str]
    summary: str
    status: str = "PROCESSED_AND_INDEXED"
