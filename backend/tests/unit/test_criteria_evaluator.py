from app.schemas.profile import UserProfileInputModel
from app.schemas.scheme import CustomCriterionModel, EligibilityCriteriaModel
from app.services.eligibility.criteria import CriterionEvaluator


def test_cross_scheme_exclusion_blocks_match():
    profile = UserProfileInputModel(existing_scheme_ids=["pmay_g"])
    criteria = EligibilityCriteriaModel(exclusion_scheme_ids=["pmay_g"])
    result = CriterionEvaluator().evaluate_scheme("target", criteria, profile)
    assert result.status == "ineligible"
    assert result.reason == "already_receives_excluded_scheme"
    assert not result.is_near_miss


def test_missing_profile_field_is_unknown_not_failed():
    profile = UserProfileInputModel(age=30, existing_scheme_ids=[])
    criteria = EligibilityCriteriaModel(caste_categories=["SC"])
    result = CriterionEvaluator().evaluate_scheme("scholarship", criteria, profile)
    assert result.status == "incomplete"
    assert result.unknown_criteria == ["caste_category"]


def test_custom_criterion_lte():
    profile = UserProfileInputModel(custom_attributes={"monthly_income": 14000})
    criteria = EligibilityCriteriaModel(
        custom_criteria=[
            CustomCriterionModel(
                field="monthly_income",
                operator="lte",
                value=15000,
                how_to_qualify="Income must be within the limit.",
            )
        ]
    )
    result = CriterionEvaluator().evaluate_scheme("pm_sym", criteria, profile)
    assert result.status == "matched"
    assert result.matched_criteria == ["monthly_income"]

