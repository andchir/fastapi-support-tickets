import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Owner, Ticket
from app.schemas import TicketOut, TicketWithComments, TicketStatusUpdate
from app.auth import require_user_key
from app.config import settings
from app.i18n import get_language, get_status
from app.timeutil import utc_now_naive

router = APIRouter()


ALLOWED_MIME_PREFIXES = ("image/", "video/")


async def save_upload(file: UploadFile) -> str:
    content_type = file.content_type or ""
    if not any(content_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail="only_image_video_allowed",
        )
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(settings.upload_dir, filename)
    os.makedirs(settings.upload_dir, exist_ok=True)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return path


@router.post("", response_model=TicketOut, status_code=201)
async def create_ticket(
    request: Request,
    owner_uuid: str = Form(...),
    subject: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    owner_result = await db.execute(select(Owner).where(Owner.uuid == owner_uuid))
    owner = owner_result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")

    file_path = None
    if file and file.filename:
        file_path = await save_upload(file)

    lang = get_language(request)
    ticket = Ticket(
        owner_id=owner.id,
        subject=subject,
        name=name,
        email=email,
        message=message,
        file_path=file_path,
        status=get_status("new", lang),
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    await db.refresh(ticket, ["owner"])
    return ticket


@router.get("/{ticket_uuid}", response_model=TicketWithComments)
async def get_ticket(
    ticket_uuid: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    result = await db.execute(
        select(Ticket)
        .where(Ticket.uuid == ticket_uuid)
        .options(selectinload(Ticket.owner), selectinload(Ticket.comments))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket_not_found")
    return ticket


@router.patch("/{ticket_uuid}/close", response_model=TicketOut)
async def close_ticket(
    ticket_uuid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    result = await db.execute(
        select(Ticket)
        .where(Ticket.uuid == ticket_uuid)
        .options(selectinload(Ticket.owner))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket_not_found")
    lang = get_language(request)
    ticket.status = get_status("closed", lang)
    ticket.updated_at = utc_now_naive()
    await db.commit()
    await db.refresh(ticket)
    return ticket
