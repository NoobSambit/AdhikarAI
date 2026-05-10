import re
from dataclasses import dataclass

from pydantic import ValidationError

from app.schemas.scheme import EligibilityCriteriaModel

STATE_CODE_RE = re.compile(r"^IN-[A-Z]{2}$")
ALLOWED_CUSTOM_OPERATORS = {"equals", "not_equals", "in", "lte", "gte"}


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    field: str


def validate_rule(criteria: EligibilityCriteriaModel, known_scheme_ids: set[str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if criteria.required_documents is None:
        issues.append(
            ValidationIssue(
                "RULE_MISSING_REQUIRED_DOCUMENTS_ARRAY",
                "required_documents must be an array.",
                "criteria.required_documents",
            )
        )
    if criteria.min_age is not None and criteria.max_age is not None and criteria.min_age > criteria.max_age:
        issues.append(
            ValidationIssue(
                "RULE_CONTRADICTION",
                "Minimum age cannot be greater than maximum age.",
                "criteria.min_age",
            )
        )
    for field, value in (
        ("max_annual_income", criteria.max_annual_income),
        ("max_land_holding_acres", criteria.max_land_holding_acres),
    ):
        if value is not None and value < 0:
            issues.append(ValidationIssue("NEGATIVE_THRESHOLD", "Threshold cannot be negative.", f"criteria.{field}"))
    for state_code in criteria.state_codes or []:
        if not STATE_CODE_RE.match(state_code):
            issues.append(ValidationIssue("INVALID_STATE_CODE", "State code must use ISO 3166-2 IN format.", "criteria.state_codes"))
    missing = sorted(set(criteria.exclusion_scheme_ids) - known_scheme_ids)
    if missing:
        issues.append(
            ValidationIssue(
                "BROKEN_EXCLUSION_REFERENCE",
                "Exclusion references unknown schemes in this organisation.",
                "criteria.exclusion_scheme_ids",
            )
        )
    for index, criterion in enumerate(criteria.custom_criteria):
        if criterion.operator not in ALLOWED_CUSTOM_OPERATORS:
            issues.append(
                ValidationIssue(
                    "INVALID_CUSTOM_OPERATOR",
                    "Custom criterion operator is not supported.",
                    f"criteria.custom_criteria.{index}.operator",
                )
            )
        if not criterion.field.strip():
            issues.append(
                ValidationIssue(
                    "INVALID_CUSTOM_OPERATOR",
                    "Custom criterion field cannot be empty.",
                    f"criteria.custom_criteria.{index}.field",
                )
            )
    for doc_index, document in enumerate(criteria.required_documents):
        if document.is_mandatory and not document.name.strip():
            issues.append(
                ValidationIssue(
                    "EMPTY_DOCUMENT_NAME",
                    "Mandatory document name cannot be empty.",
                    f"criteria.required_documents.{doc_index}.name",
                )
            )
        for sub_index, substitute in enumerate(document.accepted_substitutes):
            if not substitute.name.strip():
                issues.append(
                    ValidationIssue(
                        "EMPTY_DOCUMENT_NAME",
                        "Substitute document name cannot be empty.",
                        f"criteria.required_documents.{doc_index}.accepted_substitutes.{sub_index}.name",
                    )
                )
            if not substitute.instructions.strip():
                issues.append(
                    ValidationIssue(
                        "EMPTY_SUBSTITUTE_INSTRUCTIONS",
                        "Substitute instructions cannot be empty.",
                        f"criteria.required_documents.{doc_index}.accepted_substitutes.{sub_index}.instructions",
                    )
                )
    return issues


def validate_rule_payload(payload: dict, known_scheme_ids: set[str]) -> list[ValidationIssue]:
    try:
        criteria = EligibilityCriteriaModel.model_validate(payload)
    except ValidationError as exc:
        return [
            ValidationIssue("RULE_VALIDATION_ERROR", error["msg"], "criteria." + ".".join(str(part) for part in error["loc"]))
            for error in exc.errors()
        ]
    return validate_rule(criteria, known_scheme_ids)

