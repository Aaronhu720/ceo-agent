import uuid

from sqlalchemy import String, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, MetadataMixin


class File(Base, TimestampMixin, OrgScopedMixin, MetadataMixin):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    preview_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
