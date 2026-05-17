"""phase 5 dashboard and admin schema

Revision ID: 0005_phase_5
Revises: 0004_phase_4
Create Date: 2026-05-17
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_phase_5"
down_revision: str | None = "0004_phase_4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid_pk() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def upgrade() -> None:
    op.create_table(
        "organisation_members",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("admin_users.id", ondelete="CASCADE")),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("phone_e164", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("sms_opt_in", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        *_timestamps(),
        sa.CheckConstraint("role IN ('super_admin', 'ngo_admin', 'operator')", name="ck_org_members_role"),
        sa.CheckConstraint("user_id IS NOT NULL OR admin_user_id IS NOT NULL", name="ck_org_members_actor"),
    )
    op.create_table(
        "beneficiaries",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id", ondelete="SET NULL")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone_e164", sa.Text()),
        sa.Column("state_code", sa.Text(), nullable=False),
        sa.Column("language_code", sa.Text(), nullable=False, server_default="hi"),
        sa.Column("village", sa.Text()),
        sa.Column("district", sa.Text()),
        sa.Column("source", sa.Text(), nullable=False, server_default="operator"),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.CheckConstraint("source IN ('operator', 'self_signup', 'csv_import')", name="ck_beneficiaries_source"),
        sa.CheckConstraint("state_code ~ '^IN-[A-Z]{2}$'", name="ck_beneficiaries_state_code"),
    )
    op.create_index("idx_beneficiaries_org_operator", "beneficiaries", ["organisation_id", "assigned_operator_id"])
    op.create_index(
        "idx_beneficiaries_search",
        "beneficiaries",
        [sa.text("to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(phone_e164,'') || ' ' || coalesce(village,''))")],
        postgresql_using="gin",
    )
    op.create_table(
        "beneficiary_notes",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("beneficiary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id"), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "beneficiary_followups",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("beneficiary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id", ondelete="SET NULL")),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.CheckConstraint("status IN ('open', 'completed', 'cancelled')", name="ck_followups_status"),
    )
    op.create_index("idx_followups_due", "beneficiary_followups", ["organisation_id", "due_date", "status"])
    op.create_table(
        "beneficiary_scheme_assignments",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("beneficiary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheme_id", sa.Text(), sa.ForeignKey("schemes.id"), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id")),
        sa.Column("assignment_source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("assignment_source IN ('eligibility_match', 'manual', 'bulk_csv')", name="ck_assignment_source"),
        sa.UniqueConstraint("organisation_id", "beneficiary_id", "scheme_id", name="uq_beneficiary_scheme_assignment"),
    )
    op.create_table(
        "bulk_eligibility_jobs",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id"), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_storage_url", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "bulk_eligibility_rows",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bulk_eligibility_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("input_payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("matched_schemes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("near_miss_schemes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("profile_completeness", sa.Integer()),
        sa.Column("error_code", sa.Text()),
        sa.Column("error_message", sa.Text()),
        *_timestamps(),
        sa.CheckConstraint("status IN ('pending', 'processed', 'failed')", name="ck_bulk_rows_status"),
        sa.UniqueConstraint("organisation_id", "job_id", "row_number", name="uq_bulk_row_number"),
    )
    op.create_table(
        "operator_notifications",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("recipient_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id", ondelete="CASCADE")),
        sa.Column("state_code", sa.Text()),
        sa.Column("notification_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("sms_sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "unmatched_queries",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("conversation_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversation_sessions.id", ondelete="SET NULL")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("original_query_text", sa.Text(), nullable=False),
        sa.Column("normalized_query_text", sa.Text(), nullable=False),
        sa.Column("language_code", sa.Text(), nullable=False),
        sa.Column("profile_completeness", sa.Integer()),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_unmatched_queries_group", "unmatched_queries", ["organisation_id", "normalized_query_text"])
    op.create_table(
        "scheme_drafts",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("scheme_id", sa.Text(), sa.ForeignKey("schemes.id", ondelete="SET NULL")),
        sa.Column("draft_payload", postgresql.JSONB(), nullable=False),
        sa.Column("validation_result", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id"), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id")),
        *_timestamps(),
    )
    op.create_table(
        "scheme_audit_logs",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("scheme_id", sa.Text()),
        sa.Column("draft_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scheme_drafts.id", ondelete="SET NULL")),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id"), nullable=False),
        sa.Column("before_snapshot", postgresql.JSONB()),
        sa.Column("after_snapshot", postgresql.JSONB()),
        sa.Column("diff", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "quality_flags",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("conversation_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversation_sessions.id", ondelete="SET NULL")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("flag_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False, server_default="warning"),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("review_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "rate_limit_events",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("limit_key", sa.Text(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("limit_value", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("actor_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisation_members.id")),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=False),
        sa.Column("before_snapshot", postgresql.JSONB()),
        sa.Column("after_snapshot", postgresql.JSONB()),
        sa.Column("ip_address", sa.Text()),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in [
        "audit_logs",
        "rate_limit_events",
        "quality_flags",
        "scheme_audit_logs",
        "scheme_drafts",
        "unmatched_queries",
        "operator_notifications",
        "bulk_eligibility_rows",
        "bulk_eligibility_jobs",
        "beneficiary_scheme_assignments",
        "beneficiary_followups",
        "beneficiary_notes",
    ]:
        op.drop_table(table)
    op.drop_index("idx_beneficiaries_search", table_name="beneficiaries")
    op.drop_index("idx_beneficiaries_org_operator", table_name="beneficiaries")
    op.drop_table("beneficiaries")
    op.drop_table("organisation_members")
