import asyncio
import uuid
from datetime import datetime, timezone, timedelta 
from celery import Celery
from sqlalchemy.pool import NullPool 
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.models.alert import AlertStatus  
from app.repositories.event import EventRepository 
from app.repositories.alert import AlertRepository 

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

celery_app.conf.beat_schedule = {
    "evaluate-alerts-every-60-seconds": {
        "task": "evaluate_alerts_task",
        "schedule": 60.0,  # Evaluate active rules every 60 seconds
    }
}

# Create a dedicated worker engine with NullPool
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
    """Worker database connector using our clean EventRepository layer."""
    async with WorkerSessionLocal() as db:
        repo = EventRepository(db)
        await repo.create_events_batch(events_data, org_id)


@celery_app.task(name="process_events_task")
def process_events_task(events_data: list[dict], org_id_str: str):
    """Synchronous worker thread wrapper to execute asynchronous task queues."""
    org_id = uuid.UUID(org_id_str)
    asyncio.run(_insert_events_async(events_data, org_id))

@celery_app.task(name="send_invitation_email_task")
def send_invitation_email_task(email: str, org_name: str, invite_link: str):
    """Asynchronously log a secure onboarding invitation email dispatch"""
    print(
        f"\n"
        f"======================================================================\n"
        f"📨  [SMTP MOCK EMAIL] Onboarding Invitation Dispatched!\n"
        f"----------------------------------------------------------------------\n"
        f"To:          {email}\n"
        f"From:        no-reply@analytics-platform.com\n"
        f"Subject:     Join the '{org_name}' workspace on Analytics Platform!\n"
        f"\n"
        f"Click the link below to configure your password and join the team:\n"
        f"👉  {invite_link}\n"
        f"======================================================================\n"
    )
    return
        
async def _evaluate_alerts_async():
    """Evaluate active alert rule thresholds using clean decoupled repository layers."""
    async with WorkerSessionLocal() as db:
        alert_repo = AlertRepository(db)
        event_repo = EventRepository(db)

        # 1. Fetch rules currently monitoring or triggered using AlertRepository
        rules = await alert_repo.list_active_and_triggered_rules()
        
        now = datetime.now(timezone.utc)
        
        for rule in rules:
            window_start = now - timedelta(minutes=rule.time_window_minutes)
            
            # 2. Query event count using EventRepository
            current_count = await event_repo.count_events_in_window(
                org_id=rule.organization_id,
                event_name=rule.event_name,
                start_time=window_start
            )
            
            # 3. Breach checking logic
            if current_count >= rule.threshold:
                if rule.status == AlertStatus.ACTIVE:
                    rule.status = AlertStatus.TRIGGERED
                    await alert_repo.create_history_log(
                        rule_id=rule.id,
                        value=float(current_count),
                        status=AlertStatus.TRIGGERED
                    )
                    print(f"[ALERT TRIGGERED] Rule '{rule.name}' breached! Count: {current_count} >= Threshold: {rule.threshold}")
            
            # 4. Resolution checking logic
            else:
                if rule.status == AlertStatus.TRIGGERED:
                    rule.status = AlertStatus.ACTIVE
                    await alert_repo.create_history_log(
                        rule_id=rule.id,
                        value=float(current_count),
                        status=AlertStatus.RESOLVED
                    )
                    print(f"[ALERT RESOLVED] Rule '{rule.name}' resolved. Count: {current_count} < Threshold: {rule.threshold}")
        
        await db.commit()

@celery_app.task(name="evaluate_alerts_task")
def evaluate_alerts_task():
    """Periodic task wrapper triggered by Celery Beat scheduler."""
    asyncio.run(_evaluate_alerts_async())