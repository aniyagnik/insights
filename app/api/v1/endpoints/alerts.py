import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.models.alert import AlertRule
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse

router = APIRouter()

@router.post("/", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    payload: AlertRuleCreate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new metric threshold alert rule (Owners and Admins only)."""
    new_rule = AlertRule(
        organization_id=current_user.organization_id,
        name=payload.name,
        event_name=payload.event_name,
        metric=payload.metric,
        threshold=payload.threshold,
        time_window_minutes=payload.time_window_minutes
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule

@router.get("/", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all alert rules belonging strictly to the user's organization."""
    query = select(AlertRule).where(
        AlertRule.organization_id == current_user.organization_id
    ).order_by(AlertRule.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch a single organization alert rule by its ID."""
    query = select(AlertRule).where(
        AlertRule.id == rule_id,
        AlertRule.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found or access denied."
        )
    return rule

@router.put("/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: uuid.UUID,
    payload: AlertRuleUpdate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Update active conditions of a tenant-owned alert rule (Owners and Admins only)."""
    query = select(AlertRule).where(
        AlertRule.id == rule_id,
        AlertRule.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found or access denied."
        )
        
    if payload.name is not None:
        rule.name = payload.name
    if payload.event_name is not None:
        rule.event_name = payload.event_name
    if payload.metric is not None:
        rule.metric = payload.metric
    if payload.threshold is not None:
        rule.threshold = payload.threshold
    if payload.time_window_minutes is not None:
        rule.time_window_minutes = payload.time_window_minutes
    if payload.status is not None:
        rule.status = payload.status
        
    await db.commit()
    await db.refresh(rule)
    return rule

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert rule and recursively purge its trigger logs (Owners and Admins only)."""
    query = select(AlertRule).where(
        AlertRule.id == rule_id,
        AlertRule.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found or access denied."
        )
        
    await db.delete(rule)
    await db.commit()
    return