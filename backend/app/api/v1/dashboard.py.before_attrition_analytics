from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/hiring-trends")
def dashboard_hiring_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "HR", "MANAGER"):
        raise HTTPException(
            status_code=403,
            detail="Dashboard access requires HR, Manager, or Admin",
        )

    from datetime import date

    today = date.today()
    current_month = today.year * 12 + today.month - 1
    first_month = current_month - 5
    start_date = date(first_month // 12, first_month % 12 + 1, 1)

    rows = db.execute(
        select(
            func.year(Employee.hire_date),
            func.month(Employee.hire_date),
            func.count(Employee.id),
        )
        .where(
            Employee.hire_date >= start_date,
            Employee.hire_date <= today,
        )
        .group_by(
            func.year(Employee.hire_date),
            func.month(Employee.hire_date),
        )
    ).all()

    counts = {
        (int(year), int(month)): int(count)
        for year, month, count in rows
    }

    monthly_hires = []
    for offset in range(6):
        month_index = first_month + offset
        year = month_index // 12
        month = month_index % 12 + 1
        month_date = date(year, month, 1)
        monthly_hires.append({
            "month": month_date.strftime("%b"),
            "year": year,
            "hires": counts.get((year, month), 0),
        })

    return {
        "metric": "monthly_hires",
        "description": "Employees whose hire_date falls within each month",
        "monthly_hires": monthly_hires,
    }


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
