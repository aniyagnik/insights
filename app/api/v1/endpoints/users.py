from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.schemas.user_org import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile details of the currently authenticated user."""
    return current_user

@router.get("/admin-only")
async def admin_only_route(
    current_user: User = Depends(RoleChecker([UserRole.OWNER, UserRole.ADMIN]))
):
    """A restricted route only accessible to tenant Owners and Admins."""
    return {
        "message": "Authorized access granted.",
        "user": current_user.email,
        "role": current_user.role
    }