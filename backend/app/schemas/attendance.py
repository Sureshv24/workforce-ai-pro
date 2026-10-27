from datetime import date, datetime, time, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AttendanceStatus = Literal["Present", "Absent", "Late", "On Leave"]


class AttendanceCreate(BaseModel):
    employee_id: int = Field(gt=0)
    attendance_date: date
    shift_id: int | None = Field(default=None, gt=0)
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
    shift_id: int | None = Field(default=None, gt=0)
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
    shift_id: int | None = None
    shift_name: str | None = None
    worked_minutes: int | None = None
    overtime_minutes: int | None = None
    check_in: datetime | None
    check_out: datetime | None
    status: str
    remarks: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShiftCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_time: time
    end_time: time
    break_minutes: int = Field(default=60, ge=0, le=720)

    @model_validator(mode="after")
    def validate_shift(self):
        start = datetime.combine(date.min, self.start_time)
        end = datetime.combine(date.min, self.end_time)
        if end <= start:
            end += timedelta(days=1)
        duration = int((end - start).total_seconds() // 60)
        if self.break_minutes >= duration:
            raise ValueError("Break must be shorter than the shift duration.")
        return self


class ShiftUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_time: time | None = None
    end_time: time | None = None
    break_minutes: int | None = Field(default=None, ge=0, le=720)


class ShiftResponse(BaseModel):
    id: int
    name: str
    start_time: time
    end_time: time
    break_minutes: int
    expected_work_minutes: int
    model_config = ConfigDict(from_attributes=True)
