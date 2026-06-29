import uuid
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status

from app.repositories.invitation import InvitationRepository
from app.models.invitation import Invitation
from app.models.user_org import User
from app.schemas.invitation import InviteCreate, InviteAccept
from app.core.security import hash_password
from app.worker import celery_app

class InvitationService:
    def __init__(self, repo: InvitationRepository):
        self.repo = repo

    async def create_invitation(self, payload: InviteCreate, org_id: uuid.UUID, frontend_origin: str) -> Invitation:
        """Validate registration data, generate safe tokens, and dispatch SMTP background tasks."""
        existing_user = await self.repo.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email is already registered."
            )

        # Generate a secure 7-day token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Save to database
        new_invite = await self.repo.create(
            org_id=org_id,
            email=payload.email,
            role=payload.role,
            token=token,
            expires_at=expires_at
        )

        # Dispatch SMTP onboarding email task asynchronously
        org_name = await self.repo.get_organization_name(org_id)
        invite_link = f"{frontend_origin}/invite/accept?token={token}"
        
        try:
            celery_app.send_task(
                "send_invitation_email_task", 
                args=[new_invite.email, org_name, invite_link]
            )
        except Exception as e:
            import logging
            logger = logging.getLogger("app.invites")
            logger.error(f"Failed to dispatch Celery onboarding task: {e}")

        return new_invite

    async def list_pending_invitations(self, org_id: uuid.UUID) -> list[Invitation]:
        """Fetch all active pending invitations."""
        return await self.repo.list_pending(org_id)

    async def accept_invitation(self, token: str, payload: InviteAccept) -> User:
        """Verify invitation tokens, validate email uniqueness, and complete registration."""
        invite = await self.repo.get_active_by_token(token)
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid, expired, or already accepted invitation."
            )

        # Ensure email didn't sign up separately while invite was pending
        existing_user = await self.repo.get_by_email(invite.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email has already registered."
            )

        hashed_pw = hash_password(payload.password)
        return await self.repo.accept_invitation(invite, hashed_pw)