import asyncio
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta 
from celery import Celery
from sqlalchemy.pool import NullPool 
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func 

from app.config import settings
from app.models.event import Event
from app.models.alert import AlertRule, AlertHistory, AlertStatus 

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

@celery_app.task(name="send_invitation_email_task")
def send_invitation_email_task(email: str, org_name: str, invite_link: str):
    """Asynchronously dispatch real invitation HTML emails via SMTP."""
    # Fallback to local logs if SMTP credentials are not configured
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"\n[SMTP MOCK] Credentials missing. Printing invite email to logs:\n"
              f"To: {email}\n"
              f"Org: {org_name}\n"
              f"Invite Link: {invite_link}\n")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"You are invited to join {org_name} on Analytics Platform!"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = email

    html_payload = f"""
    <html>
      <body style="font-family: sans-serif; padding: 20px;">
        <h2>Join {org_name}</h2>
        <p>You have been invited to join the team as a member.</p>
        <p>Please click the button below to accept and complete your account setup:</p>
        <p style="margin: 30px 0;">
          <a href="{invite_link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">
            Accept Invitation
          </a>
        </p>
        <p>This invitation link will expire in 7 days.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_payload, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, email, msg.as_string())
            print(f"[SMTP SUCCESS] Dispatched invitation email successfully to {email}")
    except Exception as e:
        print(f"[SMTP ERROR] Failed to dispatch email: {e}")
        
async def _evaluate_alerts_async():
    """Evaluate active alert rule thresholds against chronological event counts."""
    async with WorkerSessionLocal() as db:
        query = select(AlertRule).where(
            AlertRule.status.in_([AlertStatus.ACTIVE, AlertStatus.TRIGGERED])
        )
        result = await db.execute(query)
        rules = result.scalars().all()
        
        now = datetime.now(timezone.utc)
        
        for rule in rules:
            window_start = now - timedelta(minutes=rule.time_window_minutes)
            
            event_query = select(func.count(Event.id)).where(
                Event.organization_id == rule.organization_id,
                Event.event_name == rule.event_name,
                Event.timestamp >= window_start
            )
            event_res = await db.execute(event_query)
            current_count = event_res.scalar_one() or 0
            
            if current_count >= rule.threshold:
                if rule.status == AlertStatus.ACTIVE:
                    rule.status = AlertStatus.TRIGGERED
                    history_log = AlertHistory(
                        alert_rule_id=rule.id,
                        triggered_value=float(current_count),
                        status_at_trigger=AlertStatus.TRIGGERED
                    )
                    db.add(history_log)
                    print(f"[ALERT TRIGGERED] Rule '{rule.name}' breached! Count: {current_count} >= Threshold: {rule.threshold}")
            
            else:
                if rule.status == AlertStatus.TRIGGERED:
                    rule.status = AlertStatus.ACTIVE
                    history_log = AlertHistory(
                        alert_rule_id=rule.id,
                        triggered_value=float(current_count),
                        status_at_trigger=AlertStatus.RESOLVED
                    )
                    db.add(history_log)
                    print(f"[ALERT RESOLVED] Rule '{rule.name}' resolved. Count: {current_count} < Threshold: {rule.threshold}")
        
        await db.commit()

@celery_app.task(name="evaluate_alerts_task")
def evaluate_alerts_task():
    """Periodic task wrapper triggered by Celery Beat scheduler."""
    asyncio.run(_evaluate_alerts_async())        
