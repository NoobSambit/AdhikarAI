from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    __table_args__ = (UniqueConstraint("organisation_id", "session_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    household_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("households.id", ondelete="SET NULL"))
    primary_profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    active_profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="en", server_default="en")
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0, server_default="0")
    profile_completeness: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    asked_fields: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    remaining_required_fields: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    redis_key: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name="ck_conversation_message_role"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    conversation_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="en", server_default="en")
    message_type: Mapped[str] = mapped_column(Text, nullable=False, default="text", server_default="text")
    structured_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
