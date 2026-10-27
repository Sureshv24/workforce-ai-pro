from datetime import date, datetime

from datetime import date, datetime, time, timedelta

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time as SQLTime,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    start_time: Mapped[time] = mapped_column(SQLTime, nullable=False)
    end_time: Mapped[time] = mapped_column(SQLTime, nullable=False)
    break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="shift"
    )

    @property
    def expected_work_minutes(self) -> int:
        start = datetime.combine(date.min, self.start_time)
        end = datetime.combine(date.min, self.end_time)
        if end <= start:
            end += timedelta(days=1)
        return max(
            0,
            int((end - start).total_seconds() // 60) - self.break_minutes,
        )


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name="uq_attendance_employee_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    shift_id: Mapped[int | None] = mapped_column(
        ForeignKey("shifts.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    shift: Mapped["Shift | None"] = relationship(
        back_populates="attendance_records",
        lazy="selectin",
    )
    attendance_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    check_in: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    check_out: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Present"
    )
    remarks: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )


    @property
    def worked_minutes(self) -> int | None:
        if self.check_in is None or self.check_out is None:
            return None
        elapsed = int((self.check_out - self.check_in).total_seconds() // 60)
        if self.shift is not None:
            elapsed -= self.shift.break_minutes
        return max(0, elapsed)

    @property
    def overtime_minutes(self) -> int | None:
        if self.worked_minutes is None or self.shift is None:
            return None
        return max(0, self.worked_minutes - self.shift.expected_work_minutes)

    @property
    def shift_name(self) -> str | None:
        return self.shift.name if self.shift is not None else None
