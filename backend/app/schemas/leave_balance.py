from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BalanceLeaveType = Literal["Casual", "Sick", "Annual", "Unpaid"]


class LeaveBalanceCreate(BaseModel):
    employee_id: int = Field(gt=0)
    leave_type: BalanceLeaveType
    year: int = Field(ge=2000, le=2100)
    total_days: int = Field(ge=0, le=365)


class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    year: int
    total_days: int
    used_days: int
    remaining_days: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
