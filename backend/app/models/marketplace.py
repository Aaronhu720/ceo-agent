"""Generic marketplace account and listing models for all platforms."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin


PLATFORMS = {
    "walmart": {
        "name": "Walmart",
        "icon": "walmart",
        "sites": {
            "walmart_us": {"name": "Walmart US", "domain": "walmart.com", "currency": "USD", "country": "美国"},
            "walmart_mx": {"name": "Walmart Mexico", "domain": "walmart.com.mx", "currency": "MXN", "country": "墨西哥"},
            "walmart_ca": {"name": "Walmart Canada", "domain": "walmart.ca", "currency": "CAD", "country": "加拿大"},
        },
    },
    "ebay": {
        "name": "eBay",
        "icon": "ebay",
        "sites": {
            "ebay_us": {"name": "eBay US", "domain": "ebay.com", "currency": "USD", "country": "美国"},
            "ebay_uk": {"name": "eBay UK", "domain": "ebay.co.uk", "currency": "GBP", "country": "英国"},
            "ebay_de": {"name": "eBay Germany", "domain": "ebay.de", "currency": "EUR", "country": "德国"},
            "ebay_fr": {"name": "eBay France", "domain": "ebay.fr", "currency": "EUR", "country": "法国"},
            "ebay_it": {"name": "eBay Italy", "domain": "ebay.it", "currency": "EUR", "country": "意大利"},
            "ebay_es": {"name": "eBay Spain", "domain": "ebay.es", "currency": "EUR", "country": "西班牙"},
            "ebay_au": {"name": "eBay Australia", "domain": "ebay.com.au", "currency": "AUD", "country": "澳大利亚"},
            "ebay_ca": {"name": "eBay Canada", "domain": "ebay.ca", "currency": "CAD", "country": "加拿大"},
        },
    },
    "amazon": {
        "name": "Amazon",
        "icon": "amazon",
        "sites": {
            "amazon_us": {"name": "Amazon US", "domain": "amazon.com", "currency": "USD", "country": "美国"},
            "amazon_ca": {"name": "Amazon Canada", "domain": "amazon.ca", "currency": "CAD", "country": "加拿大"},
            "amazon_mx": {"name": "Amazon Mexico", "domain": "amazon.com.mx", "currency": "MXN", "country": "墨西哥"},
            "amazon_uk": {"name": "Amazon UK", "domain": "amazon.co.uk", "currency": "GBP", "country": "英国"},
            "amazon_de": {"name": "Amazon Germany", "domain": "amazon.de", "currency": "EUR", "country": "德国"},
            "amazon_fr": {"name": "Amazon France", "domain": "amazon.fr", "currency": "EUR", "country": "法国"},
            "amazon_it": {"name": "Amazon Italy", "domain": "amazon.it", "currency": "EUR", "country": "意大利"},
            "amazon_es": {"name": "Amazon Spain", "domain": "amazon.es", "currency": "EUR", "country": "西班牙"},
            "amazon_jp": {"name": "Amazon Japan", "domain": "amazon.co.jp", "currency": "JPY", "country": "日本"},
            "amazon_au": {"name": "Amazon Australia", "domain": "amazon.com.au", "currency": "AUD", "country": "澳大利亚"},
            "amazon_br": {"name": "Amazon Brazil", "domain": "amazon.com.br", "currency": "BRL", "country": "巴西"},
        },
    },
    "wayfair": {
        "name": "Wayfair",
        "icon": "wayfair",
        "sites": {
            "wayfair_us": {"name": "Wayfair US", "domain": "wayfair.com", "currency": "USD", "country": "美国"},
            "wayfair_ca": {"name": "Wayfair Canada", "domain": "wayfair.ca", "currency": "CAD", "country": "加拿大"},
            "wayfair_uk": {"name": "Wayfair UK", "domain": "wayfair.co.uk", "currency": "GBP", "country": "英国"},
            "wayfair_de": {"name": "Wayfair Germany", "domain": "wayfair.de", "currency": "EUR", "country": "德国"},
        },
    },
    "temu": {
        "name": "Temu",
        "icon": "temu",
        "sites": {
            "temu_us": {"name": "Temu US", "domain": "temu.com", "currency": "USD", "country": "美国"},
            "temu_eu": {"name": "Temu EU", "domain": "temu.com", "currency": "EUR", "country": "欧洲"},
        },
    },
    "shein": {
        "name": "SHEIN",
        "icon": "shein",
        "sites": {
            "shein_global": {"name": "SHEIN Global", "domain": "shein.com", "currency": "USD", "country": "全球"},
        },
    },
    "cdiscount": {
        "name": "Cdiscount",
        "icon": "cdiscount",
        "sites": {
            "cdiscount_fr": {"name": "Cdiscount France", "domain": "cdiscount.com", "currency": "EUR", "country": "法国"},
        },
    },
    "otto": {
        "name": "OTTO",
        "icon": "otto",
        "sites": {
            "otto_de": {"name": "OTTO Germany", "domain": "otto.de", "currency": "EUR", "country": "德国"},
        },
    },
}


class MarketplaceAccount(Base, TimestampMixin, OrgScopedMixin, StatusMixin, MetadataMixin):
    __tablename__ = "marketplace_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(50), nullable=False)
    site_name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    seller_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shop_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    app_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    app_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    total_listings: Mapped[int] = mapped_column(Integer, default=0)
    active_listings: Mapped[int] = mapped_column(Integer, default=0)

    listings = relationship("MarketplaceListing", back_populates="account", lazy="dynamic")


class MarketplaceListing(Base, TimestampMixin, OrgScopedMixin, MetadataMixin):
    __tablename__ = "marketplace_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("marketplace_accounts.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pim_sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    platform_status: Mapped[str] = mapped_column(String(50), default="draft")
    sync_status: Mapped[str] = mapped_column(String(50), default="pending")
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    permalink: Mapped[str | None] = mapped_column(String(500), nullable=True)

    account = relationship("MarketplaceAccount", back_populates="listings")
