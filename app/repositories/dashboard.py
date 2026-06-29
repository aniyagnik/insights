import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from app.models.dashboard import Dashboard, Widget
from app.models.event import Event

class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dashboard(self, org_id: uuid.UUID, name: str, description: str | None, is_public: bool) -> Dashboard:
        """Stage and persist a new custom dashboard record."""
        db_dash = Dashboard(organization_id=org_id, name=name, description=description, is_public=is_public)
        self.db.add(db_dash)
        await self.db.commit()
        await self.db.refresh(db_dash)
        return db_dash

    async def list_dashboards(self, org_id: uuid.UUID) -> list[Dashboard]:
        """Fetch all registered dashboards matching the organization ID."""
        query = select(Dashboard).where(Dashboard.organization_id == org_id).order_by(Dashboard.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_dashboard(self, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> Dashboard | None:
        """Fetch a single organization dashboard by its ID."""
        query = select(Dashboard).where(Dashboard.id == dashboard_id, Dashboard.organization_id == org_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_dashboard(self, dashboard: Dashboard, name: str | None, description: str | None, is_public: bool | None) -> Dashboard:
        """Update configurations of an existing dashboard model."""
        if name is not None:
            dashboard.name = name
        if description is not None:
            dashboard.description = description
        if is_public is not None:
            dashboard.is_public = is_public
        await self.db.commit()
        await self.db.refresh(dashboard)
        return dashboard

    async def delete_dashboard(self, dashboard: Dashboard) -> None:
        """Delete a dashboard and purge all its children cascade elements."""
        await self.db.delete(dashboard)
        await self.db.commit()

    async def create_widget(self, dashboard_id: uuid.UUID, name: str, type_val: str, query_config: dict) -> Widget:
        """Stage and persist a custom visual widget."""
        db_widget = Widget(dashboard_id=dashboard_id, name=name, type=type_val, query_config=query_config)
        self.db.add(db_widget)
        await self.db.commit()
        await self.db.refresh(db_widget)
        return db_widget

    async def get_widget_with_dashboard(self, widget_id: uuid.UUID, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> Widget | None:
        """Fetch a specific organization widget matching the IDs."""
        query = select(Widget).join(Dashboard).where(
            Widget.id == widget_id,
            Dashboard.id == dashboard_id,
            Dashboard.organization_id == org_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def query_time_series_data(self, org_id: uuid.UUID, event_name: str, start_time: datetime, interval: str) -> list[tuple]:
        """Aggregate timeseries occurrences using PostgreSQL date_trunc functions."""
        time_bucket = func.date_trunc(interval, Event.timestamp).label("interval")
        query = (
            select(time_bucket, func.count(Event.id).label("count"))
            .where(
                Event.organization_id == org_id,
                Event.event_name == event_name,
                Event.timestamp >= start_time
            )
            .group_by(time_bucket)
            .order_by(time_bucket.asc())
        )
        result = await self.db.execute(query)
        return list(result.all())

    async def get_public_dashboard(self, dashboard_id: uuid.UUID) -> Dashboard | None:
        """Fetch an active dashboard marked as public."""
        query = select(Dashboard).where(Dashboard.id == dashboard_id, Dashboard.is_public == True)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_public_widget_with_dashboard(self, widget_id: uuid.UUID, dashboard_id: uuid.UUID) -> Widget | None:
        """Eagerly load the dashboard relationship and fetch a public widget."""
        query = (
            select(Widget)
            .options(joinedload(Widget.dashboard))
            .join(Dashboard)
            .where(
                Widget.id == widget_id,
                Dashboard.id == dashboard_id,
                Dashboard.is_public == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()