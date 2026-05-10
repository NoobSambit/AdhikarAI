from dataclasses import dataclass
from typing import Any

from app.agent.completeness import fields_referenced_by_rule
from app.schemas.agent import AgentStateModel
from app.schemas.scheme import EligibilityCriteriaModel

QUESTION_TEMPLATES = {
    "state_code": "Which state do you live in?",
    "age": "How old are you?",
    "gender": "Should I mark this profile as woman, man, or other?",
    "annual_income": "About how much money does your household earn in one year?",
    "occupation_type": "What work do you mainly do?",
    "caste_category": "Do you belong to SC, ST, OBC, or General category?",
    "marital_status": "Are you married, unmarried, widowed, divorced, or separated?",
    "land_holding_acres": "How much farming land does your family have, in acres?",
    "custom_attributes.is_bpl": "Do you have a BPL card or ration card for a poor household?",
    "fallback": "Do you want me to show the best schemes I found so far?",
}
FIELD_WEIGHT = {
    "state_code": 3.0,
    "annual_income": 2.8,
    "age": 2.6,
    "occupation_type": 2.4,
    "gender": 2.0,
    "marital_status": 1.8,
    "caste_category": 1.5,
    "land_holding_acres": 1.4,
}


@dataclass(frozen=True)
class Question:
    field: str
    text: str
    asked_key: str


def _profile_value(profile: dict[str, Any], field: str) -> Any:
    if field.startswith("custom_attributes."):
        return profile.get("custom_attributes", {}).get(field.split(".", 1)[1])
    return profile.get(field)


def compute_information_gain(field: str, candidate_rules: list[EligibilityCriteriaModel]) -> float:
    score = 0.0
    for rule in candidate_rules:
        if field in fields_referenced_by_rule(rule):
            score += FIELD_WEIGHT.get(field, 1.0)
    return score


def select_next_question(state: AgentStateModel, candidate_rules: list[EligibilityCriteriaModel]) -> Question:
    scores: dict[str, float] = {}
    profile = state.user_profile.model_dump()
    for rule in candidate_rules:
        for field in fields_referenced_by_rule(rule):
            asked_key = f"{state.active_member_id}:{field}"
            if asked_key in state.asked_fields or _profile_value(profile, field) is not None:
                continue
            scores[field] = scores.get(field, 0.0) + compute_information_gain(field, [rule])

    if not scores:
        return Question(field="fallback", text=QUESTION_TEMPLATES["fallback"], asked_key=f"{state.active_member_id}:fallback")
    field = max(scores, key=lambda key: (scores[key], FIELD_WEIGHT.get(key, 1.0), key))
    return Question(field=field, text=QUESTION_TEMPLATES.get(field, QUESTION_TEMPLATES["fallback"]), asked_key=f"{state.active_member_id}:{field}")
