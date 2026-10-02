"""Notifications API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
import uuid

from app.database import get_db
from app.auth.security import get_current_user
from app.models import Notification, User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query = select(Notification).where(Notification.user_id == current_user.id).order_by(
            Notification.created_at.desc()
        )
        if unread_only:
            query = query.where(Notification.is_read == False)

        result = await db.execute(query.limit(limit))
        notifications = result.scalars().all()

        # Count unread
        unread_result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == current_user.id, Notification.is_read == False
            )
        )
        unread_count = unread_result.scalar_one()

        return {
            "unread_count": unread_count,
            "items": [
                {
                    "id": str(n.id),
                    "type": n.type.value,
                    "title": n.title,
                    "message": n.message,
                    "severity": n.severity.value if n.severity else None,
                    "entity_type": n.entity_type,
                    "entity_id": str(n.entity_id) if n.entity_id else None,
                    "is_read": n.is_read,
                    "action_url": n.action_url,
                    "created_at": n.created_at.isoformat(),
                }
                for n in notifications
            ],
        }
    except Exception:
        from app.services.demo_store import DEMO_NOTIFICATIONS
        items = [n for n in DEMO_NOTIFICATIONS if not (unread_only and n["is_read"])]
        return {
            "unread_count": sum(1 for n in items if not n["is_read"]),
            "items": items[:limit],
        }


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime
    await db.execute(
        update(Notification)
        .where(Notification.id == uuid.UUID(notification_id), Notification.user_id == current_user.id)
        .values(is_read=True, read_at=datetime.utcnow())
    )
    return {"status": "marked_read"}


@router.patch("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True, read_at=datetime.utcnow())
    )
    return {"status": "all_marked_read"}
