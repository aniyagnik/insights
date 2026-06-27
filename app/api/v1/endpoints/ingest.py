from datetime import datetime, timezone
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.api.deps import get_api_key_org_id
from app.schemas.event import EventIngestSingle, EventIngestBatch
from app.worker import process_events_task  # Imported background tasks

router = APIRouter()

@router.post("/single", status_code=status.HTTP_202_ACCEPTED)
async def ingest_single_event(
    payload: EventIngestSingle,
    org_id: Annotated[uuid.UUID, Depends(get_api_key_org_id)]
):
    """Queue a single tracking event asynchronously inside the task broker."""
    timestamp = payload.timestamp or datetime.now(timezone.utc)
    event_data = {
        "event_name": payload.event_name,
        "properties": payload.properties,
        "timestamp": timestamp.isoformat()
    }
    
    process_events_task.delay([event_data], str(org_id))
    
    return {
        "status": "queued", 
        "message": "Event has been accepted and queued for processing."
    }

@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch_events(
    payload: EventIngestBatch,
    org_id: Annotated[uuid.UUID, Depends(get_api_key_org_id)]
):
    """Queue an array of tracking events inside the task broker."""
    events_data = []
    for item in payload.events:
        timestamp = item.timestamp or datetime.now(timezone.utc)
        events_data.append({
            "event_name": item.event_name,
            "properties": item.properties,
            "timestamp": timestamp.isoformat()
        })
    
    process_events_task.delay(events_data, str(org_id))
    
    return {
        "status": "queued",
        "message": f"Batch of {len(events_data)} events has been queued for processing."
    }