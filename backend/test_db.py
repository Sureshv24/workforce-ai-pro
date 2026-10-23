from sqlalchemy import text
from app.db.session import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT DATABASE()"))
        print("MySQL connected successfully!")
        print("Database:", result.scalar())
except Exception as exc:
    print("Database connection failed:", exc)
