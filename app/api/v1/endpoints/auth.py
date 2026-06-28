import uuid
import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request  # Added Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user_org import User, Organization, UserRole
from app.schemas.user_org import TenantSignUpRequest, UserResponse, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.config import settings

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def tenant_signup(payload: TenantSignUpRequest, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == payload.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    try:
        new_org = Organization(name=payload.org_name)
        db.add(new_org)
        await db.flush()

        hashed_pw = hash_password(payload.password)
        new_user = User(
            email=payload.email,
            hashed_password=hashed_pw,
            role=UserRole.OWNER,
            organization_id=new_org.id
        )
        db.add(new_user)
        
        await db.commit()
        await db.refresh(new_user)
        return new_user

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during organization registration."
        )

@router.post("/login", response_model=TokenResponse)
async def login(response: Response, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate credentials and issue short-lived JWT + long-lived refresh cookie."""
    query = select(User).where(User.email == payload.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
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

    # 1. Issue access token
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "org_id": str(user.organization_id),
        "role": user.role.value
    }
    access_token = create_access_token(data=token_claims)
    
    # 2. Issue refresh token
    refresh_claims = {
        "sub": str(user.id)
    }
    refresh_token = create_refresh_token(data=refresh_claims)
    
    # 3. Securely set refresh token as an HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        # Must be True in production (HTTPS required)
        secure=settings.ENVIRONMENT != "local",
        # "none" allows secure cross-site cookie sharing between Vercel and Render [4]
        samesite="none" if settings.ENVIRONMENT != "local" else "lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh")
async def refresh_access_token(request: Request, db: AsyncSession = Depends(get_db)):
    """Validate HTTP-only cookie and return a new short-lived access token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing."
        )
    
    try:
        # Decode and verify payload
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
    
    # Fetch database user definition
    query = select(User).where(User.id == uuid.UUID(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or not found.")
    
    # Generate a fresh short-lived access token
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


@router.post("/logout")
async def logout(response: Response):
    """Clear the client's HTTP-only refresh token session cookie."""
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    return {"detail": "Successfully logged out."}