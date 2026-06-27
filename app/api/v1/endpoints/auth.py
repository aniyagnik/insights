from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user_org import Organization, User, UserRole
from app.schemas.user_org import TenantSignUpRequest, UserResponse, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token

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
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate credentials and return a signed user access token."""
    # Find user by unique email
    query = select(User).where(User.email == payload.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    # Securely verify password matches
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

    # Encode critical metadata inside token claims
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "org_id": str(user.organization_id),
        "role": user.role.value
    }
    
    access_token = create_access_token(data=token_claims)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }