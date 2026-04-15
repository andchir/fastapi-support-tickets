from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.database import get_db
from app.models import Owner
from app.schemas import OwnerCreate, OwnerUpdate, OwnerOut, OwnerListResponse
from app.auth import require_admin_key

router = APIRouter()


@router.post("", response_model=OwnerOut, status_code=201)
async def create_owner(
    body: OwnerCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    owner = Owner(name=body.name)
    db.add(owner)
    await db.commit()
    await db.refresh(owner)
    return owner


@router.get("/{owner_uuid}", response_model=OwnerOut)
async def get_owner(
    owner_uuid: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    result = await db.execute(select(Owner).where(Owner.uuid == owner_uuid))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")
    return owner


@router.patch("/{owner_uuid}", response_model=OwnerOut)
async def update_owner(
    owner_uuid: str,
    body: OwnerUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    result = await db.execute(select(Owner).where(Owner.uuid == owner_uuid))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")
    owner.name = body.name
    await db.commit()
    await db.refresh(owner)
    return owner


@router.delete("/{owner_uuid}", status_code=204)
async def delete_owner(
    owner_uuid: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    result = await db.execute(select(Owner).where(Owner.uuid == owner_uuid))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")
    await db.delete(owner)
    await db.commit()
