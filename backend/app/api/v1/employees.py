from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse

router = APIRouter(prefix="/employees", tags=["Employees"])


def require_hr(user: User):
    if user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=403,
            detail="Admin or HR permission required",
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

    for field, value in data.model_dump(exclude_unset=True).items():
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
