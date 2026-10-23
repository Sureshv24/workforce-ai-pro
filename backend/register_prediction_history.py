from pathlib import Path

path = Path("app/main.py")
source = path.read_text(encoding="utf-8-sig")

line = "from app.api.v1.prediction_history import router as prediction_history_router"

if line not in source:
    source = source.replace(
        "from fastapi import FastAPI",
        "from fastapi import FastAPI\n" + line,
        1,
    )

registration = 'app.include_router(prediction_history_router, prefix="/api/v1")'

if registration not in source:
    anchor = 'app.include_router(predictions_router, prefix="/api/v1")'
    if anchor not in source:
        raise SystemExit("Prediction router registration not found.")

    source = source.replace(
        anchor,
        anchor + "\n" + registration,
        1,
    )

path.write_text(source, encoding="utf-8")
print("Prediction history router registered!")
