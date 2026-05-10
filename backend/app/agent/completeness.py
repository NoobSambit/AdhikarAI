from typing import Any

from app.schemas.scheme import EligibilityCriteriaModel

FIELD_WEIGHTS = {
    "state_code": 15,
    "age": 15,
    "gender": 10,
    "annual_income": 15,
    "occupation_type": 15,
    "caste_category": 8,
    "marital_status": 8,
    "land_holding_acres": 8,
}
BASE_FIELDS = {"state_code", "age", "gender", "occupation_type", "annual_income"}


def fields_referenced_by_rule(rule: EligibilityCriteriaModel) -> set[str]:
    fields: set[str] = set()
    if rule.min_age is not None or rule.max_age is not None:
        fields.add("age")
    if rule.gender:
        fields.add("gender")
    if rule.caste_categories:
        fields.add("caste_category")
    if rule.max_annual_income is not None:
        fields.add("annual_income")
    if rule.max_land_holding_acres is not None:
        fields.add("land_holding_acres")
    if rule.occupation_types:
        fields.add("occupation_type")
    if rule.marital_status:
        fields.add("marital_status")
    if rule.state_codes:
        fields.add("state_code")
    for criterion in rule.custom_criteria:
        fields.add(f"custom_attributes.{criterion.field}")
    return fields


def _has_value(profile: dict[str, Any], field: str) -> bool:
    if field.startswith("custom_attributes."):
        key = field.split(".", 1)[1]
        return profile.get("custom_attributes", {}).get(key) is not None
    return profile.get(field) is not None


def compute_profile_completeness(profile: dict[str, Any], candidate_rules: list[EligibilityCriteriaModel]) -> int:
    relevant_fields: set[str] = set(BASE_FIELDS)
    for rule in candidate_rules[:20]:
        relevant_fields.update(fields_referenced_by_rule(rule))

    custom_fields = sorted(field for field in relevant_fields if field.startswith("custom_attributes."))
    normal_fields = sorted(field for field in relevant_fields if not field.startswith("custom_attributes."))
    custom_weight = 6 / len(custom_fields) if custom_fields else 0

    total = 0.0
    answered = 0.0
    for field in normal_fields:
        weight = FIELD_WEIGHTS.get(field, 0)
        total += weight
        if _has_value(profile, field):
            answered += weight
    for field in custom_fields:
        total += custom_weight
        if _has_value(profile, field):
            answered += custom_weight

    if total <= 0:
        return 0
    return max(0, min(100, int(round((answered / total) * 100))))
