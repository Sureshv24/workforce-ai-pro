from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PayrollCreate(BaseModel):
    employee_id: int = Field(gt=0)
    pay_period_start: date
    pay_period_end: date
    basic_salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    allowances: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    deductions: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    status: Literal["DRAFT", "APPROVED", "PAID", "CANCELLED"] = "DRAFT"
    payment_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_payroll(self):
        if self.pay_period_end < self.pay_period_start:
            raise ValueError("Pay period end must be on or after its start.")
        if self.deductions > self.basic_salary + self.allowances:
            raise ValueError("Deductions cannot exceed gross salary.")
        if self.status == "PAID" and self.payment_date is None:
            raise ValueError("A payment date is required for PAID payroll.")
        self.currency = self.currency.upper()
        return self


class PayrollUpdate(BaseModel):
    basic_salary: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    allowances: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    deductions: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    status: Literal["DRAFT", "APPROVED", "PAID", "CANCELLED"] | None = None
    payment_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class PayrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    pay_period_start: date
    pay_period_end: date
    basic_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    gross_salary: Decimal
    net_salary: Decimal
    currency: str
    status: str
    payment_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
