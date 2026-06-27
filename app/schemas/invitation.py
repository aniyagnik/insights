import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.user_org import UserRole

class InviteCreate(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER

class InviteResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: UserRole
    token: str
    is_accepted: bool
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class InviteAccept(BaseModel):
    password: str = Field(..., min_length=8, max_length=100)