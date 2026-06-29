import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.invitation import Invitation
from app.models.user_org import User, Organization, UserRole

class InvitationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        """Query user details by email to prevent duplicate accounts."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self, 
        org_id: uuid.UUID, 
        email: str, 
        role: UserRole, 
        token: str, 
        expires_at: datetime
    ) -> Invitation:
        """Stage and persist a new invitation record."""
        new_invite = Invitation(
            organization_id=org_id,
            email=email,
            role=role,
            token=token,
            expires_at=expires_at
        )
        self.db.add(new_invite)
        await self.db.commit()
        await self.db.refresh(new_invite)
        return new_invite

    async def list_pending(self, org_id: uuid.UUID) -> list[Invitation]:
        """Fetch unaccepted, unexpired invitations for an organization."""
        query = select(Invitation).where(
            Invitation.organization_id == org_id,
            Invitation.is_accepted == False,
            Invitation.expires_at > datetime.now(timezone.utc)
        ).order_by(Invitation.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_by_token(self, token: str) -> Invitation | None:
        """Fetch an active, unaccepted, unexpired invitation by its token string."""
        query = select(Invitation).where(
            Invitation.token == token,
            Invitation.is_accepted == False,
            Invitation.expires_at > datetime.now(timezone.utc)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_organization_name(self, org_id: uuid.UUID) -> str:
        """Fetch organization name by ID safely with no relationship triggers."""
        query = select(Organization).where(Organization.id == org_id)
        result = await self.db.execute(query)
        org = result.scalar_one_or_none()
        return org.name if org else "Your Organization"

    async def accept_invitation(self, invite: Invitation, hashed_password: str) -> User:
        """Register the user account and mark the invitation as accepted in a single transaction."""
        # 1. Create the new user mapped strictly to the invite's tenant role
        new_user = User(
            email=invite.email,
            hashed_password=hashed_password,
            role=invite.role,
            organization_id=invite.organization_id
        )
        self.db.add(new_user)

        # 2. Mark the invitation as accepted
        invite.is_accepted = True
        
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user