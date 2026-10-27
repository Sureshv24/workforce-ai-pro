import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.document import EmployeeDocument
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

# Files stay outside the public frontend/static directory.
STORAGE_DIR = Path(os.getenv("DOCUMENT_STORAGE_DIR", "private_uploads")).resolve()
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg",
    ".doc", ".docx", ".txt", ".csv", ".xlsx"
}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}


def role_of(user: User) -> str:
    return (user.role or "").strip().upper()


def require_active(user: User):
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account.")


def can_access_document(user: User, document: EmployeeDocument):
    require_active(user)
    if role_of(user) in {"ADMIN", "HR"}:
        return
    if document.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found.")


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(default="GENERAL", max_length=50),
    description: str | None = Form(default=None, max_length=2000),
    employee_id: int | None = Form(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active(current_user)

    original_name = Path(file.filename or "").name.strip()
    extension = Path(original_name).suffix.lower()
    if not original_name or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="File type is not allowed.")

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported content type.")

    if employee_id is not None:
        if role_of(current_user) not in {"ADMIN", "HR"}:
            raise HTTPException(
                status_code=403,
                detail="Only Admin/HR can assign documents to an employee.",
            )
        if db.get(Employee, employee_id) is None:
            raise HTTPException(status_code=404, detail="Employee not found.")

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    storage_name = f"{uuid.uuid4().hex}{extension}"
    destination = (STORAGE_DIR / storage_name).resolve()

    if destination.parent != STORAGE_DIR:
        raise HTTPException(status_code=400, detail="Invalid storage path.")

    size = 0
    try:
        with destination.open("xb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Maximum upload size is 10 MB.",
                    )
                output.write(chunk)

        if size == 0:
            raise HTTPException(status_code=422, detail="Empty files are not allowed.")

        record = EmployeeDocument(
            owner_user_id=current_user.id,
            employee_id=employee_id if employee_id is not None else current_user.employee_id,
            original_filename=original_name[:255],
            storage_filename=storage_name,
            content_type=file.content_type or "application/octet-stream",
            file_size=size,
            category=category.strip().upper() or "GENERAL",
            description=description.strip() if description else None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        if destination.exists():
            destination.unlink()
        raise
    finally:
        await file.close()


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active(current_user)
    if not 1 <= limit <= 100 or offset < 0:
        raise HTTPException(status_code=422, detail="Invalid pagination values.")

    query = select(EmployeeDocument)
    if role_of(current_user) not in {"ADMIN", "HR"}:
        query = query.where(EmployeeDocument.owner_user_id == current_user.id)

    query = query.order_by(
        EmployeeDocument.created_at.desc(), EmployeeDocument.id.desc()
    ).offset(offset).limit(limit)
    return list(db.scalars(query).all())


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active(current_user)
    document = db.get(EmployeeDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    can_access_document(current_user, document)
    path = (STORAGE_DIR / document.storage_filename).resolve()
    if path.parent != STORAGE_DIR or not path.is_file():
        raise HTTPException(status_code=404, detail="Stored file not found.")

    return FileResponse(
        path=str(path),
        media_type=document.content_type,
        filename=document.original_filename,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_active(current_user)
    document = db.get(EmployeeDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    can_access_document(current_user, document)
    path = (STORAGE_DIR / document.storage_filename).resolve()

    db.delete(document)
    db.commit()

    if path.parent == STORAGE_DIR and path.is_file():
        path.unlink()

    return None
