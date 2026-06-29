import uuid
import jwt
from fastapi import Response, HTTPException, status
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.repositories.user import UserRepository
from app.models.user_org import User
from app.schemas.user_org import TenantSignUpRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token

class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register_tenant(self, payload: TenantSignUpRequest) -> User:
        """Validate registration data, hash credentials, and provision tenant workspace."""
        existing_user = await self.repo.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )
        
        hashed_pw = hash_password(payload.password)
        return await self.repo.create_tenant(
            org_name=payload.org_name,
            email=payload.email,
            hashed_password=hashed_pw
        )

    async def login(self, response: Response, payload: LoginRequest) -> dict:
        """Verify credentials and set secure HttpOnly refresh session cookies."""
        user = await self.repo.get_by_email(payload.email)
        
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated."
            )

        # 1. Encode access token claims
        token_claims = {
            "sub": str(user.id),
            "email": user.email,
            "org_id": str(user.organization_id),
            "role": user.role.value
        }
        access_token = create_access_token(data=token_claims)
        
        # 2. Encode refresh token claims
        refresh_claims = {"sub": str(user.id)}
        refresh_token = create_refresh_token(data=refresh_claims)
        
        # 3. Configure HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT != "local",
            samesite="none" if settings.ENVIRONMENT != "local" else "lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    async def refresh_access_token(self, refresh_token: str | None) -> dict:
        """Validate an active refresh token and issue a fresh, short-lived access token."""
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is missing."
            )
        
        try:
            payload = jwt.decode(
                refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "refresh":
                raise jwt.PyJWTError()
            user_id = payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired.")
        except jwt.PyJWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
        
        user = await self.repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or not found.")
        
        token_claims = {
            "sub": str(user.id),
            "email": user.email,
            "org_id": str(user.organization_id),
            "role": user.role.value
        }
        new_access_token = create_access_token(data=token_claims)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }