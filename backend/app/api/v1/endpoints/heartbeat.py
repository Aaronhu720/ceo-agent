from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.heartbeat import HeartbeatRule, HeartbeatRun

router = APIRouter()


class HeartbeatRuleCreate(BaseModel):
    name: str
    description: str | None = None
    agent_id: UUID | None = None
    frequency_type: str
    cron_expression: str | None = None
    check_type: str
    conditions_json: dict | None = None
    action_json: dict | None = None
    priority: str = "normal"


class HeartbeatRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    frequency_type: str | None = None
    cron_expression: str | None = None
    enabled: bool | None = None
    priority: str | None = None


@router.get("")
async def list_heartbeat_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HeartbeatRule)
        .where(HeartbeatRule.organization_id == current_user.organization_id)
        .order_by(HeartbeatRule.created_at.desc())
    )
    rules = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "frequency_type": r.frequency_type,
            "cron_expression": r.cron_expression,
            "check_type": r.check_type,
            "priority": r.priority,
            "enabled": r.enabled,
            "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
            "next_run_at": r.next_run_at.isoformat() if r.next_run_at else None,
        }
        for r in rules
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_heartbeat_rule(
    req: HeartbeatRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = HeartbeatRule(
        organization_id=current_user.organization_id,
        **req.model_dump(),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"id": str(rule.id), "name": rule.name}


@router.patch("/{rule_id}")
async def update_heartbeat_rule(
    rule_id: UUID,
    req: HeartbeatRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HeartbeatRule).where(
            HeartbeatRule.id == rule_id,
            HeartbeatRule.organization_id == current_user.organization_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    await db.commit()
    return {"success": True}


@router.post("/{rule_id}/run")
async def trigger_heartbeat_run(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HeartbeatRule).where(
            HeartbeatRule.id == rule_id,
            HeartbeatRule.organization_id == current_user.organization_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"success": True, "message": "Heartbeat run queued"}


@router.get("/runs")
async def list_heartbeat_runs(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(HeartbeatRun)
        .join(HeartbeatRule, HeartbeatRun.heartbeat_rule_id == HeartbeatRule.id)
        .where(HeartbeatRule.organization_id == current_user.organization_id)
        .order_by(HeartbeatRun.started_at.desc())
        .offset(offset).limit(page_size)
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "heartbeat_rule_id": str(r.heartbeat_rule_id),
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "findings_json": r.findings_json,
            "notification_sent": r.notification_sent,
        }
        for r in runs
    ]
