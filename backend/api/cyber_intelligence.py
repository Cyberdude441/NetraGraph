from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File

from database.neo4j import neo4j_db
from services.cyber_analytics import cyber_analytics_service
from services.cyber_reasoning import cyber_reasoning_service
from pipelines.cyber_ingestion import DATASET_NAMES, cyber_dataset_pipeline

router = APIRouter(prefix="/cyber", tags=["Cyber Threat Intelligence"])


@router.get("/datasets")
def list_datasets():
    return {
        "datasets": list(DATASET_NAMES),
        "raw_path": "backend/datasets/raw",
        "supported_formats": ["csv", "json", "jsonl", "txt"],
    }


@router.post("/datasets/{dataset}/ingest")
def ingest_dataset(dataset: str):
    try:
        return cyber_dataset_pipeline.ingest(dataset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/datasets/ingest-all")
def ingest_all_datasets():
    return cyber_dataset_pipeline.ingest_all()


@router.post("/datasets/{dataset}/upload")
async def upload_dataset(dataset: str, file: UploadFile = File(...)):
    if dataset not in DATASET_NAMES:
        raise HTTPException(status_code=400, detail=f"Unsupported dataset: {dataset}")
    filename = Path(file.filename or "upload.txt").name
    destination = cyber_dataset_pipeline.dataset_root / "raw" / dataset / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(await file.read())
    return {"status": "STORED", "dataset": dataset, "filename": destination.name}


@router.get("/graph")
def get_cyber_graph(
    search: Optional[str] = Query(None),
    node_type: Optional[str] = Query(None),
    relationship_type: Optional[str] = Query(None),
):
    return neo4j_db.query_cyber_graph(search, node_type, relationship_type)


@router.get("/overview")
def get_cyber_overview():
    return cyber_analytics_service.overview()


@router.get("/risk/{entity_id}")
def get_cyber_risk(entity_id: str):
    try:
        return cyber_analytics_service.risk_assessment(entity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Cyber entity not found: {entity_id}") from exc


@router.get("/anomalies")
def get_cyber_anomalies():
    return {"anomalies": cyber_analytics_service.anomalies()}


@router.get("/link-predictions")
def get_link_predictions():
    return {"predictions": cyber_analytics_service.link_predictions()}


@router.post("/reason")
def reason_over_cyber_graph(payload: dict[str, str]):
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    return cyber_reasoning_service.answer(question)
