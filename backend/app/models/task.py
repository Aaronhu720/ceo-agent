import uuid
from datetime import datetime, date

from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin, AuditMixin


class Task(Base, TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin, AuditMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), default="general")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependency_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
