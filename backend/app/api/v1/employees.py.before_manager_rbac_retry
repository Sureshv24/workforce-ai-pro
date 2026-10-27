from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.schemas.employee_account import EmployeeAccountLink

router = APIRouter(prefix="/employees", tags=["Employees"])


def require_hr(user: User):
    if user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=403,
            detail="Admin or HR permission required",
        )


def validate_employee_lifecycle(hire_date, exit_date, employment_status):
    if hire_date is None:
        raise HTTPException(
            status_code=422,
            detail="Hire date is required for employee lifecycle analytics.",
        )

    if exit_date is not None and exit_date < hire_date:
        raise HTTPException(
            status_code=422,
            detail="Exit date cannot be earlier than hire date.",
        )

    normalized_status = str(employment_status or "").strip().lower()
    allowed_statuses = {"active", "inactive", "on leave"}

    if normalized_status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail="Employment status must be Active, Inactive, or On Leave.",
        )

    if normalized_status == "inactive" and exit_date is None:
        raise HTTPException(
            status_code=422,
            detail="An inactive employee must have an exit date.",
        )

    if normalized_status in {"active", "on leave"} and exit_date is not None:
        raise HTTPException(
            status_code=422,
            detail="Active or On Leave employees cannot have an exit date.",
        )


@router.get("/", response_model=list[EmployeeResponse])
def list_employees(
    search: str | None = None,
    department_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    query = select(Employee)

    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Employee.full_name.like(term),
                Employee.employee_code.like(term),
            )
        )

    if department_id is not None:
        query = query.where(Employee.department_id == department_id)

    return db.scalars(
        query.order_by(Employee.id).offset((page - 1) * page_size).limit(page_size)
    ).all()


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    validate_employee_lifecycle(
        data.hire_date,
        data.exit_date,
        data.employment_status,
    )

    employee = Employee(**data.model_dump())
    db.add(employee)

    try:
        db.commit()
        db.refresh(employee)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not create employee. Check duplicate code and department.",
        )

    return employee


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    updates = data.model_dump(exclude_unset=True)

    validate_employee_lifecycle(
        updates.get("hire_date", employee.hire_date),
        updates.get("exit_date", employee.exit_date),
        updates.get("employment_status", employee.employment_status),
    )

    for field, value in updates.items():
        setattr(employee, field, value)

    try:
        db.commit()
        db.refresh(employee)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not update employee")

    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()


@router.put("/{employee_id}/account")
def link_employee_account(
    employee_id: int,
    payload: EmployeeAccountLink,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    account = db.scalar(
        select(User).where(User.email == str(payload.email).lower())
    )
    if account is None:
        raise HTTPException(
            status_code=404,
            detail="User account not found. The employee must register first.",
        )

    if account.employee_id == employee.id:
        return {
            "message": "Account is already linked to this employee.",
            "employee_id": employee.id,
            "user_id": account.id,
            "email": account.email,
        }

    if account.employee_id is not None:
        raise HTTPException(
            status_code=409,
            detail="This user account is already linked to another employee.",
        )

    existing = db.scalar(
        select(User).where(User.employee_id == employee.id)
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="This employee is already linked to another user account.",
        )

    account.employee_id = employee.id
    try:
        db.commit()
        db.refresh(account)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not link account. Please verify the records and retry.",
        )

    return {
        "message": "Employee account linked successfully.",
        "employee_id": employee.id,
        "user_id": account.id,
        "email": account.email,
    }
