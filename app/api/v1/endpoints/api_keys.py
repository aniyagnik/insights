from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse
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