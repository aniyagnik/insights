import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, UploadFile, File

from app.api.deps import get_api_key_org_id
from app.services.ingest import IngestService
from app.schemas.event import EventIngestSingle, EventIngestBatch

router = APIRouter()

async def get_ingest_service() -> IngestService:
    """Dependency injection to resolve the Ingestion Service layer."""
    return IngestService()

@router.post("/single", status_code=status.HTTP_202_ACCEPTED)
async def ingest_single_event(
    payload: EventIngestSingle,
    org_id: Annotated[uuid.UUID, Depends(get_api_key_org_id)],
    service: IngestService = Depends(get_ingest_service)
):
    """Queue event in Celery and instantly broadcast to connected telemetry web clients."""
    return await service.ingest_single(payload, org_id)

@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch_events(
    payload: EventIngestBatch,
    org_id: Annotated[uuid.UUID, Depends(get_api_key_org_id)],
    service: IngestService = Depends(get_ingest_service)
):
    """Queue event array in Celery and broadcast to connected telemetry web clients."""
    return await service.ingest_batch(payload, org_id)

@router.post("/csv", status_code=status.HTTP_202_ACCEPTED)
async def ingest_csv_file(
    file: UploadFile = File(...),
    org_id: uuid.UUID = Depends(get_api_key_org_id),
    service: IngestService = Depends(get_ingest_service)
):
    """Upload a CSV telemetry file to parse, queue, and broadcast asynchronously."""
    return await service.ingest_csv(file, org_id)