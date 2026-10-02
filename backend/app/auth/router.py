from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import User
from app.auth.security import (
    verify_password, create_access_token, hash_password, get_current_user
)
from app.config import settings
from app.audit.service import log_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str
    mine_id: Optional[str] = None
    expires_in: int


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. Try DB lookup if active
    try:
        result = await db.execute(
            select(User).where(User.email.ilike(form_data.email.strip()), User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if user and not verify_password(form_data.password, user.hashed_password):
            user = None
    except Exception:
        user = None

    # 2. Demo fallback when DB is offline or for demo credentials
    if not user:
        from app.auth.demo_users import get_demo_user, DEMO_USERS_MAP
        email_clean = form_data.email.strip().lower()
        demo_meta = DEMO_USERS_MAP.get(email_clean)
        if demo_meta:
            # Match specific demo password or master Admin password
            if form_data.password in (demo_meta["password"], "Admin@1234"):
                user = get_demo_user(email_clean)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    try:
        # Update last login
        await db.execute(
            update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
        )
        await db.commit()

        # Log audit
        await log_audit(
            db=db,
            user_id=str(user.id),
            action="login",
            entity_type="user",
            entity_id=str(user.id),
        )
    except Exception:
        pass

    token = create_access_token({"sub": str(user.id), "role": user.role.value})

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        mine_id=str(user.mine_id) if user.mine_id else None,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "employee_id": current_user.employee_id,
        "department": current_user.department,
        "mine_id": str(current_user.mine_id) if current_user.mine_id else None,
        "subsidiary_id": str(current_user.subsidiary_id) if current_user.subsidiary_id else None,
        "preferred_language": current_user.preferred_language,
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await log_audit(
        db=db,
        user_id=str(current_user.id),
        action="logout",
        entity_type="user",
        entity_id=str(current_user.id),
    )
    return {"message": "Logged out successfully"}
