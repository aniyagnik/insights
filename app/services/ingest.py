import csv
import io
import uuid
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, status

from app.worker import process_events_task
from app.core.websocket import manager
from app.schemas.event import EventIngestSingle, EventIngestBatch

class IngestService:
    async def ingest_single(self, payload: EventIngestSingle, org_id: uuid.UUID) -> dict:
        """Format parameters, dispatch Celery queue, and broadcast to active WebSockets."""
        timestamp = payload.timestamp or datetime.now(timezone.utc)
        event_data = {
            "event_name": payload.event_name,
            "properties": payload.properties,
            "timestamp": timestamp.isoformat()
        }
        
        # Dispatch database write asynchronously to Celery
        process_events_task.delay([event_data], str(org_id))
        
        # Broadcast real-time push notification
        await manager.broadcast_to_org(str(org_id), {
            "type": "live_event",
            "data": event_data
        })
        
        return {
            "status": "queued",
            "message": "Event has been accepted and queued for processing."
        }

    async def ingest_batch(self, payload: EventIngestBatch, org_id: uuid.UUID) -> dict:
        """Format batch arrays, dispatch Celery queue, and broadcast to active WebSockets."""
        events_data = []
        for item in payload.events:
            timestamp = item.timestamp or datetime.now(timezone.utc)
            events_data.append({
                "event_name": item.event_name,
                "properties": item.properties,
                "timestamp": timestamp.isoformat()
            })
        
        # Dispatch batch database write asynchronously to Celery
        process_events_task.delay(events_data, str(org_id))
        
        # Broadcast batch data to active sockets
        await manager.broadcast_to_org(str(org_id), {
            "type": "batch",
            "events": events_data
        })
        
        return {
            "status": "queued",
            "message": f"Batch of {len(events_data)} events has been queued for processing."
        }

    async def ingest_csv(self, file: UploadFile, org_id: uuid.UUID) -> dict:
        """Parse uploaded CSV files, queue tasks, and broadcast rows in real-time."""
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

            # Dispatch parsed bulk database write asynchronously to Celery
            process_events_task.delay(events_data, str(org_id))

            # Broadcast parsed CSV rows to active sockets
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