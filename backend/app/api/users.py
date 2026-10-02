"""Users API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import uuid

from app.database import get_db
from app.auth.security import get_current_user, require_roles
from app.models import User, UserRole
from app.auth.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    employee_id: str
    email: str
    full_name: str
    password: str
    role: str = "field_officer"
    phone: Optional[str] = None
    department: Optional[str] = None
    mine_id: Optional[str] = None
    subsidiary_id: Optional[str] = None
    preferred_language: str = "en"


@router.get("")
async def list_users(
    role: Optional[str] = Query(None),
    mine_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MINE_MANAGER, UserRole.CORPORATE_MANAGER)),
):
    query = select(User).where(User.is_active == True).order_by(User.full_name)

    if role:
        query = query.where(User.role == UserRole(role))
    if mine_id:
        query = query.where(User.mine_id == uuid.UUID(mine_id))

    result = await db.execute(query.limit(limit))
    users = result.scalars().all()

    return [
        {
            "id": str(u.id),
            "employee_id": u.employee_id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "phone": u.phone,
            "department": u.department,
            "mine_id": str(u.mine_id) if u.mine_id else None,
            "subsidiary_id": str(u.subsidiary_id) if u.subsidiary_id else None,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]


@router.post("", status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    # Check uniqueness
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        employee_id=data.employee_id,
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=UserRole(data.role),
        phone=data.phone,
        department=data.department,
        mine_id=uuid.UUID(data.mine_id) if data.mine_id else None,
        subsidiary_id=uuid.UUID(data.subsidiary_id) if data.subsidiary_id else None,
        preferred_language=data.preferred_language,
    )
    db.add(user)
    await db.flush()

    return {"id": str(user.id), "email": user.email, "role": user.role.value}
