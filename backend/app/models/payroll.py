from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Payroll(Base):
    __tablename__ = "payroll_records"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "pay_period_start", "pay_period_end",
            name="uq_payroll_employee_period"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    pay_period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    pay_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    allowances: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    deductions: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", index=True
    )
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        onupdate=func.now()
    )

    employee = relationship("Employee", lazy="selectin")
