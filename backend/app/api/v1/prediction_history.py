from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.attrition_prediction import AttritionPrediction

router = APIRouter(
    prefix="/predictions",
    tags=["AI Predictions"],
)


@router.get("/history")
def prediction_history(
    employee_id: int | None = Query(default=None, gt=0),
    risk_level: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "HR"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail="Admin or HR permission required",
        )

    query = select(AttritionPrediction)

    if employee_id is not None:
        query = query.where(
            AttritionPrediction.employee_id == employee_id
        )

    if risk_level:
        normalized = risk_level.strip().title()
        if normalized not in ("Low", "Medium", "High"):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail="risk_level must be Low, Medium, or High",
            )
        query = query.where(
            AttritionPrediction.risk_level == normalized
        )

    query = query.order_by(
        AttritionPrediction.created_at.desc(),
        AttritionPrediction.id.desc(),
    )

    total = len(db.scalars(query).all())
    records = db.scalars(
        query.offset((page - 1) * page_size).limit(page_size)
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": item.id,
                "employee_id": item.employee_id,
                "predicted_attrition": item.predicted_attrition,
                "risk_score": item.risk_score,
                "risk_level": item.risk_level,
                "created_at": item.created_at.isoformat(),
            }
            for item in records
        ],
    }
