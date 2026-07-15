from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    memory_type: str
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    summary: str | None = None
    importance_score: float = 0.5
    confidence_score: float = 0.5
    sensitivity_level: str = "normal"
    valid_until: datetime | None = None


class MemoryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    summary: str | None = None
    importance_score: float | None = None
    confidence_score: float | None = None
    sensitivity_level: str | None = None
    valid_until: datetime | None = None
    status: str | None = None


class MemoryResponse(BaseModel):
    id: UUID
    memory_type: str
    title: str
    content: str
    summary: str | None
    importance_score: float
    confidence_score: float
    sensitivity_level: str
    status: str
    confirmed_by_user: bool
    valid_until: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemorySearchRequest(BaseModel):
    query: str
    memory_types: list[str] | None = None
    limit: int = 10
