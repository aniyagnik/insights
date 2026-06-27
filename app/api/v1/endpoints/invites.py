import secrets
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.models.invitation import Invitation
from app.schemas.invitation import InviteCreate, InviteResponse, InviteAccept
from app.schemas.user_org import UserResponse
from app.core.security import hash_password

router = APIRouter()

@router.post("/", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    payload: InviteCreate,
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Generate a secure onboarding invitation token for a new team member."""
    # Check if a user with this email is already registered
    user_query = select(User).where(User.email == payload.email)
    user_res = await db.execute(user_query)
    if user_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )

    # Issue a secure 7-day token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    new_invite = Invitation(
        organization_id=current_user.organization_id,
        email=payload.email,
        role=payload.role,
        token=token,
        expires_at=expires_at
    )
    db.add(new_invite)
    await db.commit()
    await db.refresh(new_invite)
    return new_invite

@router.get("/", response_model=list[InviteResponse])
async def list_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List active unexpired invitations for your organization."""
    query = select(Invitation).where(
        Invitation.organization_id == current_user.organization_id,
        Invitation.is_accepted == False,
        Invitation.expires_at > datetime.now(timezone.utc)
    ).order_by(Invitation.created_at.desc())
    
    res = await db.execute(query)
    return res.scalars().all()

@router.post("/{token}/accept", response_model=UserResponse)
async def accept_invitation(
    token: str,
    payload: InviteAccept,
    db: AsyncSession = Depends(get_db)
):
    """Accept an invitation, register the user account, and apply their assigned role."""
    # Verify the token is active and valid
    query = select(Invitation).where(
        Invitation.token == token,
        Invitation.is_accepted == False,
        Invitation.expires_at > datetime.now(timezone.utc)
    )
    res = await db.execute(query)
    invite = res.scalar_one_or_none()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already accepted invitation."
        )

    # Ensure email is still unique
    user_query = select(User).where(User.email == invite.email)
    user_res = await db.execute(user_query)
    if user_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email has already registered."
        )

    try:
        # Create user mapped strictly to invite's organization and role
        hashed_pw = hash_password(payload.password)
        new_user = User(
            email=invite.email,
            hashed_password=hashed_pw,
            role=invite.role,
            organization_id=invite.organization_id
        )
        db.add(new_user)

        # Mark invitation as accepted
        invite.is_accepted = True
        
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while accepting the invitation."
        )