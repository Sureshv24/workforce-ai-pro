from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AttendanceStatus = Literal["Present", "Absent", "Late", "On Leave"]


class AttendanceCreate(BaseModel):
    employee_id: int = Field(gt=0)
    attendance_date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: AttendanceStatus = "Present"
    remarks: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_check_times(self):
        if self.check_in and self.check_out:
            if self.check_out < self.check_in:
                raise ValueError("Check-out cannot be earlier than check-in.")
        return self


class AttendanceUpdate(BaseModel):
    attendance_date: date | None = None
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: AttendanceStatus | None = None
    remarks: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_check_times(self):
        if self.check_in and self.check_out:
            if self.check_out < self.check_in:
                raise ValueError("Check-out cannot be earlier than check-in.")
        return self


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    attendance_date: date
    check_in: datetime | None
    check_out: datetime | None
    status: str
    remarks: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
