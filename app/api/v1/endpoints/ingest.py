from datetime import datetime, timezone
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_api_key_org_id
from app.models.event import Event
from app.schemas.event import EventIngestSingle, EventIngestBatch

router = APIRouter()

@router.post("/single", status_code=status.HTTP_201_CREATED)
async def ingest_single_event(
    payload: EventIngestSingle,
    org_id: Annotated[uuid.UUID, Depends(get_api_key_org_id)],
    db: AsyncSession = Depends(get_db)
):
    """Ingest a single tracking event mapped strictly to your organization's context."""
    timestamp = payload.timestamp or datetime.now(timezone.utc)
    
    new_event = Event(
        organization_id=org_id,
        event_name=payload.event_name,
        properties=payload.properties,
        timestamp=timestamp
    )
    db.add(new_event)
    await db.commit()
    
    return {"status": "success", "event_id": str(new_event.id)}

@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def ingest_batch_events(
    payload: EventIngestBatch,
    org_id: Annotated[uuid.UUID, Depends(get_api_key_org_id)],
    db: AsyncSession = Depends(get_db)
):
    """Ingest multiple tracking events inside a single transaction mapping."""
    db_events = []
    for item in payload.events:
        timestamp = item.timestamp or datetime.now(timezone.utc)
        db_events.append(
            Event(
                organization_id=org_id,
                event_name=item.event_name,
                properties=item.properties,
                timestamp=timestamp
            )
        )
    
    db.add_all(db_events)
    await db.commit()
    
    return {
        "status": "success",
        "ingested_count": len(db_events)
    }