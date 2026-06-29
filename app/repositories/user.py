import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_org import User, Organization, UserRole

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        """Query user details by email."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Query user details by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_tenant(self, org_name: str, email: str, hashed_password: str) -> User:
        """Create a new Organization and assign its Owner administrator in a single transaction."""
        # 1. Stage organization
        new_org = Organization(name=org_name)
        self.db.add(new_org)
        await self.db.flush()  # Populate new_org.id for FK relation mapping

        # 2. Stage Owner User
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            role=UserRole.OWNER,
            organization_id=new_org.id
        )
        self.db.add(new_user)
        
        # 3. Commit transactions
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user