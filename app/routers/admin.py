from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Ticket
from app.schemas import TicketOut, TicketWithComments, TicketStatusUpdate, TicketListItem
from app.auth import require_admin_key

router = APIRouter()

VALID_STATUSES = {"new", "in_progress", "answered", "closed", "deferred"}


@router.get("", response_model=list[TicketListItem])
async def list_tickets(
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    stmt = select(Ticket)
    if status:
        stmt = stmt.where(Ticket.status == status)
    if date_from:
        stmt = stmt.where(Ticket.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        stmt = stmt.where(Ticket.created_at <= datetime.combine(date_to, datetime.max.time()))
    stmt = stmt.order_by(Ticket.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{ticket_uuid}", response_model=TicketWithComments)
async def get_ticket_admin(
    ticket_uuid: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    result = await db.execute(select(Ticket).where(Ticket.uuid == ticket_uuid))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await db.refresh(ticket, ["comments"])
    return ticket


@router.patch("/{ticket_uuid}/status", response_model=TicketOut)
async def update_ticket_status(
    ticket_uuid: str,
    body: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid values: {', '.join(VALID_STATUSES)}")
    result = await db.execute(select(Ticket).where(Ticket.uuid == ticket_uuid))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = body.status
    ticket.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(ticket)
    return ticket
