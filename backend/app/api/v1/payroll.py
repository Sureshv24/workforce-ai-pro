from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.payroll import Payroll
from app.schemas.payroll import PayrollCreate, PayrollUpdate, PayrollResponse

router = APIRouter(prefix="/payroll", tags=["Payroll"])


def role_of(user: User) -> str:
    return (user.role or "").strip().upper()


def require_payroll_admin(user: User):
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")
    if role_of(user) not in {"ADMIN", "HR"}:
        raise HTTPException(status_code=403, detail="Admin or HR permission required.")


def can_view_payroll(user: User, employee_id: int):
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")
    if role_of(user) in {"ADMIN", "HR"}:
        return
    if user.employee_id is None or user.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="You can only view your own payroll.")


def recalculate(record: Payroll):
    record.gross_salary = (
        Decimal(record.basic_salary) + Decimal(record.allowances)
    ).quantize(Decimal("0.01"))
    record.net_salary = (
        record.gross_salary - Decimal(record.deductions)
    ).quantize(Decimal("0.01"))


@router.post("/", response_model=PayrollResponse, status_code=status.HTTP_201_CREATED)
def create_payroll(
    payload: PayrollCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_payroll_admin(current_user)

    employee = db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found.")

    if db.scalar(select(Payroll.id).where(
        Payroll.employee_id == payload.employee_id,
        Payroll.pay_period_start == payload.pay_period_start,
        Payroll.pay_period_end == payload.pay_period_end,
    )):
        raise HTTPException(
            status_code=409,
            detail="Payroll already exists for this employee and pay period.",
        )

    record = Payroll(
        **payload.model_dump(),
        gross_salary=Decimal("0.00"),
        net_salary=Decimal("0.00"),
    )
    recalculate(record)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/", response_model=list[PayrollResponse])
def list_payroll(
    employee_id: int | None = Query(default=None, gt=0),
    period_start: date | None = None,
    period_end: date | None = None,
    payroll_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if role_of(current_user) not in {"ADMIN", "HR"}:
        if current_user.employee_id is None:
            raise HTTPException(status_code=403, detail="Account is not linked to an employee.")
        employee_id = current_user.employee_id
    elif employee_id is not None and db.get(Employee, employee_id) is None:
        raise HTTPException(status_code=404, detail="Employee not found.")

    query = select(Payroll)
    if employee_id is not None:
        query = query.where(Payroll.employee_id == employee_id)
    if period_start is not None:
        query = query.where(Payroll.pay_period_start >= period_start)
    if period_end is not None:
        query = query.where(Payroll.pay_period_end <= period_end)
    if payroll_status:
        query = query.where(Payroll.status == payroll_status.upper())

    return list(db.scalars(
        query.order_by(Payroll.pay_period_start.desc(), Payroll.id.desc())
    ).all())


@router.get("/{payroll_id}", response_model=PayrollResponse)
def get_payroll(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.get(Payroll, payroll_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Payroll record not found.")
    can_view_payroll(current_user, record.employee_id)
    return record


@router.patch("/{payroll_id}", response_model=PayrollResponse)
def update_payroll(
    payroll_id: int,
    payload: PayrollUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_payroll_admin(current_user)
    record = db.get(Payroll, payroll_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Payroll record not found.")

    changes = payload.model_dump(exclude_unset=True)
    if record.status in {"PAID", "CANCELLED"} and any(
        key in changes for key in {"basic_salary", "allowances", "deductions"}
    ):
        raise HTTPException(
            status_code=409,
            detail="Salary amounts cannot be changed after payroll is paid or cancelled.",
        )

    for key, value in changes.items():
        setattr(record, key, value)

    if record.status == "PAID" and record.payment_date is None:
        raise HTTPException(status_code=422, detail="Payment date is required for PAID payroll.")
    if record.pay_period_end < record.pay_period_start:
        raise HTTPException(status_code=422, detail="Invalid payroll period.")

    recalculate(record)
    if record.deductions > record.gross_salary:
        raise HTTPException(status_code=422, detail="Deductions cannot exceed gross salary.")

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payroll(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_payroll_admin(current_user)
    record = db.get(Payroll, payroll_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Payroll record not found.")
    if record.status == "PAID":
        raise HTTPException(status_code=409, detail="Paid payroll cannot be deleted.")
    db.delete(record)
    db.commit()
    return None
