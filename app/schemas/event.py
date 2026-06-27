from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class EventIngestSingle(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=255)
    properties: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None

class EventIngestBatch(BaseModel):
    events: list[EventIngestSingle] = Field(..., min_length=1, max_length=1000)