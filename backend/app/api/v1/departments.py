from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)

router = APIRouter(prefix="/departments", tags=["Departments"])


def require_hr(user: User):
    if user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=403,
            detail="Admin or HR permission required",
        )


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    department = Department(**data.model_dump())
    db.add(department)

    try:
        db.commit()
        db.refresh(department)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Department name already exists",
        )

    return department


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    query = select(Department)

    if search:
        query = query.where(Department.name.like(f"%{search.strip()}%"))

    return db.scalars(
        query.order_by(Department.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    return department


@router.patch("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(department, field, value)

    try:
        db.commit()
        db.refresh(department)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Department name already exists",
        )

    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    employee_exists = db.scalar(
        select(Employee.id)
        .where(Employee.department_id == department_id)
        .limit(1)
    )

    if employee_exists is not None:
        raise HTTPException(
            status_code=409,
            detail="Department has employees. Reassign them before deleting.",
        )

    db.delete(department)
    db.commit()
