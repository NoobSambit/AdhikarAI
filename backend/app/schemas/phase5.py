from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


DashboardRole = Literal["super_admin", "ngo_admin", "operator"]


class DashboardMeResponse(BaseModel):
    member_id: UUID
    organisation_id: UUID
    role: DashboardRole
    display_name: str
    permissions: list[str]


class CreateBeneficiaryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone_e164: str | None = None
    state_code: str
    language_code: str = "hi"
    village: str | None = None
    district: str | None = None
    assigned_operator_id: UUID | None = None
    profile: dict[str, Any] = Field(default_factory=dict)
    household_members: list[dict[str, Any]] = Field(default_factory=list)


class UpdateBeneficiaryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone_e164: str | None = None
    state_code: str | None = None
    language_code: str | None = None
    village: str | None = None
    district: str | None = None
    assigned_operator_id: UUID | None = None
    profile: dict[str, Any] | None = None


class BeneficiaryResponse(BaseModel):
    id: UUID
    name: str
    phone_e164: str | None
    state_code: str
    language_code: str
    village: str | None = None
    district: str | None = None
    profile_id: UUID
    assigned_operator_id: UUID | None
    application_statuses: list[dict[str, Any]] = Field(default_factory=list)
    follow_up: dict[str, Any] | None = None


class BeneficiaryDetailResponse(BeneficiaryResponse):
    profile: dict[str, Any] = Field(default_factory=dict)
    notes: list[dict[str, Any]] = Field(default_factory=list)
    followups: list[dict[str, Any]] = Field(default_factory=list)
    assigned_schemes: list[dict[str, Any]] = Field(default_factory=list)


class BeneficiaryListResponse(BaseModel):
    items: list[BeneficiaryResponse]
    total: int


class BeneficiaryNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=5000)


class FollowupRequest(BaseModel):
    due_date: date
    reason: str | None = Field(default=None, max_length=500)


class FollowupUpdateRequest(BaseModel):
    status: Literal["completed", "cancelled"]


class EligibilityRunRequest(BaseModel):
    assign_matched_schemes: bool = True


class EligibilityRunResponse(BaseModel):
    matched_schemes: list[Any]
    near_miss_schemes: list[Any]
    assigned_count: int


class BulkJobCreateResponse(BaseModel):
    job_id: UUID
    status: str


class BulkJobStatusResponse(BaseModel):
    id: UUID
    status: Literal["queued", "processing", "completed", "completed_with_errors", "failed"]
    total_rows: int
    processed_rows: int
    failed_rows: int
    result_storage_url: str | None = None


class ApplicationStatusUpdateRequest(BaseModel):
    status: Literal["not_started", "documents_gathering", "submitted", "pending", "approved", "rejected"]
    notes: str | None = Field(default=None, max_length=2000)


class SchemeDraftRequest(BaseModel):
    draft_payload: dict[str, Any]
    change_summary: str = Field(min_length=5, max_length=1000)


class ReviewQualityFlagRequest(BaseModel):
    review_notes: str = Field(min_length=1, max_length=2000)


class GroupedUnmatchedQuery(BaseModel):
    normalized_query_text: str
    frequency: int
    languages: list[str]
    latest_at: datetime
