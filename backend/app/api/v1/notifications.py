from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def role_of(user: User) -> str:
    return (user.role or "").strip().upper()


def require_hr_or_admin(user: User):
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")
    if role_of(user) not in {"ADMIN", "HR"}:
        raise HTTPException(status_code=403, detail="Admin or HR permission required.")


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr_or_admin(current_user)

    recipient = db.get(User, payload.user_id)
    if recipient is None or not recipient.is_active:
        raise HTTPException(status_code=404, detail="Active recipient account not found.")

    notification = Notification(
        user_id=payload.user_id,
        title=payload.title.strip(),
        message=payload.message.strip(),
        category=payload.category.strip().upper(),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.get("/", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")

    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))

    query = query.order_by(Notification.created_at.desc(), Notification.id.desc())
    return list(db.scalars(query.offset(offset).limit(limit)).all())


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")

    count = db.scalar(
        select(Notification.id).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    # Count all matching records using a dedicated SQL count.
    from sqlalchemy import func
    total = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    return {"unread_count": total or 0}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")

    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")

    records = db.scalars(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    ).all()
    for record in records:
        record.is_read = True
    db.commit()
    return {"updated_count": len(records)}
