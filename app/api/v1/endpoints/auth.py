from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user_org import Organization, User, UserRole
from app.schemas.user_org import TenantSignUpRequest, UserResponse
from app.core.security import hash_password

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def tenant_signup(payload: TenantSignUpRequest, db: AsyncSession = Depends(get_db)):
    # 1. Enforce email uniqueness
    query = select(User).where(User.email == payload.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    try:
        # 2. Instantiate and stage the organization
        new_org = Organization(name=payload.org_name)
        db.add(new_org)
        await db.flush()  # Populates new_org.id in memory

        # 3. Instantiate and stage the administrative owner user
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