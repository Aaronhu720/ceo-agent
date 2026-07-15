import uuid
from datetime import datetime, date

from sqlalchemy import String, Text, ForeignKey, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, MetadataMixin


class Decision(Base, TimestampMixin, OrgScopedMixin, MetadataMixin):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    problem_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    known_facts: Mapped[str | None] = mapped_column(Text, nullable=True)
    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    options_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    selected_option: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_status: Mapped[str] = mapped_column(String(50), default="proposed")
    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reversibility: Mapped[str] = mapped_column(String(20), default="reversible")
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    source_conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
