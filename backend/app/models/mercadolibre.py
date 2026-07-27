"""Mercado Libre multi-country account and listing models."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin


ML_SITES = {
    "MLM": {"name": "México", "domain": "mercadolibre.com.mx", "currency": "MXN"},
    "MLB": {"name": "Brasil", "domain": "mercadolivre.com.br", "currency": "BRL"},
    "MLC": {"name": "Chile", "domain": "mercadolibre.cl", "currency": "CLP"},
    "MLA": {"name": "Argentina", "domain": "mercadolibre.com.ar", "currency": "ARS"},
    "MCO": {"name": "Colombia", "domain": "mercadolibre.com.co", "currency": "COP"},
    "MLU": {"name": "Uruguay", "domain": "mercadolibre.com.uy", "currency": "UYU"},
    "MPE": {"name": "Perú", "domain": "mercadolibre.com.pe", "currency": "PEN"},
    "MEC": {"name": "Ecuador", "domain": "mercadolibre.com.ec", "currency": "USD"},
    "MCR": {"name": "Costa Rica", "domain": "mercadolibre.co.cr", "currency": "CRC"},
    "MPA": {"name": "Panamá", "domain": "mercadolibre.com.pa", "currency": "USD"},
    "MLV": {"name": "Venezuela", "domain": "mercadolibre.com.ve", "currency": "VES"},
    "MRD": {"name": "República Dominicana", "domain": "mercadolibre.com.do", "currency": "DOP"},
    "MBO": {"name": "Bolivia", "domain": "mercadolibre.com.bo", "currency": "BOB"},
    "MPY": {"name": "Paraguay", "domain": "mercadolibre.com.py", "currency": "PYG"},
    "MGT": {"name": "Guatemala", "domain": "mercadolibre.com.gt", "currency": "GTQ"},
    "MHN": {"name": "Honduras", "domain": "mercadolibre.com.hn", "currency": "HNL"},
    "MNI": {"name": "Nicaragua", "domain": "mercadolibre.com.ni", "currency": "NIO"},
    "MSV": {"name": "El Salvador", "domain": "mercadolibre.com.sv", "currency": "USD"},
}


class MLAccount(Base, TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin):
    """A Mercado Libre seller account for one country/site."""
    __tablename__ = "ml_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[str] = mapped_column(String(10), nullable=False)  # MLM, MLB, etc.
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    seller_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # ML user ID
    nickname: Mapped[str | None] = mapped_column(String(200), nullable=True)  # ML seller nickname
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    app_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # ML App ID
    app_secret: Mapped[str | None] = mapped_column(Text, nullable=True)  # ML App Secret
    redirect_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_listings: Mapped[int] = mapped_column(Integer, default=0)
    active_listings: Mapped[int] = mapped_column(Integer, default=0)

    listings = relationship("MLListing", back_populates="account", lazy="dynamic")


class MLListing(Base, TimestampMixin, OrgScopedMixin, MetadataMixin):
    """A product listing on Mercado Libre."""
    __tablename__ = "ml_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ml_accounts.id"), nullable=False)
    ml_item_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. MLM123456789
    pim_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)  # link to PIM product
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)
    listing_type: Mapped[str] = mapped_column(String(50), default="gold_special")  # gold_special, gold_pro, etc.
    condition: Mapped[str] = mapped_column(String(20), default="new")
    permalink: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ml_status: Mapped[str] = mapped_column(String(50), default="draft")  # draft, active, paused, closed
    sync_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, synced, error
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account = relationship("MLAccount", back_populates="listings")
