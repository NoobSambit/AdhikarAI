from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProfileEvent(Base):
    __tablename__ = "profile_events"
    __table_args__ = (CheckConstraint("source IN ('conversation', 'api_patch', 'system')", name="ck_profile_event_source"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    changed_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    previous_values: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    new_values: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DocumentCheckEvent(Base):
    __tablename__ = "document_check_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id"), nullable=False)
    documents_available: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ZeroMatchEvent(Base):
    __tablename__ = "zero_match_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    conversation_session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="SET NULL")
    )
    profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    original_query_text: Mapped[str | None] = mapped_column(Text)
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="en", server_default="en")
    profile_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
