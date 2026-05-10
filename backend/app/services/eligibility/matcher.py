from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import new_request_id
from app.schemas.match import IncompleteSchemeModel, MatchProfileResponse, MatchedSchemeModel, NearMissSchemeModel
from app.schemas.profile import MatchProfileRequest
from app.services.eligibility.experta_engine import SchemeEligibilityEngine
from app.services.schemes import active_scheme_rules, scheme_summary


async def match_profile(request: MatchProfileRequest, db: AsyncSession, request_id: str | None = None) -> MatchProfileResponse:
    request_id = request_id or new_request_id()
    scheme_rules = await active_scheme_rules(db, request.organisation_id)
    engine = SchemeEligibilityEngine()
    evaluations = engine.run_evaluation(request.profile, scheme_rules)
    by_id = {item.scheme.id: item for item in scheme_rules}
    matched: list[MatchedSchemeModel] = []
    near_miss: list[NearMissSchemeModel] = []
    incomplete: list[IncompleteSchemeModel] = []
    for evaluation in evaluations:
        item = by_id[evaluation.scheme_id]
        summary = scheme_summary(item.scheme, item.rule)
        if evaluation.status == "matched":
            matched.append(
                MatchedSchemeModel(
                    scheme=summary,
                    eligibility_score=100,
                    matched_criteria=evaluation.matched_criteria,
                    explanation=f"You appear eligible for {item.scheme.name}.",
                )
            )
        elif evaluation.status == "near_miss":
            failed = evaluation.failed_criteria[0]
            score = max(50, min(99, int(100 * len(evaluation.matched_criteria) / (len(evaluation.matched_criteria) + 1 or 1))))
            near_miss.append(
                NearMissSchemeModel(
                    scheme=summary,
                    eligibility_score=score,
                    failed_criterion=failed.criterion_id,
                    failed_value=failed.actual,
                    required_value=failed.expected,
                    how_to_qualify=failed.how_to_qualify,
                )
            )
        elif evaluation.status == "incomplete" and request.include_incomplete:
            incomplete.append(
                IncompleteSchemeModel(
                    scheme=summary,
                    unknown_criteria=evaluation.unknown_criteria,
                    explanation="More information is needed before this scheme can be checked.",
                )
            )
    matched.sort(key=lambda item: (item.scheme.benefit_type, -item.eligibility_score, item.scheme.name))
    near_miss.sort(key=lambda item: (-item.eligibility_score, item.scheme.name))
    return MatchProfileResponse(
        matched_schemes=matched[: request.limit],
        near_miss_schemes=near_miss[: request.limit],
        incomplete_schemes=incomplete[: request.limit] if request.include_incomplete else [],
        evaluated_scheme_count=len(evaluations),
        request_id=request_id,
    )

