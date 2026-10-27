from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(150))
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL", name="fk_employees_manager_id_employees"),
        nullable=True,
        index=True,
    )
    manager: Mapped["Employee | None"] = relationship(
        "Employee", remote_side="Employee.id",
        foreign_keys=[manager_id], back_populates="direct_reports"
    )
    direct_reports: Mapped[list["Employee"]] = relationship(
        "Employee", foreign_keys=[manager_id],
        back_populates="manager"
    )
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    exit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(
        String(30), default="Active"
    )

    user_account: Mapped["User | None"] = relationship(
        "User",
        uselist=False,
        foreign_keys="User.employee_id",
        lazy="selectin",
    )

    @property
    def account_linked(self) -> bool:
        return self.user_account is not None
