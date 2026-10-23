from pathlib import Path

path = Path("app/main.py")
source = path.read_text(encoding="utf-8-sig")

import_line = "from app.api.v1.predictions import router as predictions_router"

if import_line not in source:
    source = source.replace(
        "from fastapi import FastAPI",
        "from fastapi import FastAPI\n" + import_line,
        1,
    )

include_line = 'app.include_router(predictions_router, prefix="/api/v1")'

if include_line not in source:
    anchor = 'app.include_router(dashboard_router, prefix="/api/v1")'
    if anchor not in source:
        raise SystemExit(
            "Dashboard router registration not found. main.py was not updated."
        )
    source = source.replace(anchor, anchor + "\n" + include_line, 1)

path.write_text(source, encoding="utf-8")
print("Prediction router registered in app/main.py")
