from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.scheme import CasteCategory, Gender, MaritalStatus

ALLOWED_LANGUAGE_CODES = {"en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or"}
AgentMessageType = Literal["question", "result", "clarification", "error", "state"]


class HouseholdMemberProfileModel(BaseModel):
    id: str | None = None
    display_name: str | None = None
    relationship_to_primary: str = "self"
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
    profile_completeness: int = Field(default=0, ge=0, le=100)


class HouseholdStateModel(BaseModel):
    id: str | None = None
    state_code: str | None = None
    district: str | None = None
    village: str | None = None
    pincode: str | None = None
    ration_card_type: str | None = None
    annual_household_income: int | None = Field(default=None, ge=0)
    members: list[HouseholdMemberProfileModel] = Field(default_factory=list)


class AgentStateModel(BaseModel):
    session_id: str
    organisation_id: str
    messages: list[dict[str, str]] = Field(default_factory=list)
    user_profile: HouseholdMemberProfileModel = Field(default_factory=HouseholdMemberProfileModel)
    household: HouseholdStateModel = Field(default_factory=HouseholdStateModel)
    active_member_id: str = "self"
    asked_fields: list[str] = Field(default_factory=list)
    remaining_required_fields: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0, ge=0, le=1)
    profile_completeness: int = Field(default=0, ge=0, le=100)
    language_code: str = "en"
    last_match_result: dict[str, Any] | None = None
    turn_count_since_result: int = 0
    pending_confirmation: dict[str, Any] | None = None

    @field_validator("language_code")
    @classmethod
    def validate_language_code(cls, value: str) -> str:
        if value not in ALLOWED_LANGUAGE_CODES:
            raise ValueError("Unsupported language code.")
        return value


class CreateSessionRequest(BaseModel):
    organisation_id: UUID
    session_id: str | None = None
    language_code: str = "en"

    @field_validator("language_code")
    @classmethod
    def validate_language_code(cls, value: str) -> str:
        if value not in ALLOWED_LANGUAGE_CODES:
            raise ValueError("Unsupported language code.")
        return value


class CreateSessionResponse(BaseModel):
    session_id: str
    profile_id: UUID
    household_id: UUID
    greeting: str
    profile_completeness: int


class ChatInputModel(BaseModel):
    organisation_id: UUID | None = None
    session_id: str
    message: str = Field(min_length=1, max_length=2000)
    language_code: str = "en"

    @field_validator("language_code")
    @classmethod
    def validate_language_code(cls, value: str) -> str:
        if value not in ALLOWED_LANGUAGE_CODES:
            raise ValueError("Unsupported language code.")
        return value


class ChatOutputModel(BaseModel):
    type: AgentMessageType
    content: str
    profile_completeness: int
    session_id: str
    payload: dict[str, Any] | None = None


class PatchProfileRequest(BaseModel):
    organisation_id: UUID
    fields: dict[str, Any]
    source: Literal["conversation", "api_patch"] = "api_patch"


class PatchProfileResponse(BaseModel):
    profile: HouseholdMemberProfileModel
    changed_fields: list[str]
    profile_completeness: int
    match_snapshot: dict[str, Any]
