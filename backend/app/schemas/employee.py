from datetime import date

from pydantic import BaseModel, Field, ConfigDict


class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=150)
    department_id: int | None = None
    job_title: str | None = Field(default=None, max_length=100)
    hire_date: date | None = None
    exit_date: date | None = None
    employment_status: str = "Active"


class EmployeeUpdate(BaseModel):
    employee_code: str | None = Field(default=None, min_length=1, max_length=50)
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    department_id: int | None = None
    job_title: str | None = Field(default=None, max_length=100)
    hire_date: date | None = None
    exit_date: date | None = None
    employment_status: str | None = None


class EmployeeResponse(EmployeeCreate):
    id: int
    account_linked: bool
    model_config = ConfigDict(from_attributes=True)
