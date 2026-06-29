import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event

class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_events_batch(self, events_data: list[dict], org_id: uuid.UUID) -> None:
        """Batch-persist normalized chronological telemetry events under the organization ID."""
        db_events = []
        for item in events_data:
            ts_str = item.get("timestamp")
            ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)
            db_events.append(
                Event(
                    organization_id=org_id,
                    event_name=item["event_name"],
                    properties=item["properties"],
                    timestamp=ts
                )
            )
        self.db.add_all(db_events)
        await self.db.commit()