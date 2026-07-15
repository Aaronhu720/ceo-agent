from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("")
async def list_audit_logs(
    resource_type: str | None = None,
    action: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AuditLog).where(AuditLog.organization_id == current_user.organization_id)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if action:
        query = query.where(AuditLog.action == action)

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "agent_id": str(log.agent_id) if log.agent_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
