import uuid
from app.repositories.alert import AlertRepository
from app.models.alert import AlertRule
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate
from app.core.exceptions import TenantAccessDeniedException

class AlertService:
    def __init__(self, repo: AlertRepository):
        self.repo = repo

    async def create_rule(self, payload: AlertRuleCreate, org_id: uuid.UUID) -> AlertRule:
        """Process and register a new alert condition within the organization."""
        return await self.repo.create_rule(
            org_id=org_id,
            name=payload.name,
            event_name=payload.event_name,
            metric=payload.metric,
            threshold=payload.threshold,
            time_window_minutes=payload.time_window_minutes
        )

    async def list_rules(self, org_id: uuid.UUID) -> list[AlertRule]:
        """List all alert rules configured for the organization."""
        return await self.repo.list_rules(org_id)

    async def get_rule(self, rule_id: uuid.UUID, org_id: uuid.UUID) -> AlertRule:
        """Retrieve details of a single alert rule, enforcing strict tenant isolation."""
        rule = await self.repo.get_rule(rule_id, org_id)
        if not rule:
            raise TenantAccessDeniedException("Alert rule not found or access denied.")
        return rule

    async def update_rule(self, rule_id: uuid.UUID, payload: AlertRuleUpdate, org_id: uuid.UUID) -> AlertRule:
        """Update configurations or toggle muting states on an existing alert rule."""
        rule = await self.get_rule(rule_id, org_id)
        return await self.repo.update_rule(
            rule=rule,
            name=payload.name,
            event_name=payload.event_name,
            metric=payload.metric,
            threshold=payload.threshold,
            time_window_minutes=payload.time_window_minutes,
            status=payload.status
        )

    async def delete_rule(self, rule_id: uuid.UUID, org_id: uuid.UUID) -> None:
        """Delete an existing alert rule, validating ownership before performing deletions."""
        rule = await self.get_rule(rule_id, org_id)
        await self.repo.delete_rule(rule)