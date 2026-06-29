import uuid
import jwt
import hashlib
from datetime import datetime, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.config import settings
from app.database import get_db
from app.models.user_org import User, UserRole
from app.repositories.user import UserRepository        # Imported UserRepository
from app.repositories.api_key import ApiKeyRepository  # Imported ApiKeyRepository

security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Initialize the async Redis client
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def is_rate_limited(key_identifier: str, limit: int = 100, window: int = 60) -> bool:
    """
    Sliding-window rate limiter using Redis sorted sets (zset).
    Prunes timestamps older than the sliding window and evaluates current frequency.
    """
    now = datetime.now(timezone.utc).timestamp()
    clear_before = now - window
    redis_key = f"rate_limit:{key_identifier}"
    
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(redis_key, 0, clear_before)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window)
        
        results = await pipe.execute()
        current_count = results[1]
        
    return current_count >= limit


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract, decode, and validate the active user using their JWT access token, querying via UserRepository."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(user_id))

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated."
        )
    return user


class RoleChecker:
    """Class dependency to enforce Role-Based Access Control on targeted endpoints."""
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access permission to perform this action."
            )
        return current_user


async def get_api_key_org_id(
    api_key: Annotated[str | None, Depends(api_key_header)],
    db: AsyncSession = Depends(get_db)
) -> uuid.UUID:
    """Validate X-API-Key custom header, check active rate limits, and yield org ID, querying via ApiKeyRepository."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'X-API-Key' header."
        )
    
    if "." not in api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key format."
        )

    hashed_key = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    
    api_key_repo = ApiKeyRepository(db)
    db_key = await api_key_repo.get_active_by_hash(hashed_key)

    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or deactivated API Key."
        )
        
    # Enforce Sliding Window Rate Limiting (100 requests per 60 seconds) per API Key
    if await is_rate_limited(str(db_key.id), limit=100, window=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 100 requests per minute per API Key."
        )
        
    return db_key.organization_id