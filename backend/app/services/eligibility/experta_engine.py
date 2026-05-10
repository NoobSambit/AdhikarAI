try:
    from experta import Fact, KnowledgeEngine, Rule
except Exception:  # pragma: no cover - dependency may not be installed in lightweight CI.
    Fact = dict
    KnowledgeEngine = object

    def Rule(*_args, **_kwargs):
        def decorator(func):
            return func

        return decorator

from app.schemas.profile import UserProfileInputModel
from app.services.eligibility.engine import EligibilityEngine, SchemeWithRule


class ProfileFact(Fact):
    pass


class SchemeRuleFact(Fact):
    pass


class SchemeEligibilityEngine(KnowledgeEngine):
    def __init__(self, delegate: EligibilityEngine | None = None) -> None:
        super().__init__()
        self.delegate = delegate or EligibilityEngine()
        self.profile: UserProfileInputModel | None = None
        self.schemes: list[SchemeWithRule] = []
        self.results = []

    def run_evaluation(self, profile: UserProfileInputModel, schemes: list[SchemeWithRule]):
        self.profile = profile
        self.schemes = schemes
        self.results = self.delegate.evaluate(profile, schemes)
        return self.results

    @Rule(ProfileFact(), SchemeRuleFact())
    def evaluate_scheme(self) -> None:
        if self.profile is not None:
            self.results = self.delegate.evaluate(self.profile, self.schemes)

