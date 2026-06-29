import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.api_key import ApiKey

class ApiKeyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, org_id: uuid.UUID, name: str, prefix: str, hashed_key: str) -> ApiKey:
        """Stage and persist a new API Key record."""
        new_key = ApiKey(
            organization_id=org_id,
            name=name,
            prefix=prefix,
            hashed_key=hashed_key,
            is_active=True
        )
        self.db.add(new_key)
        await self.db.commit()
        await self.db.refresh(new_key)
        return new_key

    async def list_keys(self, org_id: uuid.UUID) -> list[ApiKey]:
        """Fetch all API Keys belonging to the organization."""
        query = select(ApiKey).where(
            ApiKey.organization_id == org_id
        ).order_by(ApiKey.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id_and_org(self, key_id: uuid.UUID, org_id: uuid.UUID) -> ApiKey | None:
        """Fetch a single organization API Key by its ID."""
        query = select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.organization_id == org_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_by_hash(self, hashed_key: str) -> ApiKey | None:
        """Fetch an active API Key by its SHA256 hashed value."""
        query = select(ApiKey).where(
            ApiKey.hashed_key == hashed_key,
            ApiKey.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_key(
        self, 
        api_key: ApiKey, 
        hashed_key: str | None = None, 
        prefix: str | None = None, 
        is_active: bool | None = None
    ) -> ApiKey:
        """Update configurations or toggle active states of an API Key."""
        if hashed_key is not None:
            api_key.hashed_key = hashed_key
        if prefix is not None:
            api_key.prefix = prefix
        if is_active is not None:
            api_key.is_active = is_active
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key