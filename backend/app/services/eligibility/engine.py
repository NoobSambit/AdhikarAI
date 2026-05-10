from dataclasses import dataclass

from app.schemas.profile import UserProfileInputModel
from app.schemas.scheme import EligibilityCriteriaModel
from app.services.eligibility.criteria import CriterionEvaluator, SchemeEvaluation


@dataclass(frozen=True, slots=True)
class SchemeWithRule:
    scheme: object
    rule: EligibilityCriteriaModel


class EligibilityEngine:
    def __init__(self, evaluator: CriterionEvaluator | None = None) -> None:
        self.evaluator = evaluator or CriterionEvaluator()

    def evaluate(self, profile: UserProfileInputModel, schemes: list[SchemeWithRule]) -> list[SchemeEvaluation]:
        return [self.evaluate_scheme(profile, scheme) for scheme in schemes]

    def evaluate_scheme(self, profile: UserProfileInputModel, scheme: SchemeWithRule) -> SchemeEvaluation:
        scheme_id = getattr(scheme.scheme, "id")
        return self.evaluator.evaluate_scheme(scheme_id, scheme.rule, profile)

