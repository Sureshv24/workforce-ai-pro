from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


def require_active(user: User):
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")


@router.post(
    "/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active(current_user)

    if payload.recipient_id == current_user.id:
        raise HTTPException(status_code=422, detail="You cannot message yourself.")

    recipient = db.get(User, payload.recipient_id)
    if recipient is None or not recipient.is_active:
        raise HTTPException(status_code=404, detail="Active recipient not found.")

    record = ChatMessage(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        message=payload.message.strip(),
    )
    if not record.message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/messages", response_model=list[ChatMessageResponse])
def conversation_history(
    with_user_id: int = Query(gt=0),
    limit: int = Query(default=50, ge=1, le=100),
    before_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active(current_user)

    if with_user_id == current_user.id:
        raise HTTPException(status_code=422, detail="Choose another user.")

    other_user = db.get(User, with_user_id)
    if other_user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    query = select(ChatMessage).where(
        or_(
            and_(
                ChatMessage.sender_id == current_user.id,
                ChatMessage.recipient_id == with_user_id,
            ),
            and_(
                ChatMessage.sender_id == with_user_id,
                ChatMessage.recipient_id == current_user.id,
            ),
        )
    )

    if before_id is not None:
        query = query.where(ChatMessage.id < before_id)

    # Return chronological order for display.
    records = db.scalars(
        query.order_by(ChatMessage.id.desc()).limit(limit)
    ).all()
    return list(reversed(records))


@router.patch("/messages/{message_id}/read", response_model=ChatMessageResponse)
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active(current_user)

    record = db.get(ChatMessage, message_id)
    if record is None or record.recipient_id != current_user.id:
        # Avoid revealing whether another user's message exists.
        raise HTTPException(status_code=404, detail="Received message not found.")

    if not record.is_read:
        record.is_read = True
        record.read_at = datetime.utcnow()
        db.commit()
        db.refresh(record)

    return record


@router.get("/unread-count")
def unread_message_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import func

    require_active(current_user)
    total = db.scalar(
        select(func.count()).select_from(ChatMessage).where(
            ChatMessage.recipient_id == current_user.id,
            ChatMessage.is_read.is_(False),
        )
    )
    return {"unread_count": total or 0}
