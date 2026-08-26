from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from ..models.ingestion import (
    FIRIngestPayload,
    CDRIngestPayload,
    FinanceIngestPayload,
    CyberComplaintPayload,
    DigitalEvidencePayload,
    IngestionResponse,
)
from ..services.ingestion_service import ingestion_service

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion & Gateways"])


@router.post("/fir", response_model=IngestionResponse)
async def ingest_fir(
    payload: FIRIngestPayload,
    x_user_id: Optional[str] = Header("IN-BOSE-4417", alias="X-User-ID"),
):
    """
    Ingest FIR / Case Investigation documents (PDF, DOCX, XML, JSON).
    Extracts Suspects, Organizations, Locations, Offenses, and builds initial case linkages.
    """
    try:
        return await ingestion_service.ingest_fir(payload, user_id=x_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FIR Ingestion failed: {str(e)}")


@router.post("/cdr", response_model=IngestionResponse)
async def ingest_cdr(
    payload: CDRIngestPayload,
    x_user_id: Optional[str] = Header("IN-BOSE-4417", alias="X-User-ID"),
):
    """
    Ingest Call Detail Record (CDR) telecom logs.
    Normalizes MSISDNs, links calling/called parties, cell towers, and IMEIs.
    """
    try:
        return await ingestion_service.ingest_cdr(payload, user_id=x_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CDR Ingestion failed: {str(e)}")


@router.post("/finance", response_model=IngestionResponse)
async def ingest_finance(
    payload: FinanceIngestPayload,
    x_user_id: Optional[str] = Header("IN-BOSE-4417", alias="X-User-ID"),
):
    """
    Ingest bank account transaction sheets, UPI transfers, and Hawala routing logs.
    Generates Account nodes and Transaction links with monetary metadata.
    """
    try:
        return await ingestion_service.ingest_finance(payload, user_id=x_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Financial Ingestion failed: {str(e)}")


@router.post("/cyber", response_model=IngestionResponse)
async def ingest_cyber_complaint(
    payload: CyberComplaintPayload,
    x_user_id: Optional[str] = Header("IN-BOSE-4417", alias="X-User-ID"),
):
    """
    Ingest National Cyber Crime Portal complaints.
    Links Victim, Attacker IP, Malicious accounts, and Phishing lines.
    """
    try:
        return await ingestion_service.ingest_cyber(payload, user_id=x_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cyber Complaint Ingestion failed: {str(e)}")


@router.post("/evidence", response_model=IngestionResponse)
async def ingest_digital_evidence(
    payload: DigitalEvidencePayload,
    x_user_id: Optional[str] = Header("IN-BOSE-4417", alias="X-User-ID"),
):
    """
    Register cryptographic digital forensic exhibits with SHA-256 integrity seal.
    Anchors chain of custody in the evidence ledger.
    """
    try:
        return await ingestion_service.ingest_evidence(payload, user_id=x_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence Registration failed: {str(e)}")
