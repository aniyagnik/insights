import asyncio
import uuid
from datetime import datetime, timezone
from celery import Celery
from sqlalchemy.pool import NullPool 
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.models.event import Event

# Configure the Celery application
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Create a dedicated worker engine with NullPool
# This ensures connections are closed entirely per task and never pooled across closed event loops
worker_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

WorkerSessionLocal = async_sessionmaker(
    bind=worker_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def _insert_events_async(events_data: list[dict], org_id: uuid.UUID):
    """Worker database connector to batch-persist tracking payloads asynchronously."""
    # Use the dedicated WorkerSessionLocal instead of the main database pool
    async with WorkerSessionLocal() as db:
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
        db.add_all(db_events)
        await db.commit()

@celery_app.task(name="process_events_task")
def process_events_task(events_data: list[dict], org_id_str: str):
    """Synchronous worker thread wrapper to execute asynchronous task queues."""
    org_id = uuid.UUID(org_id_str)
    asyncio.run(_insert_events_async(events_data, org_id))