from pydantic import BaseModel, ConfigDict, Field, field_validator


class AttritionPredictionRequest(BaseModel):
    employee_id: int | None = Field(default=None, gt=0)
    age: int = Field(ge=18, le=100)
    monthly_income: float = Field(gt=0, le=10000000)
    years_at_company: int = Field(ge=0, le=80)
    job_satisfaction: int = Field(ge=1, le=4)
    work_life_balance: int = Field(ge=1, le=4)
    overtime: str
    years_since_promotion: int = Field(ge=0, le=80)
    distance_from_home: int = Field(ge=0, le=10000)

    @field_validator("overtime")
    @classmethod
    def validate_overtime(cls, value: str) -> str:
        value = value.strip().title()
        if value not in ("Yes", "No"):
            raise ValueError("overtime must be Yes or No")
        return value


class AttritionPredictionResponse(BaseModel):
    id: int
    employee_id: int | None
    predicted_attrition: bool
    risk_score: float
    risk_level: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
