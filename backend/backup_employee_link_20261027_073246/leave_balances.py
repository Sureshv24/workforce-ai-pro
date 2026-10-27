from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.leave_balance import LeaveBalance
from app.models.user import User
from app.schemas.leave_balance import LeaveBalanceCreate, LeaveBalanceResponse

router = APIRouter(prefix="/leave-balances", tags=["Leave Balances"])

LEAVE_TYPES = ("Casual", "Sick", "Annual", "Unpaid")


def require_hr(user: User):
    if user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=403,
            detail="Admin or HR permission required",
        )


def calculate_balance(db: Session, balance: LeaveBalance) -> dict:
    year_start = date(balance.year, 1, 1)
    year_end = date(balance.year, 12, 31)

    approved_requests = db.scalars(
        select(LeaveRequest).where(
            LeaveRequest.employee_id == balance.employee_id,
            LeaveRequest.leave_type == balance.leave_type,
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= year_end,
            LeaveRequest.end_date >= year_start,
        )
    ).all()

    used_days = 0
    for request in approved_requests:
        overlap_start = max(request.start_date, year_start)
        overlap_end = min(request.end_date, year_end)
        used_days += (overlap_end - overlap_start).days + 1

    return {
        "id": balance.id,
        "employee_id": balance.employee_id,
        "leave_type": balance.leave_type,
        "year": balance.year,
        "total_days": balance.total_days,
        "used_days": used_days,
        "remaining_days": max(0, balance.total_days - used_days),
        "created_at": balance.created_at,
        "updated_at": balance.updated_at,
    }


@router.get("/", response_model=list[LeaveBalanceResponse])
def list_leave_balances(
    employee_id: int | None = Query(default=None, gt=0),
    year: int = Query(default_factory=date.today().year, ge=2000, le=2100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(LeaveBalance).where(LeaveBalance.year == year)

    if user.role in ("ADMIN", "HR"):
        if employee_id is not None:
            query = query.where(LeaveBalance.employee_id == employee_id)
    else:
        employee = db.scalar(
            select(Employee).where(Employee.employee_code == user.email)
        )
        if employee is None:
            raise HTTPException(
                status_code=403,
                detail="Your user account is not linked to an employee record. Contact HR.",
            )
        query = query.where(LeaveBalance.employee_id == employee.id)

    balances = db.scalars(
        query.order_by(LeaveBalance.employee_id, LeaveBalance.leave_type)
    ).all()

    return [calculate_balance(db, balance) for balance in balances]


@router.post("/", response_model=LeaveBalanceResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_leave_balance(
    payload: LeaveBalanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)

    employee = db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == payload.employee_id,
            LeaveBalance.leave_type == payload.leave_type,
            LeaveBalance.year == payload.year,
        )
    )

    if balance is None:
        balance = LeaveBalance(**payload.model_dump())
        db.add(balance)
    else:
        balance.total_days = payload.total_days

    db.commit()
    db.refresh(balance)

    return calculate_balance(db, balance)


@router.get("/{employee_id}", response_model=list[LeaveBalanceResponse])
def get_employee_leave_balances(
    employee_id: int,
    year: int = Query(default_factory=date.today().year, ge=2000, le=2100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role in ("ADMIN", "HR"):
        employee = db.get(Employee, employee_id)
    else:
        employee = db.scalar(
            select(Employee).where(Employee.employee_code == user.email)
        )
        if employee is not None and employee.id != employee_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own leave balances.",
            )

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    balances = db.scalars(
        select(LeaveBalance)
        .where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == year,
        )
        .order_by(LeaveBalance.leave_type)
    ).all()

    return [calculate_balance(db, balance) for balance in balances]
