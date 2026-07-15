from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    task_type: str = "general"
    project_id: UUID | None = None
    assigned_to: UUID | None = None
    priority: str = "medium"
    start_date: date | None = None
    due_date: date | None = None
    completion_criteria: str | None = None
    risk_level: str = "low"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: UUID | None = None
    start_date: date | None = None
    due_date: date | None = None
    risk_level: str | None = None


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    task_type: str
    project_id: UUID | None
    assigned_to: UUID | None
    priority: str
    status: str
    start_date: date | None
    due_date: date | None
    completed_at: datetime | None
    risk_level: str
    ai_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}
