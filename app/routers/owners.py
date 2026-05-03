from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.database import get_db
from app.models import Owner
from app.schemas import OwnerCreate, OwnerUpdate, OwnerOut, OwnerPublicOut, OwnerListResponse
from app.auth import require_admin_key, require_user_key

router = APIRouter()


@router.post("", response_model=OwnerOut, status_code=201)
async def create_owner(
    body: OwnerCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    owner = Owner(name=body.name, description=body.description)
    db.add(owner)
    await db.commit()
    await db.refresh(owner)
    return owner


@router.get("/public/{owner_uuid}", response_model=OwnerPublicOut)
async def get_owner_public(
    owner_uuid: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_key),
):
    result = await db.execute(select(Owner).where(Owner.uuid == owner_uuid))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")
    return owner


@router.get("/{access_key}", response_model=OwnerOut)
async def get_owner(
    access_key: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    result = await db.execute(select(Owner).where(Owner.access_key == access_key))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")
    return owner


@router.patch("/{access_key}", response_model=OwnerOut)
async def update_owner(
    access_key: str,
    body: OwnerUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    result = await db.execute(select(Owner).where(Owner.access_key == access_key))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")
    owner.name = body.name
    owner.description = body.description
    await db.commit()
    await db.refresh(owner)
    return owner


@router.delete("/{access_key}", status_code=204)
async def delete_owner(
    access_key: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    result = await db.execute(select(Owner).where(Owner.uuid == access_key))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")
    await db.delete(owner)
    await db.commit()
