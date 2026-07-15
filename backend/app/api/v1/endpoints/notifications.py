from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter()


@router.get("")
async def list_notifications(
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Notification).where(
        Notification.organization_id == current_user.organization_id,
        Notification.user_id == current_user.id,
    )
    if unread_only:
        query = query.where(Notification.read_at.is_(None))

    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Notification.created_at.desc()).offset(offset).limit(page_size))
    notifications = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "notification_type": n.notification_type,
            "title": n.title,
            "content": n.content,
            "priority": n.priority,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "action_required": n.action_required,
            "related_entity_type": n.related_entity_type,
            "related_entity_id": str(n.related_entity_id) if n.related_entity_id else None,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True}


@router.patch("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"success": True}
