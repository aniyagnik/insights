import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Friendly identifier name")

class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ApiKeyCreateResponse(ApiKeyResponse):
    plain_key: str  # Exposed only once to the client upon creation