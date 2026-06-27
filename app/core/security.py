import secrets
import hashlib
import bcrypt
import jwt
from app.config import settings
from datetime import datetime, timedelta, timezone

def hash_password(password: str) -> str:
    """Generate a secure salted bcrypt password hash."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain password against its hashed value."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8")
    )

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": int(expire.timestamp()), "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Generate a long-lived signed HS256 JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": int(expire.timestamp()), "type": "refresh"}) 
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a secure random API key.
    Returns: Tuple of (plain_text_key, search_prefix, hashed_db_key)
    """
    prefix = "pk_live_" + secrets.token_hex(4)  
    secret = secrets.token_urlsafe(32)
    plain_key = f"{prefix}.{secret}"
    
    hashed_key = hashlib.sha256(plain_key.encode("utf-8")).hexdigest()
    return plain_key, prefix, hashed_key