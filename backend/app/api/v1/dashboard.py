from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
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
    period: str = Query("last_30_days"),
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



    # Reporting period selected by the dashboard.
    today = date.today()

    if period == "last_30_days":
        period_start = today - timedelta(days=29)
        period_label = "Last 30 days"
    elif period == "month_to_date":
        period_start = date(today.year, today.month, 1)
        period_label = "Month to date"
    elif period == "last_90_days":
        period_start = today - timedelta(days=89)
        period_label = "Last 90 days"
    elif period == "year_to_date":
        period_start = date(today.year, 1, 1)
        period_label = "Year to date"
    else:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid period. Use last_30_days, month_to_date, "
                "last_90_days, or year_to_date."
            ),
        )

    employee_rows = db.scalars(select(Employee)).all()

    missing_hire_date_count = sum(
        employee.hire_date is None for employee in employee_rows
    )

    inactive_missing_exit_date_count = sum(
        str(employee.employment_status or "").strip().lower() == "inactive"
        and employee.exit_date is None
        for employee in employee_rows
    )

    status_date_conflict_count = sum(
        str(employee.employment_status or "").strip().lower()
        in ("active", "on leave")
        and employee.exit_date is not None
        for employee in employee_rows
    )

    invalid_date_order_count = sum(
        employee.hire_date is not None
        and employee.exit_date is not None
        and employee.exit_date < employee.hire_date
        for employee in employee_rows
    )

    exits_during_period = [
        employee
        for employee in employee_rows
        if employee.exit_date is not None
        and period_start <= employee.exit_date <= today
    ]

    headcount_start = None
    headcount_end = None
    attrition_rate_pct = None
    retention_rate_pct = None

    data_complete = (
        missing_hire_date_count == 0
        and inactive_missing_exit_date_count == 0
        and status_date_conflict_count == 0
        and invalid_date_order_count == 0
    )

    if data_complete:
        opening_employees = [
            employee
            for employee in employee_rows
            if employee.hire_date <= period_start
            and (
                employee.exit_date is None
                or employee.exit_date > period_start
            )
        ]

        closing_employees = [
            employee
            for employee in employee_rows
            if employee.hire_date <= today
            and (
                employee.exit_date is None
                or employee.exit_date > today
            )
        ]

        retained_employees = [
            employee
            for employee in opening_employees
            if employee.exit_date is None or employee.exit_date > today
        ]

        headcount_start = len(opening_employees)
        headcount_end = len(closing_employees)
        average_headcount = (headcount_start + headcount_end) / 2

        if average_headcount > 0:
            attrition_rate_pct = round(
                len(exits_during_period) / average_headcount * 100, 2
            )

        if headcount_start > 0:
            retention_rate_pct = round(
                len(retained_employees) / headcount_start * 100, 2
            )

    # Use daily buckets for short periods and calendar-month buckets for
    # longer periods. All buckets are clipped to the selected date window.
    exit_trend = []

    if period in ("last_30_days", "month_to_date"):
        bucket_date = period_start
        while bucket_date <= today:
            exit_count = sum(
                employee.exit_date == bucket_date
                for employee in exits_during_period
            )
            exit_trend.append({
                "label": bucket_date.strftime("%d %b"),
                "date": bucket_date.isoformat(),
                "exits": exit_count,
            })
            bucket_date += timedelta(days=1)
    else:
        month_index = period_start.year * 12 + period_start.month - 1
        last_month_index = today.year * 12 + today.month - 1

        for index in range(month_index, last_month_index + 1):
            year = index // 12
            month = index % 12 + 1
            month_start = date(year, month, 1)

            if month == 12:
                next_month_start = date(year + 1, 1, 1)
            else:
                next_month_start = date(year, month + 1, 1)

            month_end = next_month_start - timedelta(days=1)
            bucket_start = max(month_start, period_start)
            bucket_end = min(month_end, today)

            exit_count = sum(
                bucket_start <= employee.exit_date <= bucket_end
                for employee in exits_during_period
            )

            exit_trend.append({
                "label": month_start.strftime("%b %Y"),
                "date": bucket_start.isoformat(),
                "exits": exit_count,
            })

    exit_history_complete = (
        inactive_missing_exit_date_count == 0
        and status_date_conflict_count == 0
        and invalid_date_order_count == 0
    )

    attrition_analytics = {
        "period_key": period,
        "period_label": period_label,
        "period_start": period_start.isoformat(),
        "period_end": today.isoformat(),
        "exits_during_period": len(exits_during_period),
        "headcount_start": headcount_start,
        "headcount_end": headcount_end,
        "attrition_rate_pct": attrition_rate_pct,
        "monthly_attrition_rate_pct": attrition_rate_pct,
        "retention_rate_pct": retention_rate_pct,
        "data_complete": data_complete,
        "missing_hire_date_count": missing_hire_date_count,
        "inactive_missing_exit_date_count": inactive_missing_exit_date_count,
        "status_date_conflict_count": status_date_conflict_count,
        "invalid_date_order_count": invalid_date_order_count,
        "exit_history_complete": exit_history_complete,
        "exit_trend": exit_trend,
    }

    return {
        "total_employees": total_employees,
        "attrition_analytics": attrition_analytics,
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
