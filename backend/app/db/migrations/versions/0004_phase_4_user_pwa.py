"""phase 4 user pwa schema

Revision ID: 0004_phase_4
Revises: 0003_phase_3
Create Date: 2026-05-17
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase_4"
down_revision: str | None = "0003_phase_3"
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
        "users",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("phone_e164", sa.Text(), nullable=False),
        sa.Column("phone_verified_at", sa.DateTime(timezone=True)),
        sa.Column("primary_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("language_code", sa.Text(), nullable=False, server_default="hi"),
        sa.Column("high_contrast_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("font_size", sa.Text(), nullable=False, server_default="default"),
        sa.Column("notification_opt_in", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.CheckConstraint("font_size IN ('default', 'large', 'extra_large')", name="ck_users_font_size"),
        sa.UniqueConstraint("organisation_id", "phone_e164", name="uq_users_org_phone"),
    )
    op.create_table(
        "otp_challenges",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("phone_e164", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False, server_default="msg91"),
        sa.Column("provider_request_id", sa.Text()),
        sa.Column("otp_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("status IN ('sent', 'verified', 'expired', 'failed')", name="ck_otp_challenges_status"),
    )
    op.create_table(
        "saved_schemes",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheme_id", sa.Text(), sa.ForeignKey("schemes.id"), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reminder_scheduled_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("organisation_id", "user_id", "profile_id", "scheme_id", name="uq_saved_scheme"),
    )
    op.create_table(
        "document_checklist_items",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheme_id", sa.Text(), sa.ForeignKey("schemes.id"), nullable=False),
        sa.Column("document_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="not_gathered"),
        sa.Column("source", sa.Text(), nullable=False, server_default="manual"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('not_gathered', 'gathered', 'verified', 'rejected')", name="ck_checklist_status"),
        sa.CheckConstraint("source IN ('manual', 'digilocker', 'migration')", name="ck_checklist_source"),
        sa.UniqueConstraint("organisation_id", "profile_id", "scheme_id", "document_name", name="uq_checklist_item"),
    )
    op.create_table(
        "digilocker_connections",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("digilocker_user_id", sa.Text()),
        sa.Column("access_token_encrypted", sa.Text()),
        sa.Column("refresh_token_encrypted", sa.Text()),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Text(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("status IN ('connected', 'revoked', 'failed')", name="ck_digilocker_status"),
    )
    op.create_table(
        "verified_documents",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column("issuer", sa.Text()),
        sa.Column("document_uri", sa.Text()),
        sa.Column("masked_identifier", sa.Text()),
        sa.Column("verification_status", sa.Text(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source IN ('digilocker', 'uidai_sandbox')", name="ck_verified_document_source"),
        sa.CheckConstraint("verification_status IN ('verified', 'failed', 'revoked')", name="ck_verified_document_status"),
    )
    op.create_table(
        "application_statuses",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheme_id", sa.Text(), sa.ForeignKey("schemes.id"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("source", sa.Text(), nullable=False, server_default="user"),
        *_timestamps(),
        sa.CheckConstraint("status IN ('not_started', 'documents_gathering', 'submitted', 'pending', 'approved', 'rejected')", name="ck_application_status"),
        sa.CheckConstraint("source IN ('user', 'operator', 'system')", name="ck_application_status_source"),
        sa.UniqueConstraint("organisation_id", "user_id", "profile_id", "scheme_id", name="uq_application_status"),
    )
    op.create_table(
        "application_status_events",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("application_status_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("application_statuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_status", sa.Text()),
        sa.Column("new_status", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "notification_subscriptions",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        *_timestamps(),
        sa.UniqueConstraint("organisation_id", "endpoint", name="uq_notification_endpoint"),
    )
    op.create_table(
        "notification_jobs",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("notification_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Text(), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('scheduled', 'sent', 'failed', 'cancelled')", name="ck_notification_job_status"),
    )
    op.create_table(
        "action_plans",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversation_sessions.id", ondelete="SET NULL")),
        sa.Column("format", sa.Text(), nullable=False),
        sa.Column("storage_provider", sa.Text(), nullable=False, server_default="inline"),
        sa.Column("storage_url", sa.Text(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("format IN ('pdf', 'image', 'whatsapp_text')", name="ck_action_plan_format"),
    )
    op.create_table(
        "offline_sync_events",
        _uuid_pk(),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error_code", sa.Text()),
        *_timestamps(),
        sa.CheckConstraint("status IN ('received', 'applied', 'duplicate', 'failed')", name="ck_offline_sync_status"),
        sa.UniqueConstraint("organisation_id", "idempotency_key", name="uq_offline_sync_idempotency"),
    )


def downgrade() -> None:
    for table in [
        "offline_sync_events",
        "action_plans",
        "notification_jobs",
        "notification_subscriptions",
        "application_status_events",
        "application_statuses",
        "verified_documents",
        "digilocker_connections",
        "document_checklist_items",
        "saved_schemes",
        "otp_challenges",
        "users",
    ]:
        op.drop_table(table)
