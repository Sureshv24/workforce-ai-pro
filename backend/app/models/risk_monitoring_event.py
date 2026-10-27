from datetime import datetime

from sqlalchemy import (
    DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RiskMonitoringEvent(Base):
    __tablename__ = "risk_monitoring_events"
    __table_args__ = (
        UniqueConstraint(
            "prediction_id",
            name="uq_risk_monitoring_events_prediction_id",
        ),
        Index("ix_risk_events_employee_created", "employee_id", "created_at"),
        Index("ix_risk_events_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("attrition_predictions.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_risk_level: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    current_risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_risk_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    current_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    triggered_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
