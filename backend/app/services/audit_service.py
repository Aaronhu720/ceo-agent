from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    organization_id: UUID,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    user_id: UUID | None = None,
    agent_id: UUID | None = None,
    before_json: dict | None = None,
    after_json: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    log = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        agent_id=agent_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before_json=before_json,
        after_json=after_json,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    await db.flush()
    return log
