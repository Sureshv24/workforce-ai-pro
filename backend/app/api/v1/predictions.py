from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.attrition_prediction import AttritionPrediction
from app.schemas.prediction import (
    AttritionPredictionRequest,
    AttritionPredictionResponse,
)

router = APIRouter(prefix="/predictions", tags=["AI Predictions"])

MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "ml" / "models" / "attrition_model.joblib"
)

try:
    model = joblib.load(MODEL_PATH)
except Exception as exc:
    raise RuntimeError(
        f"Could not load attrition model at {MODEL_PATH}. Train it first."
    ) from exc


@router.post(
    "/attrition",
    response_model=AttritionPredictionResponse,
)
def predict_attrition(
    data: AttritionPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=403,
            detail="Admin or HR permission required",
        )

    if data.employee_id is not None:
        employee = db.get(Employee, data.employee_id)
        if employee is None:
            raise HTTPException(
                status_code=404,
                detail="Employee not found",
            )

    features = pd.DataFrame([{
        "age": data.age,
        "monthly_income": data.monthly_income,
        "years_at_company": data.years_at_company,
        "job_satisfaction": data.job_satisfaction,
        "work_life_balance": data.work_life_balance,
        "overtime": data.overtime,
        "years_since_promotion": data.years_since_promotion,
        "distance_from_home": data.distance_from_home,
    }])

    try:
        probability = float(model.predict_proba(features)[0][1])
        predicted = bool(model.predict(features)[0])
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check the trained model.",
        )

    if probability >= 0.70:
        risk_level = "High"
    elif probability >= 0.40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    record = AttritionPrediction(
        employee_id=data.employee_id,
        predicted_attrition=predicted,
        risk_score=round(probability * 100, 2),
        risk_level=risk_level,
        age=data.age,
        monthly_income=data.monthly_income,
        years_at_company=data.years_at_company,
        job_satisfaction=data.job_satisfaction,
        work_life_balance=data.work_life_balance,
        overtime=data.overtime,
        years_since_promotion=data.years_since_promotion,
        distance_from_home=data.distance_from_home,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save prediction to database",
        )

    return {
        "id": record.id,
        "employee_id": record.employee_id,
        "predicted_attrition": record.predicted_attrition,
        "risk_score": record.risk_score,
        "risk_level": record.risk_level,
        "created_at": record.created_at.isoformat(),
    }
