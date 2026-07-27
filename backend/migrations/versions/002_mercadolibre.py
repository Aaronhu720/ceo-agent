"""Add Mercado Libre tables.

Revision ID: 002_mercadolibre
Revises: 001_initial
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "002_mercadolibre"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ml_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("site_id", sa.String(10), nullable=False),
        sa.Column("country_name", sa.String(100), nullable=False),
        sa.Column("seller_id", sa.String(50), nullable=True),
        sa.Column("nickname", sa.String(200), nullable=True),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("refresh_token", sa.Text, nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("app_id", sa.String(50), nullable=True),
        sa.Column("app_secret", sa.Text, nullable=True),
        sa.Column("redirect_uri", sa.String(500), nullable=True),
        sa.Column("total_listings", sa.Integer, server_default="0"),
        sa.Column("active_listings", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(50), server_default="'pending'"),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "ml_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("ml_accounts.id"), nullable=False),
        sa.Column("ml_item_id", sa.String(50), nullable=True),
        sa.Column("pim_sku", sa.String(100), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("category_id", sa.String(50), nullable=True),
        sa.Column("price", sa.Float, nullable=True),
        sa.Column("currency_id", sa.String(10), nullable=True),
        sa.Column("available_quantity", sa.Integer, server_default="0"),
        sa.Column("listing_type", sa.String(50), server_default="'gold_special'"),
        sa.Column("condition", sa.String(20), server_default="'new'"),
        sa.Column("permalink", sa.String(500), nullable=True),
        sa.Column("thumbnail", sa.String(500), nullable=True),
        sa.Column("ml_status", sa.String(50), server_default="'draft'"),
        sa.Column("sync_status", sa.String(50), server_default="'pending'"),
        sa.Column("sync_error", sa.Text, nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_index("ix_ml_listings_account_id", "ml_listings", ["account_id"])
    op.create_index("ix_ml_listings_pim_sku", "ml_listings", ["pim_sku"])


def downgrade() -> None:
    op.drop_table("ml_listings")
    op.drop_table("ml_accounts")
