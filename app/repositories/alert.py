import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.alert import AlertRule, AlertHistory, AlertStatus
class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rule(
        self, 
        org_id: uuid.UUID, 
        name: str, 
        event_name: str, 
        metric: str, 
        threshold: float, 
        time_window_minutes: int
    ) -> AlertRule:
        """Stage and persist a new alert rule condition."""
        db_rule = AlertRule(
            organization_id=org_id,
            name=name,
            event_name=event_name,
            metric=metric,
            threshold=threshold,
            time_window_minutes=time_window_minutes
        )
        self.db.add(db_rule)
        await self.db.commit()
        await self.db.refresh(db_rule)
        return db_rule

    async def list_rules(self, org_id: uuid.UUID) -> list[AlertRule]:
        """Fetch all alert rules belonging to the organization."""
        query = select(AlertRule).where(
            AlertRule.organization_id == org_id
        ).order_by(AlertRule.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_rule(self, rule_id: uuid.UUID, org_id: uuid.UUID) -> AlertRule | None:
        """Fetch a single alert rule by ID."""
        query = select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.organization_id == org_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_rule(
        self, 
        rule: AlertRule, 
        name: str | None, 
        event_name: str | None, 
        metric: str | None, 
        threshold: float | None, 
        time_window_minutes: int | None, 
        status: AlertStatus | None
    ) -> AlertRule:
        """Update properties of an existing alert rule model."""
        if name is not None:
            rule.name = name
        if event_name is not None:
            rule.event_name = event_name
        if metric is not None:
            rule.metric = metric
        if threshold is not None:
            rule.threshold = threshold
        if time_window_minutes is not None:
            rule.time_window_minutes = time_window_minutes
        if status is not None:
            rule.status = status
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def list_active_and_triggered_rules(self) -> list[AlertRule]:
        """Fetch all alert rules currently monitoring or triggered."""
        query = select(AlertRule).where(
            AlertRule.status.in_([AlertStatus.ACTIVE, AlertStatus.TRIGGERED])
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_history_log(self, rule_id: uuid.UUID, value: float, status: AlertStatus) -> AlertHistory:
        """Stage and persist an alert trigger or resolution history log."""
        history_log = AlertHistory(
            alert_rule_id=rule_id,
            triggered_value=value,
            status_at_trigger=status
        )
        self.db.add(history_log)
        await self.db.commit()
        return history_log
    
    async def delete_rule(self, rule: AlertRule) -> None:
        """Delete an alert rule and recursively purge its trigger log history."""
        await self.db.delete(rule)
        await self.db.commit()