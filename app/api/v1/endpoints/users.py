from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, RoleChecker
from app.models.user_org import User, UserRole
from app.schemas.user_org import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile details of the currently authenticated user."""
    return current_user
