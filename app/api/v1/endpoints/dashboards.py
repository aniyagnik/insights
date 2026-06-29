import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user_org import User
from app.repositories.dashboard import DashboardRepository
from app.services.dashboard import DashboardService
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    WidgetCreate,
    WidgetResponse,
)

router = APIRouter()

async def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    """FastAPI Dependency Injection to instantiate decoupled Service and Repository layers."""
    repo = DashboardRepository(db)
    return DashboardService(repo)


@router.post("/", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    payload: DashboardCreate,
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Create a new dashboard registered under the user's organization context."""
    return await service.create_dashboard(payload, current_user.organization_id)


@router.get("/", response_model=list[DashboardResponse])
async def list_dashboards(
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Retrieve all dashboards belonging strictly to the user's organization."""
    return await service.list_dashboards(current_user.organization_id)


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Fetch a single organization dashboard by its ID."""
    return await service.get_dashboard(dashboard_id, current_user.organization_id)


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: uuid.UUID,
    payload: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Update active configurations of a tenant-owned dashboard."""
    return await service.update_dashboard(dashboard_id, payload, current_user.organization_id)


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Delete a dashboard and recursively purge its widgets."""
    await service.delete_dashboard(dashboard_id, current_user.organization_id)
    return


@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    dashboard_id: uuid.UUID,
    payload: WidgetCreate,
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Add a data visualization widget to a verified organization dashboard."""
    return await service.add_widget(dashboard_id, payload, current_user.organization_id)


@router.get("/{dashboard_id}/widgets/{widget_id}/data")
async def get_widget_chart_data(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """Execute a widget's query configuration to fetch aggregated time-series analytical telemetry."""
    return await service.get_widget_data(dashboard_id, widget_id, current_user.organization_id)


@router.get("/public/{dashboard_id}", response_model=DashboardResponse)
async def get_public_dashboard(
    dashboard_id: uuid.UUID,
    service: DashboardService = Depends(get_dashboard_service)
):
    """Fetch a public, read-only dashboard by ID (No session auth required)."""
    return await service.get_public_dashboard(dashboard_id)


@router.get("/public/{dashboard_id}/widgets/{widget_id}/data")
async def get_public_widget_chart_data(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    service: DashboardService = Depends(get_dashboard_service)
):
    """Execute a public widget's query configuration to fetch aggregated data (No auth required)."""
    return await service.get_public_widget_data(dashboard_id, widget_id)