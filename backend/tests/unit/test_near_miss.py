from app.schemas.profile import UserProfileInputModel
from app.schemas.scheme import EligibilityCriteriaModel
from app.services.eligibility.criteria import CriterionEvaluator


def test_near_miss_exactly_one_failure():
    profile = UserProfileInputModel(age=34, annual_income=130000, existing_scheme_ids=[])
    criteria = EligibilityCriteriaModel(min_age=18, max_annual_income=120000)
    result = CriterionEvaluator().evaluate_scheme("income_scheme", criteria, profile)
    assert result.status == "near_miss"
    assert result.failed_criteria[0].criterion_id == "annual_income"


def test_two_failures_not_near_miss():
    profile = UserProfileInputModel(age=16, annual_income=130000, existing_scheme_ids=[])
    criteria = EligibilityCriteriaModel(min_age=18, max_annual_income=120000)
    result = CriterionEvaluator().evaluate_scheme("income_scheme", criteria, profile)
    assert result.status == "ineligible"
    assert not result.is_near_miss

