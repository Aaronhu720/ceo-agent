"""Tool execution handlers — each function implements the logic for a registered tool."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.project import Project
from app.models.decision import Decision
from app.models.memory import Memory
from app.models.entity import Entity
from app.models.notification import Notification
from app.services.audit_service import log_action


async def handle_create_task(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    task = Task(
        organization_id=org_id,
        title=params["title"],
        description=params.get("description"),
        priority=params.get("priority", "medium"),
        due_date=params.get("due_date"),
        project_id=UUID(params["project_id"]) if params.get("project_id") else None,
        created_by=user_id,
        ai_generated=True,
        status="proposed",
    )
    db.add(task)
    await db.flush()

    await log_action(db, organization_id=org_id, action="task.created_by_agent",
                     resource_type="task", resource_id=task.id, user_id=user_id)

    return {"task_id": str(task.id), "title": task.title, "status": "proposed"}


async def handle_update_task(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    task_id = UUID(params["task_id"])
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.organization_id == org_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        return {"error": "Task not found"}

    if params.get("status"):
        task.status = params["status"]
        if params["status"] == "completed":
            task.completed_at = datetime.now(timezone.utc)
    if params.get("priority"):
        task.priority = params["priority"]
    if params.get("title"):
        task.title = params["title"]

    task.updated_by = user_id
    await db.flush()
    return {"task_id": str(task.id), "updated": True}


async def handle_create_project(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    project = Project(
        organization_id=org_id,
        name=params["name"],
        description=params.get("description"),
        objective=params.get("objective"),
        priority=params.get("priority", "medium"),
        target_date=params.get("target_date"),
        owner_id=user_id,
        created_by=user_id,
    )
    db.add(project)
    await db.flush()

    await log_action(db, organization_id=org_id, action="project.created_by_agent",
                     resource_type="project", resource_id=project.id, user_id=user_id)

    return {"project_id": str(project.id), "name": project.name}


async def handle_update_project(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    project_id = UUID(params["project_id"])
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.organization_id == org_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        return {"error": "Project not found"}

    for field in ["status", "progress_percent", "current_summary", "next_action", "risk_level"]:
        if params.get(field) is not None:
            setattr(project, field, params[field])

    project.updated_by = user_id
    await db.flush()
    return {"project_id": str(project.id), "updated": True}


async def handle_create_decision(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    options_json = None
    if params.get("options"):
        options_json = {"options": params["options"]}

    decision = Decision(
        organization_id=org_id,
        title=params["title"],
        problem_statement=params.get("problem_statement"),
        context=params.get("context"),
        known_facts=params.get("known_facts"),
        assumptions=params.get("assumptions"),
        options_json=options_json,
        rationale=params.get("recommendation"),
        risk_level=params.get("risk_level", "medium"),
        reversibility=params.get("reversibility", "reversible"),
        decision_status="proposed",
    )
    db.add(decision)
    await db.flush()

    await log_action(db, organization_id=org_id, action="decision.created_by_agent",
                     resource_type="decision", resource_id=decision.id, user_id=user_id)

    return {"decision_id": str(decision.id), "title": decision.title}


async def handle_propose_memory(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    requires_confirmation = params.get("requires_confirmation", True)
    sensitivity = params.get("sensitivity_level", "normal")

    if sensitivity in ("confidential", "highly_confidential"):
        requires_confirmation = True

    memory = Memory(
        organization_id=org_id,
        user_id=user_id,
        memory_type=params["memory_type"],
        title=params["title"],
        content=params["content"],
        importance_score=params.get("importance_score", 0.5),
        sensitivity_level=sensitivity,
        status="proposed" if requires_confirmation else "confirmed",
        confirmed_by_user=not requires_confirmation,
    )
    db.add(memory)
    await db.flush()
    return {
        "memory_id": str(memory.id),
        "title": memory.title,
        "status": memory.status,
        "requires_confirmation": requires_confirmation,
    }


async def handle_search_memory(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    query = select(Memory).where(
        Memory.organization_id == org_id,
        Memory.status.in_(["confirmed", "proposed"]),
        Memory.content.icontains(params["query"]),
    )
    if params.get("memory_types"):
        query = query.where(Memory.memory_type.in_(params["memory_types"]))

    limit = min(params.get("limit", 10), 20)
    result = await db.execute(query.order_by(Memory.importance_score.desc()).limit(limit))
    memories = result.scalars().all()

    return {
        "count": len(memories),
        "memories": [
            {"id": str(m.id), "type": m.memory_type, "title": m.title, "content": m.content[:200]}
            for m in memories
        ],
    }


async def handle_search_entities(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    query = select(Entity).where(
        Entity.organization_id == org_id,
        Entity.name.icontains(params["query"]),
    )
    if params.get("entity_type"):
        query = query.where(Entity.entity_type == params["entity_type"])

    limit = min(params.get("limit", 10), 20)
    result = await db.execute(query.limit(limit))
    entities = result.scalars().all()

    return {
        "count": len(entities),
        "entities": [
            {"id": str(e.id), "type": e.entity_type, "name": e.name, "code": e.code}
            for e in entities
        ],
    }


async def handle_create_notification(db: AsyncSession, org_id: UUID, user_id: UUID, params: dict) -> dict:
    notification = Notification(
        organization_id=org_id,
        user_id=user_id,
        notification_type="agent_message",
        title=params["title"],
        content=params.get("content"),
        priority=params.get("priority", "normal"),
        action_required=params.get("action_required", False),
    )
    db.add(notification)
    await db.flush()
    return {"notification_id": str(notification.id)}


TOOL_HANDLERS = {
    "create_task": handle_create_task,
    "update_task": handle_update_task,
    "create_project": handle_create_project,
    "update_project": handle_update_project,
    "create_decision": handle_create_decision,
    "propose_memory": handle_propose_memory,
    "search_memory": handle_search_memory,
    "search_entities": handle_search_entities,
    "create_notification": handle_create_notification,
}


async def execute_tool(
    tool_name: str,
    db: AsyncSession,
    org_id: UUID,
    user_id: UUID,
    params: dict,
) -> dict:
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(db, org_id, user_id, params)
