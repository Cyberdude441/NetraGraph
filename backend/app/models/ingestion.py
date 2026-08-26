from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# 1. FIR Ingestion Models
class FIRIngestPayload(BaseModel):
    caseNumber: str = Field(..., description="FIR or Case registration ID (e.g. FIR-2026-9921)")
    policeStation: Optional[str] = Field(default="Cyber Crime Police Station", description="Police station jurisdiction")
    dateOfIncident: Optional[str] = None
    actsAndSections: Optional[List[str]] = Field(default_factory=lambda: ["IT Act 66D", "IPC 420"])
    rawText: Optional[str] = Field(default=None, description="Full text transcript of FIR / Investigation report")
    extractedPersons: Optional[List[str]] = Field(default_factory=list)
    extractedOrgs: Optional[List[str]] = Field(default_factory=list)
    extractedLocations: Optional[List[str]] = Field(default_factory=list)
    leadOfficer: Optional[str] = Field(default="Inspector D. Bose")


# 2. CDR Ingestion Models
class CDRRecord(BaseModel):
    caller_number: str = Field(..., description="A-Party mobile or phone number")
    receiver_number: str = Field(..., description="B-Party mobile or phone number")
    timestamp: str = Field(..., description="Call initiation timestamp (ISO 8601 or YYYY-MM-DD HH:MM:SS)")
    duration: int = Field(default=60, description="Call duration in seconds")
    tower_location: Optional[str] = Field(default="Sector-9 Tower 41", description="Cell tower / BTS location")
    imei: Optional[str] = Field(default=None, description="Handset IMEI identifier")
    imsi: Optional[str] = Field(default=None, description="SIM IMSI identifier")
    caller_name: Optional[str] = None
    receiver_name: Optional[str] = None


class CDRIngestPayload(BaseModel):
    caseReference: Optional[str] = Field(default="CDR-BATCH", description="Case or file reference ID")
    records: List[CDRRecord] = Field(..., description="Batch of CDR telecom entries")


# 3. Financial Transaction Ingestion Models
class FinanceRecord(BaseModel):
    sender_account: str = Field(..., description="Source bank account number or UPI ID")
    receiver_account: str = Field(..., description="Destination bank account number or UPI ID")
    amount: float = Field(..., ge=0.0, description="Transaction monetary amount")
    timestamp: str = Field(..., description="Transaction timestamp")
    transaction_type: str = Field(default="IMPS", description="NEFT, RTGS, IMPS, UPI, Hawala, Cash")
    bank: str = Field(default="HDFC Bank", description="Origin or routing financial institution")
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    reference_number: Optional[str] = None


class FinanceIngestPayload(BaseModel):
    caseReference: Optional[str] = Field(default="FIN-BATCH", description="Investigation case reference")
    transactions: List[FinanceRecord] = Field(..., description="Batch of bank transactions")


# 4. Cyber Crime Complaint Models
class CyberComplaintPayload(BaseModel):
    complaint_id: str = Field(..., description="Cyber crime portal complaint ID (e.g. CCP-2026-8812)")
    victim: str = Field(..., description="Complainant or victim entity name")
    attack_type: str = Field(..., description="Phishing, Ransomware, Financial Fraud, SIM Swap, Identity Theft")
    email: Optional[str] = None
    phone: Optional[str] = None
    ip_address: Optional[str] = None
    loss_amount: Optional[float] = Field(default=0.0, ge=0.0)
    date: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    suspect_account: Optional[str] = None
    suspect_phone: Optional[str] = None
    narrative: Optional[str] = None


# 5. Digital Evidence Metadata Models
class DigitalEvidencePayload(BaseModel):
    exhibit_id: Optional[str] = Field(default=None, description="EV-XXXX exhibit tag")
    file_name: str = Field(..., description="Name of digital artifact or seized image")
    file_type: str = Field(default="Document", description="Audio, Video, Document, Image, Data, DiskImage")
    hash_sha256: str = Field(..., description="SHA-256 cryptographic checksum")
    case_reference: str = Field(..., description="Associated case file ID")
    ip_address: Optional[str] = None
    domain: Optional[str] = None
    device_model: Optional[str] = None
    email_headers: Optional[Dict[str, str]] = None
    seizure_location: Optional[str] = None
    officer_in_charge: Optional[str] = Field(default="Insp. D. Bose")
    size_mb: Optional[float] = 10.5
    custody_status: Optional[str] = Field(default="VERIFIED", description="PROCESSING, VERIFIED, SEALED")


# General Ingestion Response
class IngestionResponse(BaseModel):
    status: str = "SUCCESS"
    module: str
    message: str
    nodesCreated: int
    edgesCreated: int
    entities: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
