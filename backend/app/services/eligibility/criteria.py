from dataclasses import dataclass, field
from typing import Any

from app.schemas.profile import UserProfileInputModel
from app.schemas.scheme import CustomCriterionModel, EligibilityCriteriaModel


@dataclass(frozen=True, slots=True)
class CriterionResult:
    criterion_id: str
    status: str
    actual: Any = None
    expected: Any = None
    how_to_qualify: str = ""


@dataclass(slots=True)
class SchemeEvaluation:
    scheme_id: str
    status: str
    matched_criteria: list[str] = field(default_factory=list)
    failed_criteria: list[CriterionResult] = field(default_factory=list)
    unknown_criteria: list[str] = field(default_factory=list)
    reason: str | None = None

    @property
    def is_match(self) -> bool:
        return self.status == "matched"

    @property
    def is_near_miss(self) -> bool:
        return self.status == "near_miss"


def _unknown(value: Any) -> bool:
    return value is None or value == "unknown" or value == "UNKNOWN"


def evaluate_custom_criterion(criterion: CustomCriterionModel, actual: Any) -> CriterionResult:
    expected = criterion.value
    status = "matched"
    try:
        if _unknown(actual):
            status = "unknown"
        elif criterion.operator == "equals":
            status = "matched" if actual == expected else "failed"
        elif criterion.operator == "not_equals":
            status = "matched" if actual != expected else "failed"
        elif criterion.operator == "in":
            status = "matched" if actual in expected else "failed"
        elif criterion.operator == "lte":
            status = "matched" if actual <= expected else "failed"
        elif criterion.operator == "gte":
            status = "matched" if actual >= expected else "failed"
        else:
            status = "failed"
    except TypeError:
        status = "failed"
    return CriterionResult(criterion.field, status, actual, expected, criterion.how_to_qualify)


class CriterionEvaluator:
    def evaluate_scheme(
        self,
        scheme_id: str,
        criteria: EligibilityCriteriaModel,
        profile: UserProfileInputModel,
    ) -> SchemeEvaluation:
        existing = set(profile.existing_scheme_ids)
        exclusions = set(criteria.exclusion_scheme_ids)
        if existing & exclusions:
            return SchemeEvaluation(
                scheme_id=scheme_id,
                status="ineligible",
                reason="already_receives_excluded_scheme",
            )

        results: list[CriterionResult] = []
        if criteria.min_age is not None:
            results.append(self._gte("age", profile.age, criteria.min_age, f"This scheme requires age at least {criteria.min_age}."))
        if criteria.max_age is not None:
            results.append(self._lte("age", profile.age, criteria.max_age, f"This scheme requires age at most {criteria.max_age}."))
        if criteria.gender:
            results.append(self._in("gender", profile.gender, criteria.gender, f"This scheme is for: {', '.join(criteria.gender)}."))
        if criteria.caste_categories:
            results.append(
                self._in(
                    "caste_category",
                    profile.caste_category,
                    criteria.caste_categories,
                    f"This scheme requires caste category in {', '.join(criteria.caste_categories)}.",
                )
            )
        if criteria.max_annual_income is not None:
            results.append(
                self._lte(
                    "annual_income",
                    profile.annual_income,
                    criteria.max_annual_income,
                    f"This scheme requires annual household income at or below INR {criteria.max_annual_income:,}.",
                )
            )
        if criteria.max_land_holding_acres is not None:
            results.append(
                self._lte(
                    "land_holding_acres",
                    profile.land_holding_acres,
                    criteria.max_land_holding_acres,
                    f"This scheme requires land holding at or below {criteria.max_land_holding_acres} acres.",
                )
            )
        if criteria.occupation_types:
            results.append(self._in("occupation_type", profile.occupation_type, criteria.occupation_types, "This scheme requires a covered occupation."))
        if criteria.marital_status:
            results.append(self._in("marital_status", profile.marital_status, criteria.marital_status, "This scheme requires a matching marital status."))
        if criteria.state_codes:
            results.append(self._in("state_code", profile.state_code, criteria.state_codes, "This scheme is available only in selected states."))
        for custom in criteria.custom_criteria:
            results.append(evaluate_custom_criterion(custom, profile.custom_attributes.get(custom.field)))

        failed = [result for result in results if result.status == "failed"]
        unknown = [result.criterion_id for result in results if result.status == "unknown"]
        matched = [result.criterion_id for result in results if result.status == "matched"]
        if failed:
            if len(failed) == 1 and not unknown:
                return SchemeEvaluation(scheme_id, "near_miss", matched, failed, unknown)
            return SchemeEvaluation(scheme_id, "ineligible", matched, failed, unknown)
        if unknown:
            return SchemeEvaluation(scheme_id, "incomplete", matched, failed, unknown)
        return SchemeEvaluation(scheme_id, "matched", matched, failed, unknown)

    def _in(self, criterion_id: str, actual: Any, expected: list[Any], how: str) -> CriterionResult:
        if _unknown(actual):
            return CriterionResult(criterion_id, "unknown", actual, expected, how)
        return CriterionResult(criterion_id, "matched" if actual in expected else "failed", actual, expected, how)

    def _lte(self, criterion_id: str, actual: Any, expected: int | float, how: str) -> CriterionResult:
        if _unknown(actual):
            return CriterionResult(criterion_id, "unknown", actual, expected, how)
        return CriterionResult(criterion_id, "matched" if actual <= expected else "failed", actual, expected, how)

    def _gte(self, criterion_id: str, actual: Any, expected: int | float, how: str) -> CriterionResult:
        if _unknown(actual):
            return CriterionResult(criterion_id, "unknown", actual, expected, how)
        return CriterionResult(criterion_id, "matched" if actual >= expected else "failed", actual, expected, how)

