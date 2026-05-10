from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Household(Base):
    __tablename__ = "households"
    __table_args__ = (CheckConstraint("state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$'", name="ck_household_state_code"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    state_code: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    village: Mapped[str | None] = mapped_column(Text)
    pincode: Mapped[str | None] = mapped_column(Text)
    ration_card_type: Mapped[str | None] = mapped_column(Text)
    annual_household_income: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    profiles: Mapped[list["Profile"]] = relationship(back_populates="household")
