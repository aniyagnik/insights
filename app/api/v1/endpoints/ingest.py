import csv
import io
from datetime import datetime, timezone
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException

from app.api.deps import get_api_key_org_id
from app.schemas.event import EventIngestSingle, EventIngestBatch
from app.worker import process_events_task
from app.core.websocket import manager

router = APIRouter()

@router.post("/single", status_code=status.HTTP_202_ACCEPTED)
async def ingest_single_event(
    payload: EventIngestSingle,
    org_id: Annotated[uuid.UUID, Depends(get_api_key_org_id)]
):
    """Queue event in Celery and instantly broadcast to connected telemetry web clients."""
    timestamp = payload.timestamp or datetime.now(timezone.utc)
    event_data = {
        "event_name": payload.event_name,
        "properties": payload.properties,
        "timestamp": timestamp.isoformat()
    }
    
    process_events_task.delay([event_data], str(org_id))
    
    await manager.broadcast_to_org(str(org_id), {
        "type": "live_event",
        "data": event_data
    })
    
    return {
        "status": "queued", 
        "message": "Event has been accepted and queued for processing."
    }

@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch_events(
    payload: EventIngestBatch,
    org_id: Annotated[uuid.UUID, Depends(get_api_key_org_id)]
):
    """Queue event array in Celery and broadcast to connected telemetry web clients."""
    events_data = []
    for item in payload.events:
        timestamp = item.timestamp or datetime.now(timezone.utc)
        events_data.append({
            "event_name": item.event_name,
            "properties": item.properties,
            "timestamp": timestamp.isoformat()
        })
    
    process_events_task.delay(events_data, str(org_id))
    
    await manager.broadcast_to_org(str(org_id), {
        "type": "batch",
        "events": events_data
    })
    
    return {
        "status": "queued",
        "message": f"Batch of {len(events_data)} events has been queued for processing."
    }

@router.post("/csv", status_code=status.HTTP_202_ACCEPTED)
async def ingest_csv_file(
    file: UploadFile = File(...),
    org_id: uuid.UUID = Depends(get_api_key_org_id)
):
    """Upload a CSV telemetry file to parse and ingest rows asynchronously."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV files are supported."
        )

    try:
        contents = await file.read()
        decoded_content = contents.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        events_data = []
        for row in csv_reader:
            event_name = row.get("event_name")
            if not event_name:
                continue 
            
            timestamp_str = row.get("timestamp")
            
            properties = {
                key: val for key, val in row.items()
                if key not in ("event_name", "timestamp")
            }
            
            events_data.append({
                "event_name": event_name,
                "properties": properties,
                "timestamp": timestamp_str if timestamp_str else None
            })

        if not events_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The CSV file did not contain any valid event records."
            )

        process_events_task.delay(events_data, str(org_id))

        await manager.broadcast_to_org(str(org_id), {
            "type": "batch",
            "events": events_data
        })
        return {
            "status": "queued",
            "message": f"CSV parsed successfully. {len(events_data)} events queued for background processing."
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process CSV file: {str(e)}"
        )