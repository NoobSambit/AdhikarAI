from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Gender = Literal["female", "male", "other", "unknown"]
CasteCategory = Literal["SC", "ST", "OBC", "GENERAL", "UNKNOWN"]
MaritalStatus = Literal["single", "married", "widowed", "divorced", "separated", "unknown"]
CustomOperator = Literal["equals", "not_equals", "in", "lte", "gte"]


class DocumentSubstituteModel(BaseModel):
    name: str
    instructions: str
    estimated_cost_inr: int = Field(ge=0)
    estimated_time_days: int = Field(ge=0)
    issuing_authority: str


class RequiredDocumentModel(BaseModel):
    name: str
    is_mandatory: bool
    accepted_substitutes: list[DocumentSubstituteModel] = Field(default_factory=list)


class CustomCriterionModel(BaseModel):
    field: str
    operator: CustomOperator
    value: Any
    how_to_qualify: str


class EligibilityCriteriaModel(BaseModel):
    min_age: int | None = Field(default=None, ge=0)
    max_age: int | None = Field(default=None, ge=0)
    gender: list[Gender] | None = None
    caste_categories: list[CasteCategory] | None = None
    max_annual_income: int | None = Field(default=None, ge=0)
    max_land_holding_acres: float | None = Field(default=None, ge=0)
    occupation_types: list[str] | None = None
    marital_status: list[MaritalStatus] | None = None
    state_codes: list[str] | None = None
    exclusion_scheme_ids: list[str] = Field(default_factory=list)
    required_documents: list[RequiredDocumentModel] = Field(default_factory=list)
    custom_criteria: list[CustomCriterionModel] = Field(default_factory=list)


class SchemeSummaryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    ministry: str
    state_code: str | None
    benefit_type: str
    benefit_amount: str
    application_url: str | None
    is_active: bool
    valid_until: date | None
    required_documents: list[RequiredDocumentModel] = Field(default_factory=list)


class SchemeDetailModel(SchemeSummaryModel):
    plain_language_summary: str
    status: str
    valid_from: date | None = None
    source_url: str | None = None
    verification_status: str
    source_last_checked_at: datetime | None = None
    eligibility_rule: EligibilityCriteriaModel


class CreateSchemeRequest(BaseModel):
    organisation_id: str
    id: str
    category_code: str | None = None
    name: str
    description: str
    plain_language_summary: str = ""
    ministry: str
    state_code: str | None = None
    benefit_type: str
    benefit_amount: str
    application_url: str | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    source_url: str
    verification_status: Literal["needs_admin_review", "verified", "rejected"] = "needs_admin_review"
    external_source: str | None = None
    external_id: str | None = None
    source_last_checked_at: datetime | None = None
    eligibility_rule: EligibilityCriteriaModel

    @field_validator("id")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        return value.strip()


class UpdateSchemeRequest(BaseModel):
    organisation_id: str
    change_summary: str
    publish: bool = False
    category_code: str | None = None
    name: str | None = None
    description: str | None = None
    plain_language_summary: str | None = None
    ministry: str | None = None
    state_code: str | None = None
    benefit_type: str | None = None
    benefit_amount: str | None = None
    application_url: str | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    source_url: str | None = None
    verification_status: Literal["needs_admin_review", "verified", "rejected"] | None = None
    eligibility_rule: EligibilityCriteriaModel | None = None


class AdminSchemeResponse(BaseModel):
    id: str
    version: int
    status: str
    validation_warnings: list[str] = Field(default_factory=list)


class PublishSchemeRequest(BaseModel):
    organisation_id: str


class ArchiveSchemeRequest(BaseModel):
    organisation_id: str
    reason: str

