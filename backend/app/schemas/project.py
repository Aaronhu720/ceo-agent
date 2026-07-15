from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    objective: str | None = None
    priority: str = "medium"
    start_date: date | None = None
    target_date: date | None = None
    budget: float | None = None
    currency: str = "USD"


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    objective: str | None = None
    status: str | None = None
    priority: str | None = None
    start_date: date | None = None
    target_date: date | None = None
    progress_percent: int | None = None
    budget: float | None = None
    risk_level: str | None = None
    current_summary: str | None = None
    next_action: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    objective: str | None
    status: str
    priority: str
    start_date: date | None
    target_date: date | None
    progress_percent: int
    budget: float | None
    currency: str
    current_summary: str | None
    next_action: str | None
    risk_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectUpdateCreate(BaseModel):
    update_type: str = "progress"
    content: str
    progress_percent: int | None = None
    risk_level: str | None = None


class ProjectUpdateResponse(BaseModel):
    id: UUID
    project_id: UUID
    update_type: str
    content: str
    progress_percent: int | None
    risk_level: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
