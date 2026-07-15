from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = None
    conversation_type: str = "general"
    agent_id: UUID | None = None


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None
    conversation_type: str
    summary: str | None
    status: str
    started_at: datetime
    last_message_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content_text: str = Field(..., min_length=1)
    message_type: str = "text"
    content_json: dict | None = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: str
    sender_id: UUID | None
    content_text: str | None
    content_json: dict | None
    message_type: str
    model_provider: str | None
    model_name: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
