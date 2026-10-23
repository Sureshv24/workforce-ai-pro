from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AttritionPrediction(Base):
    __tablename__ = "attrition_predictions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id"), nullable=True, index=True
    )
    predicted_attrition: Mapped[bool] = mapped_column(Boolean)
    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)

    age: Mapped[int] = mapped_column(Integer)
    monthly_income: Mapped[float] = mapped_column(Float)
    years_at_company: Mapped[int] = mapped_column(Integer)
    job_satisfaction: Mapped[int] = mapped_column(Integer)
    work_life_balance: Mapped[int] = mapped_column(Integer)
    overtime: Mapped[str] = mapped_column(String(3))
    years_since_promotion: Mapped[int] = mapped_column(Integer)
    distance_from_home: Mapped[int] = mapped_column(Integer)

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
