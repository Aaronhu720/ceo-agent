import asyncio
import json
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


@celery_app.task(name="app.workers.heartbeat_tasks.generate_chat_reminder")
def generate_chat_reminder():
    run_async(_generate_chat_reminder())


@celery_app.task(name="app.workers.heartbeat_tasks.generate_weekly_review")
def generate_weekly_review():
    run_async(_generate_weekly_review())


async def _gather_business_context(db, org_id):
    """Gather all business data for AI briefing generation."""
    from sqlalchemy import select, func
    from app.models.task import Task
    from app.models.project import Project
    from app.models.decision import Decision
    from app.models.memory import Memory

    today = date.today()

    pending_tasks = await db.execute(
        select(Task).where(
            Task.organization_id == org_id,
            Task.status.in_(["pending", "in_progress"]),
        ).limit(20)
    )
    tasks_list = pending_tasks.scalars().all()

    overdue_result = await db.execute(
        select(func.count()).select_from(Task).where(
            Task.organization_id == org_id,
            Task.status.in_(["pending", "in_progress"]),
            Task.due_date < today,
        )
    )
    overdue_count = overdue_result.scalar() or 0

    at_risk_result = await db.execute(
        select(Task).where(
            Task.organization_id == org_id,
            Task.risk_level == "high",
            Task.status != "completed",
        ).limit(10)
    )
    risk_tasks = at_risk_result.scalars().all()

    projects_result = await db.execute(
        select(Project).where(
            Project.organization_id == org_id,
            Project.status == "active",
        ).limit(10)
    )
    projects_list = projects_result.scalars().all()

    decisions_result = await db.execute(
        select(Decision).where(
            Decision.organization_id == org_id,
            Decision.decision_status == "proposed",
        ).limit(10)
    )
    pending_decisions = decisions_result.scalars().all()

    memories_result = await db.execute(
        select(Memory).where(
            Memory.organization_id == org_id,
            Memory.status == "confirmed",
        ).order_by(Memory.importance_score.desc()).limit(15)
    )
    key_memories = memories_result.scalars().all()

    completed_today = await db.execute(
        select(func.count()).select_from(Task).where(
            Task.organization_id == org_id,
            Task.status == "completed",
            func.date(Task.completed_at) == today,
        )
    )
    completed_today_count = completed_today.scalar() or 0

    context = {
        "date": today.isoformat(),
        "tasks": {
            "active": [{"title": t.title, "priority": t.priority, "status": t.status,
                        "due_date": str(t.due_date) if t.due_date else None} for t in tasks_list],
            "overdue_count": overdue_count,
            "completed_today": completed_today_count,
        },
        "risks": [{"title": t.title, "description": t.description, "risk_level": t.risk_level}
                   for t in risk_tasks],
        "projects": [{"name": p.name, "progress": p.progress_percent, "status": p.status,
                       "risk_level": p.risk_level} for p in projects_list],
        "pending_decisions": [{"title": d.title, "risk_level": d.risk_level,
                                "problem": d.problem_statement} for d in pending_decisions],
        "key_memories": [{"title": m.title, "type": m.memory_type, "content": m.content[:100]}
                          for m in key_memories[:5]],
    }
    return context


