import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.repositories.api_key import ApiKeyRepository
from app.services.api_key import ApiKeyService
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse, ApiKeyUpdate

# Core router instantiation needed by app/main.py
router = APIRouter()

async def get_api_key_service(db: AsyncSession = Depends(get_db)) -> ApiKeyService:
    """Dependency injection to resolve repositories and api_key services."""
    repo = ApiKeyRepository(db)
    return ApiKeyService(repo)


@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """Generate and register a new secure access key for the active organization."""
    return await service.create_key(payload, current_user.organization_id)


@router.get("/", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """Fetch all active and suspended access key meta definitions belonging to the organization."""
    return await service.list_keys(current_user.organization_id)


@router.put("/{api_key_id}/rotate", response_model=ApiKeyCreateResponse)
async def rotate_api_key(
    api_key_id: uuid.UUID,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """Rotate an existing API key, invalidating the old one and returning a new one."""
    return await service.rotate_key(api_key_id, current_user.organization_id)


@router.put("/{api_key_id}/status", response_model=ApiKeyResponse)
async def update_api_key_status(
    api_key_id: uuid.UUID,
    payload: ApiKeyUpdate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """Activate or deactivate an API key by its ID."""
    return await service.update_key_status(api_key_id, payload, current_user.organization_id)