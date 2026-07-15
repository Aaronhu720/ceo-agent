import uuid
from datetime import date

from sqlalchemy import String, Text, Float, Integer, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin, AuditMixin


class Project(Base, TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin, AuditMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    current_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")

    updates = relationship("ProjectUpdate", back_populates="project", order_by="ProjectUpdate.created_at.desc()")


class ProjectUpdate(Base, TimestampMixin, MetadataMixin):
    __tablename__ = "project_updates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    update_type: Mapped[str] = mapped_column(String(50), default="progress")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    progress_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    project = relationship("Project", back_populates="updates")
