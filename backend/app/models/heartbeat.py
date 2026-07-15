import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, MetadataMixin


class HeartbeatRule(Base, TimestampMixin, OrgScopedMixin, MetadataMixin):
    __tablename__ = "heartbeat_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    frequency_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    conditions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HeartbeatRun(Base, TimestampMixin, MetadataMixin):
    __tablename__ = "heartbeat_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    heartbeat_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("heartbeat_rules.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="running")
    findings_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
