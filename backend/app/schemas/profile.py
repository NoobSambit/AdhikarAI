from typing import Any

from pydantic import BaseModel, Field

from app.schemas.scheme import CasteCategory, Gender, MaritalStatus


class UserProfileInputModel(BaseModel):
    age: int | None = Field(default=None, ge=0, le=120)
    gender: Gender | None = None
    caste_category: CasteCategory | None = None
    annual_income: int | None = Field(default=None, ge=0)
    land_holding_acres: float | None = Field(default=None, ge=0)
    occupation_type: str | None = None
    marital_status: MaritalStatus | None = None
    state_code: str | None = None
    district: str | None = None
    existing_scheme_ids: list[str] = Field(default_factory=list)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class MatchProfileRequest(BaseModel):
    organisation_id: str
    profile: UserProfileInputModel
    include_incomplete: bool = False
    limit: int = Field(default=50, ge=1, le=200)

