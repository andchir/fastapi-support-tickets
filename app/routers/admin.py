from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Owner, Ticket
from app.schemas import (
    TicketOut,
    TicketWithComments,
    TicketStatusUpdate,
    TicketListResponse,
)
from app.auth import require_admin_key
from app.i18n import get_language, VALID_STATUSES, VALID_STATUSES_RU
from app.timeutil import local_day_start_utc_naive, local_next_day_start_utc_naive, utc_now_naive

router = APIRouter()


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    access_key: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if not access_key:
        raise HTTPException(status_code=422, detail="access_key_required")

    owner_result = await db.execute(select(Owner).where(Owner.access_key == access_key))
    owner = owner_result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=403, detail="invalid_access_key")

    filters = [Ticket.owner_id == owner.id]
    if status:
        filters.append(Ticket.status == status)
    if date_from:
        filters.append(Ticket.created_at >= local_day_start_utc_naive(date_from))
    if date_to:
        filters.append(Ticket.created_at < local_next_day_start_utc_naive(date_to))

    base = select(Ticket).options(selectinload(Ticket.owner))
    count_base = select(func.count()).select_from(Ticket)
    for cond in filters:
        base = base.where(cond)
        count_base = count_base.where(cond)

    total_result = await db.execute(count_base)
    total = int(total_result.scalar_one())

    offset = (page - 1) * page_size
    stmt = base.order_by(Ticket.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return TicketListResponse(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{ticket_uuid}", response_model=TicketWithComments)
async def get_ticket_admin(
    ticket_uuid: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
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


@router.patch("/{ticket_uuid}/status", response_model=TicketOut)
async def update_ticket_status(
    ticket_uuid: str,
    body: TicketStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    lang = get_language(request)
    valid = VALID_STATUSES_RU if lang == "ru" else VALID_STATUSES
    if body.status not in valid:
        raise HTTPException(
            status_code=400,
            detail={"key": "invalid_status", "ctx": {"values": ", ".join(sorted(valid))}},
        )
    result = await db.execute(
        select(Ticket)
        .where(Ticket.uuid == ticket_uuid)
        .options(selectinload(Ticket.owner))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket_not_found")
    ticket.status = body.status
    ticket.updated_at = utc_now_naive()
    await db.commit()
    await db.refresh(ticket)
    return ticket
