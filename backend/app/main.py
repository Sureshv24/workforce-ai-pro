from fastapi import FastAPI
from app.api.v1.prediction_history import router as prediction_history_router
from app.api.v1.predictions import router as predictions_router

from app.api.v1.auth import router as auth_router
from app.api.v1.employees import router as employees_router
from app.api.v1.departments import router as departments_router
from app.api.v1.dashboard import router as dashboard_router

app = FastAPI(
    title="WorkForce AI Pro",
    description="HR Attrition Prediction and Workforce Intelligence",
    version="1.0.0",
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(prediction_history_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "WorkForce AI Pro"}
