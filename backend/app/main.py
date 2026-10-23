from fastapi import FastAPI

app = FastAPI(
    title="WorkForce AI Pro",
    description="HR Attrition Prediction and Workforce Intelligence",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "WorkForce AI Pro",
    }