from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user_key
from app.database import get_db
from app.models import Message
from app.schemas import MessageCreate, MessageListResponse, MessageOut

router = APIRouter()

VALID_STATUSES = frozenset({"new", "read"})


@router.post("", response_model=MessageOut, status_code=201)
async def create_message(
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    message = Message(
        owner=body.owner,
        author=body.author,
        text=body.text,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("", response_model=MessageListResponse)
async def list_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="new or read"),
    owner: Optional[str] = Query(None, description="Filter by owner id (UUID or string)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid values: {', '.join(sorted(VALID_STATUSES))}",
        )

    filters = []
    if status is not None:
        filters.append(Message.status == status)
    if owner is not None:
        filters.append(Message.owner == owner)

    base = select(Message)
    count_base = select(func.count()).select_from(Message)
    for cond in filters:
        base = base.where(cond)
        count_base = count_base.where(cond)

    total_result = await db.execute(count_base)
    total = int(total_result.scalar_one())

    offset = (page - 1) * page_size
    stmt = base.order_by(Message.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return MessageListResponse(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
    )
