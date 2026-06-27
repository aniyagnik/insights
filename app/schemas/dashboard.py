import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.models.dashboard import WidgetType

class WidgetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: WidgetType = WidgetType.LINE
    query_config: dict[str, Any] = Field(default_factory=dict)

class WidgetResponse(BaseModel):
    id: uuid.UUID
    dashboard_id: uuid.UUID
    name: str
    type: WidgetType
    query_config: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = False

class DashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None

class DashboardResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    is_public: bool
    widgets: list[WidgetResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True