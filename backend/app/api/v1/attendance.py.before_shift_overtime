from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def require_hr(user: User):
    if user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=403,
            detail="Admin or HR permission required",
        )


def validate_employee(db: Session, employee_id: int):
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


def validate_times(check_in, check_out):
    if check_in and check_out and check_out < check_in:
        raise HTTPException(
            status_code=422,
            detail="Check-out cannot be earlier than check-in",
        )


@router.get("/", response_model=list[AttendanceResponse])
def list_attendance(
    employee_id: int | None = Query(default=None, gt=0),
    attendance_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    attendance_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date cannot be after end_date",
        )

    query = select(Attendance)

    if employee_id is not None:
        query = query.where(Attendance.employee_id == employee_id)
    if attendance_date is not None:
        query = query.where(Attendance.attendance_date == attendance_date)
    if start_date is not None:
        query = query.where(Attendance.attendance_date >= start_date)
    if end_date is not None:
        query = query.where(Attendance.attendance_date <= end_date)
    if attendance_status:
        allowed = ("Present", "Absent", "Late", "On Leave")
        if attendance_status not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"status must be one of: {', '.join(allowed)}",
            )
        query = query.where(Attendance.status == attendance_status)

    return db.scalars(
        query.order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()


@router.post(
    "/",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_attendance(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)
    validate_employee(db, data.employee_id)
    validate_times(data.check_in, data.check_out)

    existing = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == data.employee_id,
            Attendance.attendance_date == data.attendance_date,
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Attendance already exists for this employee and date",
        )

    record = Attendance(**data.model_dump())
    db.add(record)

    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Attendance already exists for this employee and date",
        )

    return record


@router.patch("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(
    attendance_id: int,
    data: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)
    record = db.get(Attendance, attendance_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Attendance not found")

    updates = data.model_dump(exclude_unset=True)
    new_check_in = updates.get("check_in", record.check_in)
    new_check_out = updates.get("check_out", record.check_out)
    validate_times(new_check_in, new_check_out)

    new_date = updates.get("attendance_date", record.attendance_date)
    duplicate = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == record.employee_id,
            Attendance.attendance_date == new_date,
            Attendance.id != record.id,
        )
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Attendance already exists for this employee and date",
        )

    for field, value in updates.items():
        setattr(record, field, value)

    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Attendance conflicts with an existing record",
        )

    return record


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)
    record = db.get(Attendance, attendance_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Attendance not found")

    db.delete(record)
    db.commit()


@router.post(
    "/{employee_id}/check-in",
    response_model=AttendanceResponse,
)
def check_in(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)
    employee = validate_employee(db, employee_id)

    if employee.employment_status != "Active":
        raise HTTPException(
            status_code=409,
            detail="Only active employees can check in",
        )

    now = datetime.now().replace(microsecond=0)
    today = now.date()
    record = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == today,
        )
    )

    if record is not None:
        if record.check_in is not None:
            raise HTTPException(
                status_code=409,
                detail="Employee has already checked in today",
            )
        record.check_in = now
        record.status = "Present"
    else:
        record = Attendance(
            employee_id=employee_id,
            attendance_date=today,
            check_in=now,
            status="Present",
        )
        db.add(record)

    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Attendance already exists for today",
        )

    return record


@router.post(
    "/{employee_id}/check-out",
    response_model=AttendanceResponse,
)
def check_out(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)
    validate_employee(db, employee_id)

    today = date.today()
    record = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == today,
        )
    )

    if record is None or record.check_in is None:
        raise HTTPException(
            status_code=409,
            detail="Employee must check in before checking out",
        )
    if record.check_out is not None:
        raise HTTPException(
            status_code=409,
            detail="Employee has already checked out today",
        )

    record.check_out = datetime.now().replace(microsecond=0)

    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save check-out")

    return record


@router.get("/summary/daily")
def daily_attendance_summary(
    attendance_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)
    target_date = attendance_date or date.today()

    records = db.scalars(
        select(Attendance).where(
            Attendance.attendance_date == target_date
        )
    ).all()

    counts = {
        "Present": 0,
        "Absent": 0,
        "Late": 0,
        "On Leave": 0,
    }
    for record in records:
        counts[record.status] = counts.get(record.status, 0) + 1

    return {
        "attendance_date": target_date,
        "total_records": len(records),
        "counts": counts,
    }
