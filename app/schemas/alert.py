import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.alert import AlertStatus

class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    event_name: str = Field(..., min_length=1, max_length=255)
    metric: str = Field("count", max_length=50)
    threshold: float = Field(..., gt=0.0, description="Metric limit value")
    time_window_minutes: int = Field(10, ge=1, description="Sliding calculation window")

class AlertRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    event_name: Optional[str] = Field(None, min_length=1, max_length=255)
    metric: Optional[str] = Field(None, max_length=50)
    threshold: Optional[float] = Field(None, gt=0.0)
    time_window_minutes: Optional[int] = Field(None, ge=1)
    status: Optional[AlertStatus] = None

class AlertHistoryResponse(BaseModel):
    id: uuid.UUID
    triggered_value: float
    status_at_trigger: AlertStatus
    created_at: datetime

    class Config:
        from_attributes = True

class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    event_name: str
    metric: str
    threshold: float
    time_window_minutes: int
    status: AlertStatus
    history: list[AlertHistoryResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True