import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, ForeignKey, DateTime, Uuid, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False, 
        index=True
    )

    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        Index("ix_events_org_timestamp", "organization_id", "timestamp"),
        Index("ix_events_org_name_timestamp", "organization_id", "event_name", "timestamp"),
    )