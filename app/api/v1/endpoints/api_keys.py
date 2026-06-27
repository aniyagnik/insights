import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse, ApiKeyUpdate
from app.core.security import generate_api_key

router = APIRouter()

@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Generate and register a new secure access key for the active organization."""
    plain_key, prefix, hashed_key = generate_api_key()
    
    new_key = ApiKey(
        organization_id=current_user.organization_id,
        name=payload.name,
        prefix=prefix,
        hashed_key=hashed_key
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    return {
        "id": new_key.id,
        "name": new_key.name,
        "prefix": new_key.prefix,
        "is_active": new_key.is_active,
        "created_at": new_key.created_at,
        "plain_key": plain_key
    }

@router.get("/", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch all active and suspended access key meta definitions belonging to the organization."""
    query = select(ApiKey).where(
        ApiKey.organization_id == current_user.organization_id
    ).order_by(ApiKey.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{api_key_id}/rotate", response_model=ApiKeyCreateResponse)
async def rotate_api_key(
    api_key_id: uuid.UUID,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Rotate an existing API key, invalidating the old one and returning a new one."""
    query = select(ApiKey).where(
        ApiKey.id == api_key_id,
        ApiKey.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    existing_key = result.scalar_one_or_none()

    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found or does not belong to your organization."
        )

    # Generate a new key and update the existing record
    plain_key, prefix, hashed_key = generate_api_key()
    
    existing_key.hashed_key = hashed_key
    existing_key.prefix = prefix
    existing_key.is_active = True  # Rotation implies the new key is active
    
    await db.commit()
    await db.refresh(existing_key)
    
    return {
        "id": existing_key.id,
        "name": existing_key.name,
        "prefix": existing_key.prefix,
        "is_active": existing_key.is_active,
        "created_at": existing_key.created_at,
        "plain_key": plain_key
    }

@router.put("/{api_key_id}/status", response_model=ApiKeyResponse)
async def update_api_key_status(
    api_key_id: uuid.UUID,
    payload: ApiKeyUpdate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Activate or deactivate an API key by its ID."""
    query = select(ApiKey).where(
        ApiKey.id == api_key_id,
        ApiKey.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    key_to_update = result.scalar_one_or_none()

    if not key_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found or does not belong to your organization."
        )

    key_to_update.is_active = payload.is_active
    await db.commit()
    await db.refresh(key_to_update)
    
    return key_to_update