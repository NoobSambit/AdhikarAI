from typing import Any

from pydantic import BaseModel, Field

from app.schemas.scheme import SchemeSummaryModel


class MatchedSchemeModel(BaseModel):
    scheme: SchemeSummaryModel
    eligibility_score: int
    matched_criteria: list[str]
    explanation: str


class NearMissSchemeModel(BaseModel):
    scheme: SchemeSummaryModel
    eligibility_score: int
    failed_criterion: str
    failed_value: Any
    required_value: Any
    how_to_qualify: str


class IncompleteSchemeModel(BaseModel):
    scheme: SchemeSummaryModel
    unknown_criteria: list[str]
    explanation: str


class MatchProfileResponse(BaseModel):
    matched_schemes: list[MatchedSchemeModel]
    near_miss_schemes: list[NearMissSchemeModel]
    incomplete_schemes: list[IncompleteSchemeModel] = Field(default_factory=list)
    evaluated_scheme_count: int
    request_id: str

