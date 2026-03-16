import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Ticket
from app.schemas import TicketOut, TicketWithComments, TicketStatusUpdate
from app.auth import require_user_key
from app.config import settings

router = APIRouter()


async def save_upload(file: UploadFile) -> str:
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
    subject: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    file_path = None
    if file and file.filename:
        file_path = await save_upload(file)

    ticket = Ticket(
        subject=subject,
        name=name,
        email=email,
        message=message,
        file_path=file_path,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/{ticket_uuid}", response_model=TicketWithComments)
async def get_ticket(
    ticket_uuid: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    result = await db.execute(select(Ticket).where(Ticket.uuid == ticket_uuid))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    # eagerly load comments
    await db.refresh(ticket, ["comments"])
    return ticket


@router.patch("/{ticket_uuid}/close", response_model=TicketOut)
async def close_ticket(
    ticket_uuid: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    result = await db.execute(select(Ticket).where(Ticket.uuid == ticket_uuid))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "closed"
    ticket.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(ticket)
    return ticket
