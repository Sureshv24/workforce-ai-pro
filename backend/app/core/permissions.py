"""Centralized role-based access control for WorkForce AI Pro."""

from fastapi import HTTPException
from app.models.user import User


ADMIN = "ADMIN"
HR = "HR"
MANAGER = "MANAGER"
EMPLOYEE = "EMPLOYEE"

ALL_ROLES = frozenset({ADMIN, HR, MANAGER, EMPLOYEE})
WORKFORCE_ADMIN_ROLES = frozenset({ADMIN, HR})


def normalize_role(role: str | None) -> str:
    return (role or "").strip().upper()


def require_roles(user: User, *allowed_roles: str) -> User:
    """Allow only explicitly listed roles."""
    allowed = {normalize_role(role) for role in allowed_roles}

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive.")

    if normalize_role(user.role) not in allowed:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to perform this action.",
        )

    return user


def require_admin(user: User) -> User:
    return require_roles(user, ADMIN)


def require_hr(user: User) -> User:
    """Allow HR and administrators to manage workforce records."""
    return require_roles(user, ADMIN, HR)


def require_manager_or_hr(user: User) -> User:
    """Role gate only; team ownership must also be checked by the endpoint."""
    return require_roles(user, ADMIN, HR, MANAGER)


def require_self_or_hr(user: User, employee_id: int) -> User:
    """Allow HR/admin or an employee accessing their own employee record."""
    if normalize_role(user.role) in {ADMIN, HR}:
        return require_roles(user, ADMIN, HR)

    require_roles(user, EMPLOYEE)

    if user.employee_id is None or user.employee_id != employee_id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own employee record.",
        )

    return user


def require_manager_of_employee(
    user: User,
    employee_id: int,
    manager_employee_id: int | None,
) -> User:
    """Check team ownership after the caller loads the target employee."""
    role = normalize_role(user.role)

    if role in {ADMIN, HR}:
        return require_roles(user, ADMIN, HR)

    require_roles(user, MANAGER)

    if user.employee_id is None or manager_employee_id != user.employee_id:
        raise HTTPException(
            status_code=403,
            detail="You can only access employees assigned to your team.",
        )

    return user
