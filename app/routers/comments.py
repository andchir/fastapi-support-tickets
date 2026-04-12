import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Ticket, Comment
from app.schemas import CommentOut
from app.auth import require_user_key
from app.config import settings

router = APIRouter()


ALLOWED_MIME_PREFIXES = ("image/", "video/")


async def save_upload(file: UploadFile) -> str:
    content_type = file.content_type or ""
    if not any(content_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail="Only image and video files are allowed",
        )
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(settings.upload_dir, filename)
    os.makedirs(settings.upload_dir, exist_ok=True)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return path


@router.post("/{ticket_uuid}/comments", response_model=CommentOut, status_code=201)
async def add_comment(
    ticket_uuid: str,
    author: str = Form(''),
    text: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    result = await db.execute(select(Ticket).where(Ticket.uuid == ticket_uuid))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    file_path = None
    if file and file.filename:
        file_path = await save_upload(file)

    comment = Comment(
        ticket_id=ticket.id,
        author=author,
        text=text,
        file_path=file_path,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment
