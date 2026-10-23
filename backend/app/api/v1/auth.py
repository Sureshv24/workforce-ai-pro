from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(
        select(User).where(User.email == str(data.email).lower())
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    # Public registration always creates an EMPLOYEE.
    # Privileged roles must be assigned by an authorized administrator.
    user = User(
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        role="EMPLOYEE",
    )
    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(
        select(User).where(User.email == str(data.email).lower())
    )

    if (
        user is None
        or not verify_password(data.password, user.password_hash)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
