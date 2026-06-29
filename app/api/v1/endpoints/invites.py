import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.repositories.invitation import InvitationRepository
from app.services.invitation import InvitationService
from app.schemas.invitation import InviteCreate, InviteResponse, InviteAccept
from app.schemas.user_org import UserResponse

router = APIRouter()

async def get_invitation_service(db: AsyncSession = Depends(get_db)) -> InvitationService:
    """FastAPI Dependency Injection to instantiate decoupled Service and Repository layers."""
    repo = InvitationRepository(db)
    return InvitationService(repo)


@router.post("/", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    payload: InviteCreate,
    request: Request,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    service: InvitationService = Depends(get_invitation_service)
):
    """Generate a secure onboarding invitation token for a new team member."""
    frontend_origin = request.headers.get("origin") or "http://127.0.0.1:3000"
    return await service.create_invitation(payload, current_user.organization_id, frontend_origin)

@router.get("/", response_model=list[InviteResponse])
async def list_pending_invitations(
    current_user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service)
):
    """List active unexpired invitations for your organization."""
    return await service.list_pending_invitations(current_user.organization_id)

@router.post("/{token}/accept", response_model=UserResponse)
async def accept_invitation(
    token: str,
    payload: InviteAccept,
    service: InvitationService = Depends(get_invitation_service)
):
    """Accept an invitation, register the user account, and apply their assigned role."""
    return await service.accept_invitation(token, payload)