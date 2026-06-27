from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TenantSignUpRequest(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)