import asyncio
from datetime import datetime, timezone, date

from app.workers.celery_app import celery_app


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.heartbeat_tasks.generate_morning_brief")
def generate_morning_brief():
    run_async(_generate_morning_brief())


@celery_app.task(name="app.workers.heartbeat_tasks.generate_evening_review")
def generate_evening_review():
    run_async(_generate_evening_review())


@celery_app.task(name="app.workers.heartbeat_tasks.generate_weekly_review")
def generate_weekly_review():
    run_async(_generate_weekly_review())


async def _generate_morning_brief():
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.organization import Organization
    from app.models.task import Task
    from app.models.notification import Notification
    from app.models.daily_log import DailyLog
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        orgs = await db.execute(select(Organization))
        for org in orgs.scalars().all():
            users = await db.execute(
                select(User).where(User.organization_id == org.id, User.status == "active")
            )
            owner = users.scalars().first()
            if not owner:
                continue

            overdue_tasks = await db.execute(
                select(func.count()).select_from(Task).where(
                    Task.organization_id == org.id,
                    Task.status.in_(["pending", "in_progress"]),
                    Task.due_date < date.today(),
                )
            )
            overdue_count = overdue_tasks.scalar() or 0

            pending_tasks = await db.execute(
                select(func.count()).select_from(Task).where(
                    Task.organization_id == org.id,
                    Task.status.in_(["pending", "in_progress"]),
                )
            )
            pending_count = pending_tasks.scalar() or 0

            today = date.today()
            log = DailyLog(
                organization_id=org.id,
                log_date=today,
                summary=f"Morning Brief: {pending_count} active tasks, {overdue_count} overdue",
                tasks_json={"pending": pending_count, "overdue": overdue_count},
            )
            db.add(log)

            notification = Notification(
                organization_id=org.id,
                user_id=owner.id,
                notification_type="morning_brief",
                title=f"Early Report - {today.isoformat()}",
                content=f"You have {pending_count} active tasks, {overdue_count} overdue.",
                priority="normal" if overdue_count == 0 else "high",
            )
            db.add(notification)
            await db.commit()


async def _generate_evening_review():
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.organization import Organization
    from app.models.conversation import Conversation
    from app.models.task import Task
    from app.models.notification import Notification
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        orgs = await db.execute(select(Organization))
        for org in orgs.scalars().all():
            users = await db.execute(
                select(User).where(User.organization_id == org.id, User.status == "active")
            )
            owner = users.scalars().first()
            if not owner:
                continue

            today = date.today()

            completed_tasks = await db.execute(
                select(func.count()).select_from(Task).where(
                    Task.organization_id == org.id,
                    Task.status == "completed",
                    func.date(Task.completed_at) == today,
                )
            )
            completed_count = completed_tasks.scalar() or 0

            notification = Notification(
                organization_id=org.id,
                user_id=owner.id,
                notification_type="evening_review",
                title=f"Evening Review - {today.isoformat()}",
                content=f"Today you completed {completed_count} tasks.",
                priority="normal",
            )
            db.add(notification)
            await db.commit()


async def _generate_weekly_review():
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.organization import Organization
    from app.models.notification import Notification
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        orgs = await db.execute(select(Organization))
        for org in orgs.scalars().all():
            users = await db.execute(
                select(User).where(User.organization_id == org.id, User.status == "active")
            )
            owner = users.scalars().first()
            if not owner:
                continue

            notification = Notification(
                organization_id=org.id,
                user_id=owner.id,
                notification_type="weekly_review",
                title="Weekly Review",
                content="Your weekly business review is ready.",
                priority="normal",
            )
            db.add(notification)
            await db.commit()
