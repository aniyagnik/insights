import enum
import uuid
from sqlalchemy import String, ForeignKey, Enum, Float, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    RESOLVED = "resolved"
    MUTED = "muted"

class AlertRule(Base, TimestampMixin):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(50), default="count", nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    time_window_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_statuses"), 
        default=AlertStatus.ACTIVE, 
        nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization")
    history: Mapped[list["AlertHistory"]] = relationship(
        "AlertHistory", 
        back_populates="alert_rule", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class AlertHistory(Base, TimestampMixin):
    __tablename__ = "alert_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    alert_rule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    triggered_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    status_at_trigger: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_statuses", create_type=False), 
        nullable=False
    )

    alert_rule: Mapped["AlertRule"] = relationship("AlertRule", back_populates="history")