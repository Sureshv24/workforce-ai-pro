from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

LeaveType = Literal["Casual", "Sick", "Annual", "Unpaid"]
LeaveStatus = Literal["Pending", "Approved", "Rejected"]


class LeaveRequestCreate(BaseModel):
    employee_id: int = Field(gt=0)
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date.")
        return self


class LeaveReview(BaseModel):
    status: Literal["Approved", "Rejected"]
    review_comment: str | None = Field(default=None, max_length=2000)


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    reviewed_by: int | None
    review_comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
