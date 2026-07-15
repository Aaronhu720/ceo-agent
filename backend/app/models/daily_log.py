import uuid
from datetime import date

from sqlalchemy import String, Text, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, MetadataMixin


class DailyLog(Base, TimestampMixin, OrgScopedMixin, MetadataMixin):
    __tablename__ = "daily_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    events_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    decisions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tasks_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    risks_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    lessons_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tomorrow_priorities_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
