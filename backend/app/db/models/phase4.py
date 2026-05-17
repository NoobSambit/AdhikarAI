from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("font_size IN ('default', 'large', 'extra_large')", name="ck_users_font_size"),
        UniqueConstraint("organisation_id", "phone_e164", name="uq_users_org_phone"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    phone_e164: Mapped[str] = mapped_column(Text, nullable=False)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    primary_profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="hi", server_default="hi")
    high_contrast_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    font_size: Mapped[str] = mapped_column(Text, nullable=False, default="default", server_default="default")
    notification_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"
    __table_args__ = (
        CheckConstraint("status IN ('sent', 'verified', 'expired', 'failed')", name="ck_otp_challenges_status"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    phone_e164: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False, default="msg91", server_default="msg91")
    provider_request_id: Mapped[str | None] = mapped_column(Text)
    otp_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SavedScheme(Base):
    __tablename__ = "saved_schemes"
    __table_args__ = (UniqueConstraint("organisation_id", "user_id", "profile_id", "scheme_id", name="uq_saved_scheme"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id"), nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reminder_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentChecklistItem(Base):
    __tablename__ = "document_checklist_items"
    __table_args__ = (
        CheckConstraint("status IN ('not_gathered', 'gathered', 'verified', 'rejected')", name="ck_checklist_status"),
        CheckConstraint("source IN ('manual', 'digilocker', 'migration')", name="ck_checklist_source"),
        UniqueConstraint("organisation_id", "profile_id", "scheme_id", "document_name", name="uq_checklist_item"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id"), nullable=False)
    document_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="not_gathered", server_default="not_gathered")
    source: Mapped[str] = mapped_column(Text, nullable=False, default="manual", server_default="manual")
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DigiLockerConnection(Base):
    __tablename__ = "digilocker_connections"
    __table_args__ = (CheckConstraint("status IN ('connected', 'revoked', 'failed')", name="ck_digilocker_status"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    digilocker_user_id: Mapped[str | None] = mapped_column(Text)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class VerifiedDocument(Base):
    __tablename__ = "verified_documents"
    __table_args__ = (
        CheckConstraint("source IN ('digilocker', 'uidai_sandbox')", name="ck_verified_document_source"),
        CheckConstraint("verification_status IN ('verified', 'failed', 'revoked')", name="ck_verified_document_status"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    issuer: Mapped[str | None] = mapped_column(Text)
    document_uri: Mapped[str | None] = mapped_column(Text)
    masked_identifier: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ApplicationStatus(Base):
    __tablename__ = "application_statuses"
    __table_args__ = (
        CheckConstraint("status IN ('not_started', 'documents_gathering', 'submitted', 'pending', 'approved', 'rejected')", name="ck_application_status"),
        CheckConstraint("source IN ('user', 'operator', 'system')", name="ck_application_status_source"),
        UniqueConstraint("organisation_id", "user_id", "profile_id", "scheme_id", name="uq_application_status"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="user", server_default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ApplicationStatusEvent(Base):
    __tablename__ = "application_status_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    application_status_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("application_statuses.id", ondelete="CASCADE"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(Text)
    new_status: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NotificationSubscription(Base):
    __tablename__ = "notification_subscriptions"
    __table_args__ = (UniqueConstraint("organisation_id", "endpoint", name="uq_notification_endpoint"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class NotificationJob(Base):
    __tablename__ = "notification_jobs"
    __table_args__ = (CheckConstraint("status IN ('scheduled', 'sent', 'failed', 'cancelled')", name="ck_notification_job_status"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    notification_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, nullable=False, default="scheduled", server_default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ActionPlan(Base):
    __tablename__ = "action_plans"
    __table_args__ = (CheckConstraint("format IN ('pdf', 'image', 'whatsapp_text')", name="ck_action_plan_format"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    conversation_session_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="SET NULL"))
    format: Mapped[str] = mapped_column(Text, nullable=False)
    storage_provider: Mapped[str] = mapped_column(Text, nullable=False, default="inline", server_default="inline")
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class OfflineSyncEvent(Base):
    __tablename__ = "offline_sync_events"
    __table_args__ = (
        CheckConstraint("status IN ('received', 'applied', 'duplicate', 'failed')", name="ck_offline_sync_status"),
        UniqueConstraint("organisation_id", "idempotency_key", name="uq_offline_sync_idempotency"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
