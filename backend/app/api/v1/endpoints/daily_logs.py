from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.daily_log import DailyLog

router = APIRouter()


@router.get("/today")
async def get_today_log(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.organization_id == current_user.organization_id,
            DailyLog.log_date == today,
        ).order_by(DailyLog.created_at.desc())
    )
    log = result.scalar_one_or_none()
    if not log:
        return None

    return {
        "id": str(log.id),
        "log_date": log.log_date.isoformat(),
        "summary": log.summary,
        "tasks_json": log.tasks_json,
        "risks_json": log.risks_json,
        "decisions_json": log.decisions_json,
        "tomorrow_priorities_json": log.tomorrow_priorities_json,
        "confirmed_by_user": log.confirmed_by_user,
        "created_at": log.created_at.isoformat(),
    }


@router.get("")
async def list_logs(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.organization_id == current_user.organization_id,
        ).order_by(DailyLog.log_date.desc()).offset(offset).limit(page_size)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "log_date": log.log_date.isoformat(),
            "summary": log.summary,
            "confirmed_by_user": log.confirmed_by_user,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.post("/generate")
async def generate_briefing_now(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger a morning briefing generation."""
    from app.workers.heartbeat_tasks import _gather_business_context, _call_ai_for_briefing
    from app.models.notification import Notification

    org_id = current_user.organization_id
    context = await _gather_business_context(db, org_id)
    ai_summary = await _call_ai_for_briefing(context, "morning")

    today = date.today()

    existing = await db.execute(
        select(DailyLog).where(
            DailyLog.organization_id == org_id,
            DailyLog.log_date == today,
        )
    )
    old_log = existing.scalar_one_or_none()
    if old_log:
        old_log.summary = ai_summary
        old_log.tasks_json = context["tasks"]
        old_log.risks_json = {"items": context["risks"]}
        old_log.decisions_json = {"pending": context["pending_decisions"]}
    else:
        log = DailyLog(
            organization_id=org_id,
            log_date=today,
            summary=ai_summary,
            tasks_json=context["tasks"],
            risks_json={"items": context["risks"]},
            decisions_json={"pending": context["pending_decisions"]},
        )
        db.add(log)

    notification = Notification(
        organization_id=org_id,
        user_id=current_user.id,
        notification_type="morning_brief",
        title=f"经营简报 - {today.strftime('%m月%d日')}",
        content=ai_summary[:200] + "..." if len(ai_summary) > 200 else ai_summary,
        priority="normal",
    )
    db.add(notification)
    await db.commit()

    return {
        "summary": ai_summary,
        "context": context,
        "generated_at": today.isoformat(),
    }
