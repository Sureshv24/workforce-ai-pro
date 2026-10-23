from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "HR", "MANAGER"):
        raise HTTPException(
            status_code=403,
            detail="Dashboard access requires HR, Manager, or Admin",
        )

    total_employees = db.scalar(
        select(func.count(Employee.id))
    ) or 0

    status_rows = db.execute(
        select(Employee.employment_status, func.count(Employee.id))
        .group_by(Employee.employment_status)
    ).all()

    department_rows = db.execute(
        select(
            Department.id,
            Department.name,
            func.count(Employee.id).label("employee_count"),
        )
        .outerjoin(Employee, Employee.department_id == Department.id)
        .group_by(Department.id, Department.name)
        .order_by(Department.name)
    ).all()

    return {
        "total_employees": total_employees,
        "employment_status_counts": {
            str(employee_status): count
            for employee_status, count in status_rows
        },
        "department_headcount": [
            {
                "department_id": department_id,
                "department_name": name,
                "employee_count": count,
            }
            for department_id, name, count in department_rows
        ],
    }