async def _call_ai_for_briefing(context: dict, briefing_type: str) -> str:
    """Call AI model to generate a briefing."""
    from app.services.model_gateway import get_model_provider, ChatMessage

    prompts = {
        "morning": (
            "你是 CEO Agent，一位资深的企业经营分析师。请根据以下经营数据，生成一份简洁有力的早间经营简报。\n\n"
            "要求：\n"
            "1. 用中文，控制在300字以内\n"
            "2. 开头用一句话总结今日经营状态\n"
            "3. 列出今日需要关注的重点（风险、待决策、逾期任务）\n"
            "4. 给出今日工作建议\n"
            "5. 语气专业但温和，像一个值得信赖的合伙人\n\n"
            f"经营数据：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        ),
        "evening": (
            "你是 CEO Agent，请根据以下数据生成一份简洁的晚间回顾。\n\n"
            "要求：\n"
            "1. 用中文，控制在200字以内\n"
            "2. 总结今日完成的工作\n"
            "3. 指出明日需要优先处理的事项\n"
            "4. 如有风险事项，提醒关注\n\n"
            f"经营数据：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        ),
        "weekly": (
            "你是 CEO Agent，请根据以下数据生成一份周度经营回顾。\n\n"
            "要求：\n"
            "1. 用中文，控制在400字以内\n"
            "2. 本周关键进展\n"
            "3. 本周做出的重要决策\n"
            "4. 下周重点方向建议\n"
            "5. 风险预警\n\n"
            f"经营数据：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        ),
    }

    try:
        provider = get_model_provider("openai")
        messages = [
            ChatMessage(role="user", content=prompts.get(briefing_type, prompts["morning"])),
        ]
        response = await provider.chat(messages, model="gpt-4o", temperature=0.7)
        return response.content
    except Exception as e:
        return f"AI 简报生成失败: {str(e)}"


async def _generate_morning_brief():
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.organization import Organization
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

            context = await _gather_business_context(db, org.id)
            ai_summary = await _call_ai_for_briefing(context, "morning")

            today = date.today()
            log = DailyLog(
                organization_id=org.id,
                log_date=today,
                summary=ai_summary,
                tasks_json=context["tasks"],
                risks_json={"items": context["risks"]},
                decisions_json={"pending": context["pending_decisions"]},
                tomorrow_priorities_json=None,
            )
            db.add(log)

            notification = Notification(
                organization_id=org.id,
                user_id=owner.id,
                notification_type="morning_brief",
                title=f"早间经营简报 - {today.strftime('%m月%d日')}",
                content=ai_summary[:200] + "..." if len(ai_summary) > 200 else ai_summary,
                priority="high" if context["tasks"]["overdue_count"] > 0 or len(context["risks"]) > 0 else "normal",
            )
            db.add(notification)
            await db.commit()


async def _generate_evening_review():
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

            context = await _gather_business_context(db, org.id)
            ai_summary = await _call_ai_for_briefing(context, "evening")

            today = date.today()
            notification = Notification(
                organization_id=org.id,
                user_id=owner.id,
                notification_type="evening_review",
                title=f"晚间经营回顾 - {today.strftime('%m月%d日')}",
                content=ai_summary[:200] + "..." if len(ai_summary) > 200 else ai_summary,
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

            context = await _gather_business_context(db, org.id)
            ai_summary = await _call_ai_for_briefing(context, "weekly")

            notification = Notification(
                organization_id=org.id,
                user_id=owner.id,
                notification_type="weekly_review",
                title=f"本周经营回顾",
                content=ai_summary[:200] + "..." if len(ai_summary) > 200 else ai_summary,
                priority="normal",
            )
            db.add(notification)
            await db.commit()


async def _generate_chat_reminder():
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.organization import Organization
    from app.models.notification import Notification
    from app.models.user import User
    from app.models.task import Task
    from app.models.decision import Decision

    async with AsyncSessionLocal() as db:
        orgs = await db.execute(select(Organization))
        for org in orgs.scalars().all():
            users = await db.execute(
                select(User).where(User.organization_id == org.id, User.status == "active")
            )
            owner = users.scalars().first()
            if not owner:
                continue

            pending_tasks = await db.execute(
                select(func.count()).select_from(Task).where(
                    Task.organization_id == org.id,
                    Task.status.in_(["pending", "in_progress"]),
                )
            )
            task_count = pending_tasks.scalar() or 0

            pending_decisions = await db.execute(
                select(func.count()).select_from(Decision).where(
                    Decision.organization_id == org.id,
                    Decision.decision_status == "proposed",
                )
            )
            decision_count = pending_decisions.scalar() or 0

            today = date.today()
            topics = []
            if task_count > 0:
                topics.append(f"{task_count} 个进行中的任务")
            if decision_count > 0:
                topics.append(f"{decision_count} 个待决策事项")

            topic_text = "、".join(topics) if topics else "今日经营进展"

            notification = Notification(
                organization_id=org.id,
                user_id=owner.id,
                notification_type="chat_reminder",
                title="该和 CEO Agent 聊聊了",
                content=f"建议花 1 小时和 AI 合伙人对话，回顾 {topic_text}，理清明日方向。",
                priority="high",
                action_required=True,
            )
            db.add(notification)
            await db.commit()
