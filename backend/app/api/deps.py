import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        subject = payload.get("sub")
        if not subject:
            raise unauthorized
        user_id = int(subject)
    except (InvalidTokenError, ValueError, TypeError):
        raise unauthorized

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized

    return user
