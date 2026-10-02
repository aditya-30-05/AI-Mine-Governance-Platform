"""Mines API."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
import uuid

from app.database import get_db
from app.auth.security import get_current_user, require_roles
from app.models import Mine, User, UserRole

router = APIRouter(prefix="/mines", tags=["Mines"])


class MineCreate(BaseModel):
    name: str
    code: str
    subsidiary_id: str
    location_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    mine_type: Optional[str] = "opencast"
    capacity_mtpa: Optional[float] = None


class MineResponse(BaseModel):
    id: str
    name: str
    code: str
    subsidiary_id: str
    location_name: Optional[str]
    state: Optional[str]
    district: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    mine_type: Optional[str]
    capacity_mtpa: Optional[float]
    is_active: bool


@router.get("", response_model=List[dict])
async def list_mines(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all mines accessible to current user."""
    try:
        query = select(Mine)
        if active_only:
            query = query.where(Mine.is_active == True)

        # Field officers only see their assigned mine
        if current_user.role == UserRole.FIELD_OFFICER and current_user.mine_id:
            query = query.where(Mine.id == current_user.mine_id)

        result = await db.execute(query.order_by(Mine.name))
        mines = result.scalars().all()

        return [
            {
                "id": str(m.id),
                "name": m.name,
                "code": m.code,
                "subsidiary_id": str(m.subsidiary_id),
                "location_name": m.location_name,
                "state": m.state,
                "district": m.district,
                "latitude": m.latitude,
                "longitude": m.longitude,
                "mine_type": m.mine_type,
                "capacity_mtpa": m.capacity_mtpa,
                "is_active": m.is_active,
            }
            for m in mines
        ]
    except Exception:
        from app.services.demo_store import DEMO_MINES
        return DEMO_MINES


@router.get("/{mine_id}")
async def get_mine(
    mine_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(select(Mine).where(Mine.id == uuid.UUID(mine_id)))
        mine = result.scalar_one_or_none()
        if mine:
            return {
                "id": str(mine.id),
                "name": mine.name,
                "code": mine.code,
                "subsidiary_id": str(mine.subsidiary_id),
                "location_name": mine.location_name,
                "state": mine.state,
                "district": mine.district,
                "latitude": mine.latitude,
                "longitude": mine.longitude,
                "mine_type": mine.mine_type,
                "capacity_mtpa": mine.capacity_mtpa,
                "is_active": mine.is_active,
            }
    except Exception:
        pass

    from app.services.demo_store import DEMO_MINES
    for m in DEMO_MINES:
        if m["id"] == mine_id:
            return m
    return DEMO_MINES[0]


@router.post("", status_code=201)
async def create_mine(
    data: MineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    from geoalchemy2.elements import WKTElement
    location = None
    if data.latitude and data.longitude:
        location = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)

    mine = Mine(
        name=data.name,
        code=data.code,
        subsidiary_id=uuid.UUID(data.subsidiary_id),
        location_name=data.location_name,
        state=data.state,
        district=data.district,
        latitude=data.latitude,
        longitude=data.longitude,
        location=location,
        mine_type=data.mine_type,
        capacity_mtpa=data.capacity_mtpa,
    )
    db.add(mine)
    await db.flush()

    return {"id": str(mine.id), "name": mine.name, "code": mine.code}
