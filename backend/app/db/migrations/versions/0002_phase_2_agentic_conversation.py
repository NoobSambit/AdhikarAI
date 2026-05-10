"""phase 2 agentic conversation schema

Revision ID: 0002_phase_2
Revises: 0001_phase_1
Create Date: 2026-05-10
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase_2"
down_revision: str | None = "0001_phase_1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "households",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("state_code", sa.Text()),
        sa.Column("district", sa.Text()),
        sa.Column("village", sa.Text()),
        sa.Column("pincode", sa.Text()),
        sa.Column("ration_card_type", sa.Text()),
        sa.Column("annual_household_income", sa.Integer()),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$'", name="ck_household_state_code"),
    )
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="SET NULL")),
        sa.Column("display_name", sa.Text()),
        sa.Column("relationship_to_primary", sa.Text(), nullable=False, server_default="self"),
        sa.Column("age", sa.Integer()),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("gender", sa.Text()),
        sa.Column("caste_category", sa.Text()),
        sa.Column("annual_income", sa.Integer()),
        sa.Column("land_holding_acres", sa.Numeric(8, 2)),
        sa.Column("occupation_type", sa.Text()),
        sa.Column("marital_status", sa.Text()),
        sa.Column("state_code", sa.Text()),
        sa.Column("district", sa.Text()),
        sa.Column("existing_scheme_ids", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("custom_attributes", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("profile_completeness", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_match_snapshot", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("age IS NULL OR (age >= 0 AND age <= 120)", name="ck_profile_age"),
        sa.CheckConstraint("gender IS NULL OR gender IN ('female', 'male', 'other', 'unknown')", name="ck_profile_gender"),
        sa.CheckConstraint(
            "caste_category IS NULL OR caste_category IN ('SC', 'ST', 'OBC', 'GENERAL', 'UNKNOWN')",
            name="ck_profile_caste_category",
        ),
        sa.CheckConstraint("annual_income IS NULL OR annual_income >= 0", name="ck_profile_annual_income"),
        sa.CheckConstraint("land_holding_acres IS NULL OR land_holding_acres >= 0", name="ck_profile_land_holding"),
        sa.CheckConstraint(
            "marital_status IS NULL OR marital_status IN ('single', 'married', 'widowed', 'divorced', 'separated', 'unknown')",
            name="ck_profile_marital_status",
        ),
        sa.CheckConstraint("state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$'", name="ck_profile_state_code"),
        sa.CheckConstraint("profile_completeness >= 0 AND profile_completeness <= 100", name="ck_profile_completeness"),
    )
    op.create_index("idx_profiles_org_household", "profiles", ["organisation_id", "household_id"])
    op.create_table(
        "conversation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("households.id", ondelete="SET NULL")),
        sa.Column("primary_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("active_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("language_code", sa.Text(), nullable=False, server_default="en"),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=False, server_default="0"),
        sa.Column("profile_completeness", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("asked_fields", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("remaining_required_fields", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("redis_key", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organisation_id", "session_id"),
    )
    op.create_table(
        "conversation_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column(
            "conversation_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language_code", sa.Text(), nullable=False, server_default="en"),
        sa.Column("message_type", sa.Text(), nullable=False, server_default="text"),
        sa.Column("structured_payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name="ck_conversation_message_role"),
    )
    op.create_index(
        "idx_conversation_messages_session",
        "conversation_messages",
        ["organisation_id", "conversation_session_id", "created_at"],
    )
    op.create_table(
        "profile_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("changed_fields", postgresql.JSONB(), nullable=False),
        sa.Column("previous_values", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("new_values", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("confidence_score", sa.Numeric(4, 3)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source IN ('conversation', 'api_patch', 'system')", name="ck_profile_event_source"),
    )
    op.create_table(
        "document_check_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("scheme_id", sa.Text(), sa.ForeignKey("schemes.id"), nullable=False),
        sa.Column("documents_available", postgresql.JSONB(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "zero_match_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column(
            "conversation_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        ),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("original_query_text", sa.Text()),
        sa.Column("language_code", sa.Text(), nullable=False, server_default="en"),
        sa.Column("profile_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    for index in ["idx_conversation_messages_session", "idx_profiles_org_household"]:
        op.drop_index(index)
    for table in [
        "zero_match_events",
        "document_check_events",
        "profile_events",
        "conversation_messages",
        "conversation_sessions",
        "profiles",
        "households",
    ]:
        op.drop_table(table)
