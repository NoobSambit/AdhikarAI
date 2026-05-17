from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VoiceTurn(Base):
    __tablename__ = "voice_turns"
    __table_args__ = (
        CheckConstraint("provider IN ('local', 'groq', 'browser')", name="ck_voice_turn_provider"),
        CheckConstraint(
            "status IN ('received', 'transcribed', 'low_confidence', 'agent_completed', 'failed')",
            name="ck_voice_turn_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    conversation_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False
    )
    profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    input_audio_mime_type: Mapped[str | None] = mapped_column(Text)
    input_audio_duration_ms: Mapped[int | None] = mapped_column(Integer)
    input_audio_size_bytes: Mapped[int | None] = mapped_column(Integer)
    transcript: Mapped[str | None] = mapped_column(Text)
    normalized_transcript: Mapped[str | None] = mapped_column(Text)
    detected_language_code: Mapped[str | None] = mapped_column(Text)
    selected_language_code: Mapped[str] = mapped_column(Text, nullable=False)
    asr_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    timings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
