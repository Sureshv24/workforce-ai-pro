from getpass import getpass

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User

email = input("Enter your registered email: ").strip().lower()
password = getpass("Enter your login password: ")

with SessionLocal() as db:
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        print("User not found. Register the user first.")
    else:
        from app.core.security import verify_password

        if not verify_password(password, user.password_hash):
            print("Password verification failed. No changes made.")
        else:
            confirm = input(
                "Promote this account to ADMIN? Type YES to confirm: "
            ).strip()

            if confirm == "YES":
                user.role = "ADMIN"
                db.commit()
                print("Admin role assigned successfully.")
            else:
                print("Cancelled. No changes made.")
