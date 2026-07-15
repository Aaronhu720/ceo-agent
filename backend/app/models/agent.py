import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin


class Agent(Base, TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_provider: Mapped[str] = mapped_column(String(50), default="openai")
    model_name: Mapped[str] = mapped_column(String(100), default="gpt-4o")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    tools_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    permissions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    memory_scope: Mapped[str] = mapped_column(String(50), default="organization")
    version: Mapped[int] = mapped_column(Integer, default=1)


class AgentRun(Base, TimestampMixin, OrgScopedMixin, MetadataMixin):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    input_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_usage_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)

    steps = relationship("AgentStep", back_populates="agent_run", order_by="AgentStep.step_number")


class AgentStep(Base, TimestampMixin):
    __tablename__ = "agent_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    agent_run = relationship("AgentRun", back_populates="steps")
