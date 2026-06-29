from fastapi import APIRouter, Depends, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.schemas.user_org import TenantSignUpRequest, UserResponse, LoginRequest, TokenResponse

router = APIRouter()

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency injection to resolve repositories and auth services."""
    repo = UserRepository(db)
    return AuthService(repo)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def tenant_signup(
    payload: TenantSignUpRequest, 
    service: AuthService = Depends(get_auth_service)
):
    """Register a new organization and administrative owner."""
    return await service.register_tenant(payload)


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response, 
    payload: LoginRequest, 
    service: AuthService = Depends(get_auth_service)
):
    """Authenticate credentials and issue short-lived JWT + long-lived refresh cookie."""
    return await service.login(response, payload)


@router.post("/refresh")
async def refresh_access_token(
    request: Request, 
    service: AuthService = Depends(get_auth_service)
):
    """Validate HTTP-only cookie and return a new short-lived access token."""
    refresh_token = request.cookies.get("refresh_token")
    return await service.refresh_access_token(refresh_token)


@router.post("/logout")
async def logout(response: Response):
    """Clear the client's HTTP-only refresh token session cookie."""
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    return {"detail": "Successfully logged out."}