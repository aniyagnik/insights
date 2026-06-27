import enum
import uuid
from typing import Any
from sqlalchemy import String, ForeignKey, Boolean, Enum, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class WidgetType(str, enum.Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    KPI = "kpi"
    TABLE = "table"

class Dashboard(Base, TimestampMixin):
    __tablename__ = "dashboards"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization")
    widgets: Mapped[list["Widget"]] = relationship(
        "Widget", 
        back_populates="dashboard", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class Widget(Base, TimestampMixin):
    __tablename__ = "widgets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[WidgetType] = mapped_column(
        Enum(WidgetType, name="widget_types"), 
        default=WidgetType.LINE, 
        nullable=False
    )
    
    query_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="widgets")