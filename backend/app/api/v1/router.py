from fastapi import APIRouter

from app.api.v1.endpoints import auth, conversations, memories, tasks, projects, decisions
from app.api.v1.endpoints import agents, heartbeat, files, notifications, approvals, audit

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(memories.router, prefix="/memories", tags=["Memories"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(decisions.router, prefix="/decisions", tags=["Decisions"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(heartbeat.router, prefix="/heartbeat-rules", tags=["Heartbeat"])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["Audit"])
