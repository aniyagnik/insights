import uuid
from app.repositories.api_key import ApiKeyRepository
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate
from app.core.security import generate_api_key
from app.core.exceptions import TenantAccessDeniedException

class ApiKeyService:
    def __init__(self, repo: ApiKeyRepository):
        self.repo = repo

    async def create_key(self, payload: ApiKeyCreate, org_id: uuid.UUID) -> dict:
        """Provision a secure random API Key and store its SHA256 hashed value."""
        plain_key, prefix, hashed_key = generate_api_key()
        new_key = await self.repo.create(
            org_id=org_id,
            name=payload.name,
            prefix=prefix,
            hashed_key=hashed_key
        )
        return {
            "id": new_key.id,
            "name": new_key.name,
            "prefix": new_key.prefix,
            "is_active": new_key.is_active,
            "created_at": new_key.created_at,
            "plain_key": plain_key
        }

    async def list_keys(self, org_id: uuid.UUID) -> list[ApiKey]:
        """Fetch all active and suspended key metadata."""
        return await self.repo.list_keys(org_id)

    async def rotate_key(self, key_id: uuid.UUID, org_id: uuid.UUID) -> dict:
        """Rotate an existing key, invalidating the old hash and returning a new plain key."""
        api_key = await self.repo.get_by_id_and_org(key_id, org_id)
        if not api_key:
            raise TenantAccessDeniedException("API Key not found or does not belong to your organization.")
        
        plain_key, prefix, hashed_key = generate_api_key()
        updated_key = await self.repo.update_key(
            api_key=api_key,
            hashed_key=hashed_key,
            prefix=prefix,
            is_active=True
        )
        return {
            "id": updated_key.id,
            "name": updated_key.name,
            "prefix": updated_key.prefix,
            "is_active": updated_key.is_active,
            "created_at": updated_key.created_at,
            "plain_key": plain_key
        }

    async def update_key_status(self, key_id: uuid.UUID, payload: ApiKeyUpdate, org_id: uuid.UUID) -> ApiKey:
        """Activate or deactivate an API Key by its ID."""
        api_key = await self.repo.get_by_id_and_org(key_id, org_id)
        if not api_key:
            raise TenantAccessDeniedException("API Key not found or does not belong to your organization.")
        
        return await self.repo.update_key(
            api_key=api_key,
            is_active=payload.is_active
        )