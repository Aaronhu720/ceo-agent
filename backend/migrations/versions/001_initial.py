"""Initial migration — all 23 tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # --- organizations ---
    op.create_table(
        "organizations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("settings", JSONB, server_default="{}"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- roles ---
    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("permissions_json", JSONB, server_default="{}"),
        sa.Column("is_system", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("phone", sa.String(30)),
        sa.Column("timezone", sa.String(50), server_default="Asia/Singapore"),
        sa.Column("language", sa.String(10), server_default="zh"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- conversations ---
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("conversation_type", sa.String(50), server_default="general"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("pinned", sa.Boolean, server_default="false"),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- messages ---
    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_type", sa.String(20), nullable=False),
        sa.Column("sender_id", UUID(as_uuid=True)),
        sa.Column("content_text", sa.Text),
        sa.Column("content_json", JSONB),
        sa.Column("message_type", sa.String(30), server_default="text"),
        sa.Column("parent_message_id", UUID(as_uuid=True), sa.ForeignKey("messages.id")),
        sa.Column("model_provider", sa.String(50)),
        sa.Column("model_name", sa.String(100)),
        sa.Column("token_count", sa.Integer),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("metadata_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])

    # --- memories ---
    op.create_table(
        "memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("importance_score", sa.Float, server_default="0.5"),
        sa.Column("confidence_score", sa.Float, server_default="0.5"),
        sa.Column("access_count", sa.Integer, server_default="0"),
        sa.Column("confirmed_by_user", sa.Boolean, server_default="false"),
        sa.Column("source_message_id", UUID(as_uuid=True), sa.ForeignKey("messages.id")),
        sa.Column("valid_from", sa.DateTime(timezone=True)),
        sa.Column("valid_until", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), server_default="proposed"),
        sa.Column("metadata_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- memory_relations ---
    op.create_table(
        "memory_relations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("strength", sa.Float, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- entities ---
    op.create_table(
        "entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("properties_json", JSONB, server_default="{}"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- entity_relations ---
    op.create_table(
        "entity_relations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source_entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("properties_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(30), server_default="active"),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("progress", sa.Integer, server_default="0"),
        sa.Column("risk_level", sa.String(20), server_default="low"),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("start_date", sa.Date),
        sa.Column("target_date", sa.Date),
        sa.Column("metadata_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- project_updates ---
    op.create_table(
        "project_updates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("update_type", sa.String(30)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- tasks ---
    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(30), server_default="pending"),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("assignee_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("creator_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("ai_generated", sa.Boolean, server_default="false"),
        sa.Column("requires_approval", sa.Boolean, server_default="false"),
        sa.Column("source_message_id", UUID(as_uuid=True), sa.ForeignKey("messages.id")),
        sa.Column("metadata_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- decisions ---
    op.create_table(
        "decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("problem_statement", sa.Text),
        sa.Column("options_json", JSONB, server_default="[]"),
        sa.Column("selected_option", sa.String(500)),
        sa.Column("rationale", sa.Text),
        sa.Column("reversibility", sa.String(20), server_default="reversible"),
        sa.Column("impact_level", sa.String(20), server_default="medium"),
        sa.Column("status", sa.String(30), server_default="proposed"),
        sa.Column("decided_by_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("source_conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id")),
        sa.Column("metadata_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- agents ---
    op.create_table(
        "agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("model_provider", sa.String(50)),
        sa.Column("model_name", sa.String(100)),
        sa.Column("temperature", sa.Float, server_default="0.7"),
        sa.Column("system_instructions", sa.Text),
        sa.Column("tools_json", JSONB, server_default="{}"),
        sa.Column("permissions_json", JSONB, server_default="{}"),
        sa.Column("memory_scope", sa.String(30), server_default="organization"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- agent_runs ---
    op.create_table(
        "agent_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_type", sa.String(30)),
        sa.Column("trigger_id", UUID(as_uuid=True)),
        sa.Column("input_json", JSONB),
        sa.Column("output_json", JSONB),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("token_usage_json", JSONB),
        sa.Column("cost_usd", sa.Float),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- agent_steps ---
    op.create_table(
        "agent_steps",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_run_id", UUID(as_uuid=True), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("step_type", sa.String(30), nullable=False),
        sa.Column("tool_name", sa.String(100)),
        sa.Column("input_json", JSONB),
        sa.Column("output_json", JSONB),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- heartbeat_rules ---
    op.create_table(
        "heartbeat_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("rule_type", sa.String(50)),
        sa.Column("cron_expression", sa.String(100)),
        sa.Column("conditions_json", JSONB, server_default="{}"),
        sa.Column("action_json", JSONB, server_default="{}"),
        sa.Column("enabled", sa.Boolean, server_default="true"),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- heartbeat_runs ---
    op.create_table(
        "heartbeat_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("rule_id", UUID(as_uuid=True), sa.ForeignKey("heartbeat_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), server_default="running"),
        sa.Column("result_json", JSONB),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # --- daily_logs ---
    op.create_table(
        "daily_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date, nullable=False),
        sa.Column("log_type", sa.String(30), server_default="morning"),
        sa.Column("events_json", JSONB, server_default="[]"),
        sa.Column("decisions_json", JSONB, server_default="[]"),
        sa.Column("tasks_json", JSONB, server_default="{}"),
        sa.Column("risks_json", JSONB, server_default="[]"),
        sa.Column("lessons_json", JSONB, server_default="[]"),
        sa.Column("tomorrow_priorities_json", JSONB, server_default="[]"),
        sa.Column("ai_summary", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text),
        sa.Column("notification_type", sa.String(50)),
        sa.Column("priority", sa.String(20), server_default="normal"),
        sa.Column("action_required", sa.Boolean, server_default="false"),
        sa.Column("action_url", sa.String(500)),
        sa.Column("read", sa.Boolean, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- approvals ---
    op.create_table(
        "approvals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id")),
        sa.Column("requested_for_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("action_description", sa.Text),
        sa.Column("payload_json", JSONB),
        sa.Column("risk_level", sa.String(20), server_default="medium"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("decided_by_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decision_note", sa.Text),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- files ---
    op.create_table(
        "files",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("original_name", sa.String(500), nullable=False),
        sa.Column("storage_provider", sa.String(30)),
        sa.Column("bucket", sa.String(200)),
        sa.Column("key", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100)),
        sa.Column("size_bytes", sa.BigInteger),
        sa.Column("processing_status", sa.String(30), server_default="pending"),
        sa.Column("extracted_text", sa.Text),
        sa.Column("metadata_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", UUID(as_uuid=True)),
        sa.Column("before_json", JSONB),
        sa.Column("after_json", JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_logs_org_created", "audit_logs", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("files")
    op.drop_table("approvals")
    op.drop_table("notifications")
    op.drop_table("daily_logs")
    op.drop_table("heartbeat_runs")
    op.drop_table("heartbeat_rules")
    op.drop_table("agent_steps")
    op.drop_table("agent_runs")
    op.drop_table("agents")
    op.drop_table("decisions")
    op.drop_table("tasks")
    op.drop_table("project_updates")
    op.drop_table("projects")
    op.drop_table("entity_relations")
    op.drop_table("entities")
    op.drop_table("memory_relations")
    op.drop_table("memories")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("organizations")
