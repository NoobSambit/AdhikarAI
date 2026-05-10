from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("age IS NULL OR (age >= 0 AND age <= 120)", name="ck_profile_age"),
        CheckConstraint("gender IS NULL OR gender IN ('female', 'male', 'other', 'unknown')", name="ck_profile_gender"),
        CheckConstraint(
            "caste_category IS NULL OR caste_category IN ('SC', 'ST', 'OBC', 'GENERAL', 'UNKNOWN')",
            name="ck_profile_caste_category",
        ),
        CheckConstraint("annual_income IS NULL OR annual_income >= 0", name="ck_profile_annual_income"),
        CheckConstraint("land_holding_acres IS NULL OR land_holding_acres >= 0", name="ck_profile_land_holding"),
        CheckConstraint(
            "marital_status IS NULL OR marital_status IN ('single', 'married', 'widowed', 'divorced', 'separated', 'unknown')",
            name="ck_profile_marital_status",
        ),
        CheckConstraint("state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$'", name="ck_profile_state_code"),
        CheckConstraint("profile_completeness >= 0 AND profile_completeness <= 100", name="ck_profile_completeness"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    household_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("households.id", ondelete="SET NULL"))
    display_name: Mapped[str | None] = mapped_column(Text)
    relationship_to_primary: Mapped[str] = mapped_column(Text, nullable=False, default="self", server_default="self")
    age: Mapped[int | None] = mapped_column(Integer)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(Text)
    caste_category: Mapped[str | None] = mapped_column(Text)
    annual_income: Mapped[int | None] = mapped_column(Integer)
    land_holding_acres: Mapped[float | None] = mapped_column(Numeric(8, 2))
    occupation_type: Mapped[str | None] = mapped_column(Text)
    marital_status: Mapped[str | None] = mapped_column(Text)
    state_code: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    existing_scheme_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    custom_attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    profile_completeness: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_match_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    household: Mapped["Household | None"] = relationship(back_populates="profiles")
