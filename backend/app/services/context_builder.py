from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Message
from app.models.memory import Memory
from app.models.task import Task
from app.models.project import Project
from app.models.decision import Decision
from app.services.model_gateway import ChatMessage


class ContextBuilder:
    def __init__(self, db: AsyncSession, org_id: UUID, user_id: UUID):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id

    async def build_context(
        self,
        conversation_id: UUID,
        user_message: str,
        max_tokens: int = 8000,
        image_urls: list[str] | None = None,
    ) -> list[ChatMessage]:
        messages = [ChatMessage(role="system", content=await self._build_system_prompt())]

        recent_messages = await self._get_recent_messages(conversation_id, limit=20)
        for msg in recent_messages:
            role = "user" if msg.sender_type == "user" else "assistant"
            if msg.content_text:
                messages.append(ChatMessage(role=role, content=msg.content_text))

        context_parts = []

        memories = await self._get_relevant_memories(user_message)
        if memories:
            mem_text = "\n".join([f"- [{m.memory_type}] {m.title}: {m.content}" for m in memories])
            context_parts.append(f"## Relevant Memories\n{mem_text}")

        active_tasks = await self._get_active_tasks()
        if active_tasks:
            task_text = "\n".join([f"- [{t.priority}] {t.title} (due: {t.due_date})" for t in active_tasks[:10]])
            context_parts.append(f"## Active Tasks\n{task_text}")

        active_projects = await self._get_active_projects()
        if active_projects:
            proj_text = "\n".join([f"- {p.name}: {p.progress_percent}% ({p.status})" for p in active_projects[:5]])
            context_parts.append(f"## Active Projects\n{proj_text}")

        pending_decisions = await self._get_pending_decisions()
        if pending_decisions:
            dec_text = "\n".join([f"- {d.title} ({d.decision_status})" for d in pending_decisions[:5]])
            context_parts.append(f"## Pending Decisions\n{dec_text}")

        if context_parts:
            context_block = "\n\n".join(context_parts)
            messages.insert(1, ChatMessage(
                role="system",
                content=f"Current business context:\n\n{context_block}"
            ))

        messages.append(ChatMessage(role="user", content=user_message, image_urls=image_urls))
        return messages

    async def _build_system_prompt(self) -> str:
        now = datetime.now(timezone.utc)
        return f"""You are CEO Agent, an AI business partner for enterprise founders.

Your role:
- Help the founder think through business decisions
- Track and manage projects, tasks, and decisions
- Remember important business facts and relationships
- Proactively identify risks and opportunities
- Provide daily briefings and reviews

Current time: {now.isoformat()}

Guidelines:
- Be direct and actionable. No fluff.
- When you identify a task, clearly state it so the system can extract it.
- When you identify an important fact worth remembering, highlight it.
- When a decision needs to be made, structure the analysis with options, pros/cons, and a recommendation.
- Flag risks proactively.
- Speak in the user's preferred language.
- Reference relevant memories and context when applicable.
- If you're unsure about something, say so clearly.

Format:
- Use clear structure for complex topics
- Highlight action items with [TASK]
- Highlight decisions with [DECISION]
- Highlight risks with [RISK]
- Highlight memories with [MEMORY]"""

    async def _get_recent_messages(self, conversation_id: UUID, limit: int = 20) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def _get_relevant_memories(self, query: str, limit: int = 10) -> list[Memory]:
        result = await self.db.execute(
            select(Memory)
            .where(
                Memory.organization_id == self.org_id,
                Memory.status.in_(["confirmed", "proposed"]),
            )
            .order_by(desc(Memory.importance_score))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_active_tasks(self, limit: int = 10) -> list[Task]:
        result = await self.db.execute(
            select(Task)
            .where(
                Task.organization_id == self.org_id,
                Task.status.in_(["pending", "in_progress", "at_risk"]),
            )
            .order_by(Task.due_date.asc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_active_projects(self, limit: int = 5) -> list[Project]:
        result = await self.db.execute(
            select(Project)
            .where(
                Project.organization_id == self.org_id,
                Project.status == "active",
            )
            .order_by(desc(Project.updated_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_pending_decisions(self, limit: int = 5) -> list[Decision]:
        result = await self.db.execute(
            select(Decision)
            .where(
                Decision.organization_id == self.org_id,
                Decision.decision_status.in_(["proposed", "pending_approval"]),
            )
            .order_by(desc(Decision.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
