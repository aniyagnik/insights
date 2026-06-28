import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload 

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user_org import User
from app.models.event import Event
from app.models.dashboard import Dashboard, Widget
from app.core.exceptions import TenantAccessDeniedException
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    WidgetCreate,
    WidgetResponse,
)

router = APIRouter()

@router.post("/", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    payload: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new dashboard registered under the user's organization context."""
    new_dashboard = Dashboard(
        organization_id=current_user.organization_id,
        name=payload.name,
        description=payload.description,
        is_public=payload.is_public
    )
    db.add(new_dashboard)
    await db.commit()
    await db.refresh(new_dashboard)
    return new_dashboard

@router.get("/", response_model=list[DashboardResponse])
async def list_dashboards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all dashboards belonging strictly to the user's organization."""
    query = select(Dashboard).where(
        Dashboard.organization_id == current_user.organization_id
    ).order_by(Dashboard.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch a single organization dashboard by its ID."""
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise TenantAccessDeniedException("Dashboard not found or access denied.")
    return dashboard

@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: uuid.UUID,
    payload: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update active configurations of a tenant-owned dashboard."""
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise TenantAccessDeniedException("Dashboard not found or access denied.")
        
    if payload.name is not None:
        dashboard.name = payload.name
    if payload.description is not None:
        dashboard.description = payload.description
    if payload.is_public is not None:
        dashboard.is_public = payload.is_public
        
    await db.commit()
    await db.refresh(dashboard)
    return dashboard

@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a dashboard and recursively purge its widgets."""
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise TenantAccessDeniedException("Dashboard not found or access denied.")
        
    await db.delete(dashboard)
    await db.commit()
    return

@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    dashboard_id: uuid.UUID,
    payload: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a data visualization widget to a verified organization dashboard."""
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise TenantAccessDeniedException("Dashboard not found or access denied.")
        
    new_widget = Widget(
        dashboard_id=dashboard.id,
        name=payload.name,
        type=payload.type,
        query_config=payload.query_config
    )
    db.add(new_widget)
    await db.commit()
    await db.refresh(new_widget)
    return new_widget


@router.get("/{dashboard_id}/widgets/{widget_id}/data")
async def get_widget_chart_data(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a widget's query configuration to fetch aggregated time-series analytical telemetry."""
    widget_query = select(Widget).join(Dashboard).where(
        Widget.id == widget_id,
        Dashboard.id == dashboard_id,
        Dashboard.organization_id == current_user.organization_id
    )
    result = await db.execute(widget_query)
    widget = result.scalar_one_or_none()
    
    if not widget:
        raise TenantAccessDeniedException("Widget not found or access denied.")

    config = widget.query_config
    event_name = config.get("event_name")
    time_range_hours = config.get("time_range_hours", 24)
    interval = config.get("interval", "hour")  # Default to hourly buckets
    
    if not event_name:
        raise TenantAccessDeniedException("Widget query configuration is missing 'event_name'.")

    start_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)

    time_bucket = func.date_trunc(interval, Event.timestamp).label("interval")
    analytics_query = (
        select(time_bucket, func.count(Event.id).label("count"))
        .where(
            Event.organization_id == current_user.organization_id,
            Event.event_name == event_name,
            Event.timestamp >= start_time
        )
        .group_by(time_bucket)
        .order_by(time_bucket.asc())
    )
    
    analytics_result = await db.execute(analytics_query)
    rows = analytics_result.all()

    chart_series = []
    for row in rows:
        chart_series.append({
            "timestamp": row.interval.isoformat(),
            "value": row.count
        })

    return {
        "widget_id": str(widget_id),
        "widget_name": widget.name,
        "type": widget.type.value,
        "event_name": event_name,
        "time_range_hours": time_range_hours,
        "interval": interval,
        "data": chart_series
    }
    
@router.get("/public/{dashboard_id}", response_model=DashboardResponse)
async def get_public_dashboard(
    dashboard_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Fetch a public, read-only dashboard by ID (No session auth required)."""
    query = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.is_public == True
    )
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise TenantAccessDeniedException("Dashboard not found, access denied, or private.")
    return dashboard


@router.get("/public/{dashboard_id}/widgets/{widget_id}/data")
async def get_public_widget_chart_data(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Execute a public widget's query configuration to fetch aggregated data (No auth required)."""
    widget_query = (
        select(Widget)
        .options(joinedload(Widget.dashboard))
        .join(Dashboard)
        .where(
            Widget.id == widget_id,
            Dashboard.id == dashboard_id,
            Dashboard.is_public == True
        )
    )
    result = await db.execute(widget_query)
    widget = result.scalar_one_or_none()
    
    if not widget:
        raise TenantAccessDeniedException("Widget not found, access denied, or private.")

    config = widget.query_config
    event_name = config.get("event_name")
    time_range_hours = config.get("time_range_hours", 24)
    interval = config.get("interval", "hour")
    
    if not event_name:
        raise TenantAccessDeniedException("Widget configuration missing event_name.")

    start_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)

    time_bucket = func.date_trunc(interval, Event.timestamp).label("interval")
    analytics_query = (
        select(time_bucket, func.count(Event.id).label("count"))
        .where(
            Event.organization_id == widget.dashboard.organization_id,
            Event.event_name == event_name,
            Event.timestamp >= start_time
        )
        .group_by(time_bucket)
        .order_by(time_bucket.asc())
    )
    
    analytics_result = await db.execute(analytics_query)
    rows = analytics_result.all()

    chart_series = [{"timestamp": r.interval.isoformat(), "value": r.count} for r in rows]

    return {
        "widget_id": str(widget_id),
        "widget_name": widget.name,
        "type": widget.type.value,
        "event_name": event_name,
        "time_range_hours": time_range_hours,
        "interval": interval,
        "data": chart_series
    }