"""phase 3 voice multilingual schema

Revision ID: 0003_phase_3
Revises: 0002_phase_2
Create Date: 2026-05-16
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase_3"
down_revision: str | None = "0002_phase_2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voice_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column(
            "conversation_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("input_audio_mime_type", sa.Text()),
        sa.Column("input_audio_duration_ms", sa.Integer()),
        sa.Column("input_audio_size_bytes", sa.Integer()),
        sa.Column("transcript", sa.Text()),
        sa.Column("normalized_transcript", sa.Text()),
        sa.Column("detected_language_code", sa.Text()),
        sa.Column("selected_language_code", sa.Text(), nullable=False),
        sa.Column("asr_confidence", sa.Numeric(4, 3)),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error_code", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("timings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("provider IN ('local', 'groq', 'browser')", name="ck_voice_turn_provider"),
        sa.CheckConstraint(
            "status IN ('received', 'transcribed', 'low_confidence', 'agent_completed', 'failed')",
            name="ck_voice_turn_status",
        ),
    )
    op.create_index("idx_voice_turns_session", "voice_turns", ["organisation_id", "conversation_session_id", "created_at"])

    op.create_table(
        "translation_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column(
            "conversation_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        ),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("source_lang", sa.Text(), nullable=False),
        sa.Column("target_lang", sa.Text(), nullable=False),
        sa.Column("input_text_hash", sa.Text(), nullable=False),
        sa.Column("input_text_preview", sa.Text(), nullable=False),
        sa.Column("output_text_preview", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("error_code", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('success', 'fallback_success', 'failed')", name="ck_translation_event_status"),
    )
    op.create_index(
        "idx_translation_events_session",
        "translation_events",
        ["organisation_id", "conversation_session_id", "created_at"],
    )

    op.create_table(
        "tts_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column(
            "conversation_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        ),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("language_code", sa.Text(), nullable=False),
        sa.Column("voice_name", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.Text(), nullable=False),
        sa.Column("audio_mime_type", sa.Text(), nullable=False),
        sa.Column("audio_size_bytes", sa.Integer()),
        sa.Column("speaking_rate", sa.Numeric(4, 2), nullable=False, server_default="1.0"),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("error_code", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('success', 'cache_hit', 'failed')", name="ck_tts_event_status"),
    )

    op.create_table(
        "user_language_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE")),
        sa.Column("session_id", sa.Text()),
        sa.Column("language_code", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "source IN ('selector', 'asr_detected', 'profile_patch')",
            name="ck_language_preference_source",
        ),
        sa.UniqueConstraint("organisation_id", "profile_id", name="uq_language_preference_profile"),
    )


def downgrade() -> None:
    op.drop_table("user_language_preferences")
    op.drop_table("tts_events")
    op.drop_index("idx_translation_events_session")
    op.drop_table("translation_events")
    op.drop_index("idx_voice_turns_session")
    op.drop_table("voice_turns")
