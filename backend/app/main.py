from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.prediction_history import router as prediction_history_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.risk_monitoring import router as risk_monitoring_router

from app.api.v1.auth import router as auth_router
from app.api.v1.employees import router as employees_router
from app.api.v1.departments import router as departments_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.leaves import router as leaves_router
from app.api.v1.leave_balances import router as leave_balances_router

from app.api.v1.payroll import router as payroll_router

from app.api.v1.notifications import router as notifications_router

from app.api.v1.chat import router as chat_router

from app.api.v1.documents import router as documents_router

app = FastAPI(
    title="WorkForce AI Pro",
    description="HR Attrition Prediction and Workforce Intelligence",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(attendance_router, prefix="/api/v1")
app.include_router(leaves_router, prefix='/api/v1')
app.include_router(leave_balances_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(datasets_router, prefix="/api/v1")
app.include_router(risk_monitoring_router, prefix="/api/v1")
app.include_router(prediction_history_router, prefix="/api/v1")
app.include_router(payroll_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "WorkForce AI Pro"}


