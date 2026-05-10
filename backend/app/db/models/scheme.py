from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SchemeCategory(Base):
    __tablename__ = "scheme_categories"
    __table_args__ = (UniqueConstraint("organisation_id", "code"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Scheme(Base):
    __tablename__ = "schemes"
    __table_args__ = (
        CheckConstraint("state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$'", name="ck_scheme_state_code"),
        CheckConstraint("status IN ('draft', 'active', 'expired', 'archived', 'upcoming')", name="ck_scheme_status"),
        CheckConstraint(
            "verification_status IN ('needs_admin_review', 'verified', 'rejected')",
            name="ck_scheme_verification_status",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("scheme_categories.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    plain_language_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ministry: Mapped[str] = mapped_column(Text, nullable=False)
    state_code: Mapped[str | None] = mapped_column(Text)
    benefit_type: Mapped[str] = mapped_column(Text, nullable=False)
    benefit_amount: Mapped[str] = mapped_column(Text, nullable=False)
    application_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)
    external_source: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, default="needs_admin_review")
    source_last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    rules: Mapped[list["EligibilityRule"]] = relationship(back_populates="scheme")


class SchemeStatusEvent(Base):
    __tablename__ = "scheme_status_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(Text)
    new_status: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FaissIndex(Base):
    __tablename__ = "faiss_indexes"
    __table_args__ = (UniqueConstraint("organisation_id", "index_name", "content_hash"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    index_name: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    vector_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    scheme_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SchemeEmbedding(Base):
    __tablename__ = "scheme_embeddings"
    __table_args__ = (UniqueConstraint("organisation_id", "scheme_id", "embedding_model"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_json: Mapped[list[float] | None] = mapped_column(JSONB)
    embedding_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

