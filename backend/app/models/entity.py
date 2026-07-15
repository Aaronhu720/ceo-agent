import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin


class Entity(Base, TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class EntityRelation(Base, TimestampMixin, OrgScopedMixin, MetadataMixin):
    __tablename__ = "entity_relations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    attributes_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
