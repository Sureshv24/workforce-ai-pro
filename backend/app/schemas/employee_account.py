from pydantic import BaseModel, EmailStr


class EmployeeAccountLink(BaseModel):
    email: EmailStr
