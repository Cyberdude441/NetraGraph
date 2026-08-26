from fastapi import APIRouter, status
from ..models.ingest import IngestRequest, IngestResponse
from ..services.ingest_service import ingest_service

router = APIRouter(prefix="/ingest", tags=["Crime Ingestion"])


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest unstructured crime report, FIR, CDR, or financial log",
    description="Extracts named entities, phone identifiers, accounts, vehicles, and infers network relationships with SHA-256 custody verification.",
)
async def ingest_crime_document(payload: IngestRequest) -> IngestResponse:
    return ingest_service.process_ingest(payload)
