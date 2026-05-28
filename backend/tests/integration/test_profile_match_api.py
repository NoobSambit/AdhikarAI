from types import SimpleNamespace
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.profile_match import profile_match
from app.db.models import EligibilityRule, Organisation, Scheme
from app.schemas.profile import MatchProfileRequest, UserProfileInputModel
from app.schemas.scheme import CustomCriterionModel, DocumentSubstituteModel, EligibilityCriteriaModel, RequiredDocumentModel


@pytest.mark.asyncio
async def test_profile_match_api_uses_real_rules_and_filters_expired(db_session: AsyncSession, organisation: Organisation):
    substitute = DocumentSubstituteModel(
        name="Gram panchayat certificate",
        instructions="Ask the panchayat office for a signed income certificate.",
        estimated_cost_inr=20,
        estimated_time_days=7,
        issuing_authority="Gram Panchayat",
    )
    cases = [
        (
            "pm_kisan",
            "Pradhan Mantri Kisan Samman Nidhi",
            None,
            EligibilityCriteriaModel(
                occupation_types=["farmer"],
                max_land_holding_acres=2,
                required_documents=[
                    RequiredDocumentModel(
                        name="Land record",
                        is_mandatory=True,
                        accepted_substitutes=[substitute],
                    )
                ],
            ),
        ),
        (
            "widow_pension",
            "Widow Pension",
            None,
            EligibilityCriteriaModel(gender=["female"], marital_status=["widowed"], max_annual_income=120000),
        ),
        (
            "student_support",
            "Student Support",
            None,
            EligibilityCriteriaModel(
                custom_criteria=[
                    CustomCriterionModel(
                        field="is_student",
                        operator="equals",
                        value=True,
                        how_to_qualify="This scheme is for students.",
                    )
                ]
            ),
        ),
        (
            "expired_farmer",
            "Expired Farmer Scheme",
            date.today() - timedelta(days=1),
            EligibilityCriteriaModel(occupation_types=["farmer"]),
        ),
    ]
    for scheme_id, name, valid_until, rule in cases:
        db_session.add(
            Scheme(
                id=f"{organisation.id}-{scheme_id}",
                organisation_id=organisation.id,
                name=name,
                description=name,
                plain_language_summary=name,
                ministry="Ministry",
                benefit_type="cash_transfer",
                benefit_amount="INR 1,000",
                valid_until=valid_until,
                is_active=True,
                status="active",
            )
        )
        db_session.add(
            EligibilityRule(
                organisation_id=organisation.id,
                scheme_id=f"{organisation.id}-{scheme_id}",
                version=1,
                criteria=rule.model_dump(mode="json"),
                is_active=True,
            )
        )
    await db_session.commit()

    response = await profile_match(
        MatchProfileRequest(
            organisation_id=str(organisation.id),
            profile=UserProfileInputModel(
                age=34,
                gender="female",
                occupation_type="farmer",
                marital_status="married",
                land_holding_acres=1,
                state_code="IN-UP",
                annual_income=72000,
                existing_scheme_ids=[],
            ),
            include_incomplete=True,
        ),
        SimpleNamespace(state=SimpleNamespace(request_id="req_test")),
        db_session,
    )

    assert [item.scheme.id for item in response.matched_schemes] == [f"{organisation.id}-pm_kisan"]
    assert response.matched_schemes[0].scheme.required_documents[0].accepted_substitutes[0].name == "Gram panchayat certificate"
    assert [item.scheme.id for item in response.near_miss_schemes] == [f"{organisation.id}-widow_pension"]
    assert [item.scheme.id for item in response.incomplete_schemes] == [f"{organisation.id}-student_support"]
    assert f"{organisation.id}-expired_farmer" not in {
        item.scheme.id for item in response.matched_schemes + response.near_miss_schemes + response.incomplete_schemes
    }
