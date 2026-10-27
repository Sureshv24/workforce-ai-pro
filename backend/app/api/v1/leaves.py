from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.leave_balance import LeaveBalance
from app.schemas.leave import LeaveRequestCreate, LeaveReview, LeaveRequestResponse

router = APIRouter(prefix="/leaves", tags=["Leave Management"])


def require_hr(user: User):
    if user.role not in ("ADMIN", "HR"):
        raise HTTPException(status_code=403, detail="Admin or HR permission required")


def current_employee(db: Session, user: User) -> Employee:
    employee = db.scalar(
        select(Employee).where(Employee.id == user.employee_id)
    )
    if employee is None:
        raise HTTPException(
            status_code=403,
            detail="Your user account is not linked to an employee record. Contact HR.",
        )
    return employee


@router.post("/", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role in ("ADMIN", "HR"):
        employee = db.get(Employee, payload.employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail="Employee not found")
    else:
        employee = current_employee(db, user)
        if payload.employee_id is not None and employee.id != payload.employee_id:
            raise HTTPException(status_code=403, detail="You can only request leave for yourself")

    if payload.start_date < date.today():
        raise HTTPException(status_code=422, detail="Leave start date cannot be in the past")

    overlap = db.scalar(
        select(LeaveRequest).where(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_(("Pending", "Approved")),
            LeaveRequest.start_date <= payload.end_date,
            LeaveRequest.end_date >= payload.start_date,
        )
    )
    if overlap:
        raise HTTPException(
            status_code=409,
            detail="This request overlaps an existing pending or approved leave.",
        )

    record = LeaveRequest(**payload.model_dump(exclude={"employee_id"}))
    record.employee_id = employee.id
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/", response_model=list[LeaveRequestResponse])
def list_leave_requests(
    leave_status: str | None = Query(default=None, alias="status"),
    employee_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(LeaveRequest)

    if user.role not in ("ADMIN", "HR"):
        employee = current_employee(db, user)
        query = query.where(LeaveRequest.employee_id == employee.id)
    elif employee_id is not None:
        query = query.where(LeaveRequest.employee_id == employee_id)

    if leave_status:
        if leave_status not in ("Pending", "Approved", "Rejected"):
            raise HTTPException(
                status_code=422,
                detail="status must be Pending, Approved, or Rejected",
            )
        query = query.where(LeaveRequest.status == leave_status)

    return db.scalars(
        query.order_by(LeaveRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()


@router.patch("/{leave_id}/review", response_model=LeaveRequestResponse)
def review_leave_request(
    leave_id: int,
    payload: LeaveReview,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)

    record = db.get(LeaveRequest, leave_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if record.status != "Pending":
        raise HTTPException(
            status_code=409,
            detail="Only pending leave requests can be reviewed.",
        )

    # Validate available balance before approving a request.
    if payload.status == "Approved":
        first_year = record.start_date.year
        last_year = record.end_date.year

        for year in range(first_year, last_year + 1):
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)

            overlap_start = max(record.start_date, year_start)
            overlap_end = min(record.end_date, year_end)
            requested_days = (overlap_end - overlap_start).days + 1

            balance = db.scalar(
                select(LeaveBalance).where(
                    LeaveBalance.employee_id == record.employee_id,
                    LeaveBalance.leave_type == record.leave_type,
                    LeaveBalance.year == year,
                )
            )

            if balance is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"No {record.leave_type} leave balance is configured "
                        f"for employee {record.employee_id} in {year}. "
                        "Ask HR to configure the allowance before approval."
                    ),
                )

            approved_requests = db.scalars(
                select(LeaveRequest).where(
                    LeaveRequest.employee_id == record.employee_id,
                    LeaveRequest.leave_type == record.leave_type,
                    LeaveRequest.status == "Approved",
                    LeaveRequest.id != record.id,
                    LeaveRequest.start_date <= year_end,
                    LeaveRequest.end_date >= year_start,
                )
            ).all()

            used_days = 0
            for approved in approved_requests:
                used_start = max(approved.start_date, year_start)
                used_end = min(approved.end_date, year_end)
                used_days += (used_end - used_start).days + 1

            remaining_days = max(0, balance.total_days - used_days)

            if requested_days > remaining_days:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Insufficient {record.leave_type} leave balance for "
                        f"{year}. Requested: {requested_days} day(s); "
                        f"remaining: {remaining_days} day(s)."
                    ),
                )

    record.status = payload.status
    record.reviewed_by = user.id
    record.review_comment = payload.review_comment
    db.commit()
    db.refresh(record)
    return record


@router.get("/{leave_id}", response_model=LeaveRequestResponse)
def get_leave_request(
    leave_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.get(LeaveRequest, leave_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if user.role not in ("ADMIN", "HR"):
        employee = current_employee(db, user)
        if record.employee_id != employee.id:
            raise HTTPException(status_code=403, detail="You cannot view this leave request")

    return record
