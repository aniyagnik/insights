import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.repositories.alert import AlertRepository
from app.services.alert import AlertService
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse

router = APIRouter()

async def get_alert_service(db: AsyncSession = Depends(get_db)) -> AlertService:
    """FastAPI Dependency Injection to instantiate decoupled Service and Repository layers."""
    repo = AlertRepository(db)
    return AlertService(repo)

@router.post("/", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    payload: AlertRuleCreate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    service: AlertService = Depends(get_alert_service)
):
    """Create a new metric threshold alert rule (Owners and Admins only)."""
    return await service.create_rule(payload, current_user.organization_id)

@router.get("/", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service)
):
    """Retrieve all alert rules belonging strictly to the user's organization."""
    return await service.list_rules(current_user.organization_id)

@router.get("/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service)
):
    """Fetch a single organization alert rule by its ID."""
    return await service.get_rule(rule_id, current_user.organization_id)

@router.put("/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: uuid.UUID,
    payload: AlertRuleUpdate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    service: AlertService = Depends(get_alert_service)
):
    """Update active conditions of a tenant-owned alert rule (Owners and Admins only)."""
    return await service.update_rule(rule_id, payload, current_user.organization_id)

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    service: AlertService = Depends(get_alert_service)
):
    """Delete an alert rule and recursively purge its trigger logs (Owners and Admins only)."""
    await service.delete_rule(rule_id, current_user.organization_id)
    return