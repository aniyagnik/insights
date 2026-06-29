import uuid
from datetime import datetime, timezone, timedelta

from app.repositories.dashboard import DashboardRepository
from app.models.dashboard import Dashboard, Widget
from app.schemas.dashboard import DashboardCreate, DashboardUpdate, WidgetCreate
from app.core.exceptions import TenantAccessDeniedException

class DashboardService:
    def __init__(self, repo: DashboardRepository):
        self.repo = repo

    async def create_dashboard(self, payload: DashboardCreate, org_id: uuid.UUID) -> Dashboard:
        return await self.repo.create_dashboard(
            org_id=org_id,
            name=payload.name,
            description=payload.description,
            is_public=payload.is_public
        )

    async def list_dashboards(self, org_id: uuid.UUID) -> list[Dashboard]:
        return await self.repo.list_dashboards(org_id)

    async def get_dashboard(self, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> Dashboard:
        dashboard = await self.repo.get_dashboard(dashboard_id, org_id)
        if not dashboard:
            raise TenantAccessDeniedException("Dashboard not found or access denied.")
        return dashboard

    async def update_dashboard(self, dashboard_id: uuid.UUID, payload: DashboardUpdate, org_id: uuid.UUID) -> Dashboard:
        dashboard = await self.get_dashboard(dashboard_id, org_id)
        return await self.repo.update_dashboard(
            dashboard=dashboard,
            name=payload.name,
            description=payload.description,
            is_public=payload.is_public
        )

    async def delete_dashboard(self, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> None:
        dashboard = await self.get_dashboard(dashboard_id, org_id)
        await self.repo.delete_dashboard(dashboard)

    async def add_widget(self, dashboard_id: uuid.UUID, payload: WidgetCreate, org_id: uuid.UUID) -> Widget:
        # Enforce that the dashboard belongs to their organization before adding a widget
        await self.get_dashboard(dashboard_id, org_id)
        return await self.repo.create_widget(
            dashboard_id=dashboard_id,
            name=payload.name,
            type_val=payload.type,
            query_config=payload.query_config
        )

    async def get_widget_data(self, dashboard_id: uuid.UUID, widget_id: uuid.UUID, org_id: uuid.UUID) -> dict:
        widget = await self.repo.get_widget_with_dashboard(widget_id, dashboard_id, org_id)
        if not widget:
            raise TenantAccessDeniedException("Widget not found or access denied.")
        
        config = widget.query_config
        event_name = config.get("event_name")
        time_range_hours = config.get("time_range_hours", 24)
        interval = config.get("interval", "hour")

        if not event_name:
            raise TenantAccessDeniedException("Widget query configuration is missing 'event_name'.")

        start_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
        
        chart_series = await self._run_aggregation_query(
            target_org_id=org_id,
            event_name=event_name,
            start_time=start_time,
            interval=interval
        )

        return {
            "widget_id": str(widget_id),
            "widget_name": widget.name,
            "type": widget.type.value,
            "event_name": event_name,
            "time_range_hours": time_range_hours,
            "interval": interval,
            "data": chart_series
        }

    async def get_public_dashboard(self, dashboard_id: uuid.UUID) -> Dashboard:
        dashboard = await self.repo.get_public_dashboard(dashboard_id)
        if not dashboard:
            raise TenantAccessDeniedException("Dashboard not found, access denied, or private.")
        return dashboard

    async def get_public_widget_data(self, dashboard_id: uuid.UUID, widget_id: uuid.UUID) -> dict:
        widget = await self.repo.get_public_widget_with_dashboard(widget_id, dashboard_id)
        if not widget:
            raise TenantAccessDeniedException("Widget not found, access denied, or private.")

        config = widget.query_config
        event_name = config.get("event_name")
        time_range_hours = config.get("time_range_hours", 24)
        interval = config.get("interval", "hour")

        if not event_name:
            raise TenantAccessDeniedException("Widget configuration missing event_name.")

        start_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
        chart_series = await self._run_aggregation_query(
            target_org_id=widget.dashboard.organization_id,  # Secure public cross-tenant mapping
            event_name=event_name,
            start_time=start_time,
            interval=interval
        )

        return {
            "widget_id": str(widget_id),
            "widget_name": widget.name,
            "type": widget.type.value,
            "event_name": event_name,
            "time_range_hours": time_range_hours,
            "interval": interval,
            "data": chart_series
        }

    async def _run_aggregation_query(self, target_org_id: uuid.UUID, event_name: str, start_time: datetime, interval: str) -> list[dict]:
        """Core private query runner shared between private and public routes (DRY)."""
        rows = await self.repo.query_time_series_data(target_org_id, event_name, start_time, interval)
        return [{"timestamp": r.interval.isoformat(), "value": r.count} for r in rows]