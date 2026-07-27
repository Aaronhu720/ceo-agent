"""Add generic marketplace tables.

Revision ID: 003_marketplace
Revises: 002_mercadolibre
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "003_marketplace"
down_revision = "002_mercadolibre"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketplace_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("platform", sa.String(50), nullable=False, index=True),
        sa.Column("site_id", sa.String(50), nullable=False),
        sa.Column("site_name", sa.String(200), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("seller_id", sa.String(100), nullable=True),
        sa.Column("shop_name", sa.String(300), nullable=True),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("refresh_token", sa.Text, nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("app_key", sa.String(200), nullable=True),
        sa.Column("app_secret", sa.Text, nullable=True),
        sa.Column("extra_config", JSONB, nullable=True),
        sa.Column("total_listings", sa.Integer, server_default="0"),
        sa.Column("active_listings", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(50), server_default="'pending'"),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "marketplace_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("marketplace_accounts.id"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False, index=True),
        sa.Column("item_id", sa.String(100), nullable=True),
        sa.Column("pim_sku", sa.String(100), nullable=True, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("price", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("quantity", sa.Integer, server_default="0"),
        sa.Column("platform_status", sa.String(50), server_default="'draft'"),
        sa.Column("sync_status", sa.String(50), server_default="'pending'"),
        sa.Column("sync_error", sa.Text, nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("permalink", sa.String(500), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_index("ix_marketplace_accounts_platform_site", "marketplace_accounts", ["platform", "site_id"])
    op.create_index("ix_marketplace_listings_account_id", "marketplace_listings", ["account_id"])


def downgrade() -> None:
    op.drop_table("marketplace_listings")
    op.drop_table("marketplace_accounts")
