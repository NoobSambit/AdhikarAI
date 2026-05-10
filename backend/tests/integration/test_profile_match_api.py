from types import SimpleNamespace

import pytest

from app.api.routes.profile_match import profile_match
from app.schemas.match import MatchProfileResponse, MatchedSchemeModel
from app.schemas.profile import MatchProfileRequest, UserProfileInputModel
from app.schemas.scheme import SchemeSummaryModel


@pytest.mark.asyncio
async def test_profile_match_api_returns_pm_kisan(monkeypatch):
    async def fake_match_profile(request, db, request_id=None):
        return MatchProfileResponse(
            matched_schemes=[
                MatchedSchemeModel(
                    scheme=SchemeSummaryModel(
                        id="pm_kisan",
                        name="Pradhan Mantri Kisan Samman Nidhi",
                        description="Income support for eligible farmer families.",
                        ministry="Ministry",
                        state_code=None,
                        benefit_type="cash_transfer",
                        benefit_amount="INR 6,000 per year",
                        application_url=None,
                        is_active=True,
                        valid_until=None,
                        required_documents=[],
                    ),
                    eligibility_score=100,
                    matched_criteria=["occupation_type"],
                    explanation="You appear eligible.",
                )
            ],
            near_miss_schemes=[],
            incomplete_schemes=[],
            evaluated_scheme_count=1,
            request_id=request_id or "req_test",
        )

    monkeypatch.setattr("app.api.routes.profile_match.match_profile", fake_match_profile)
    response = await profile_match(
        MatchProfileRequest(
            organisation_id="00000000-0000-0000-0000-000000000001",
            profile=UserProfileInputModel(age=34, occupation_type="farmer", existing_scheme_ids=[]),
        ),
        SimpleNamespace(state=SimpleNamespace(request_id="req_test")),
        db=None,
    )
    assert response.matched_schemes[0].scheme.id == "pm_kisan"
