from app.schemas.scheme import DocumentSubstituteModel, EligibilityCriteriaModel, RequiredDocumentModel
from app.services.eligibility.validation import validate_rule


def test_rule_validation_rejects_min_age_gt_max_age():
    issues = validate_rule(EligibilityCriteriaModel(min_age=60, max_age=18), set())
    assert issues[0].code == "RULE_CONTRADICTION"
    assert issues[0].field == "criteria.min_age"


def test_required_document_substitute_validation():
    criteria = EligibilityCriteriaModel(
        required_documents=[
            RequiredDocumentModel(
                name="Aadhaar",
                is_mandatory=True,
                accepted_substitutes=[
                    DocumentSubstituteModel(
                        name="Slip",
                        instructions="",
                        estimated_cost_inr=0,
                        estimated_time_days=1,
                        issuing_authority="UIDAI",
                    )
                ],
            )
        ]
    )
    issues = validate_rule(criteria, set())
    assert any(issue.code == "EMPTY_SUBSTITUTE_INSTRUCTIONS" for issue in issues)


def test_validation_rejects_broken_exclusion_reference_and_state_code():
    criteria = EligibilityCriteriaModel(exclusion_scheme_ids=["pmay_g"], state_codes=["BR"])
    codes = {issue.code for issue in validate_rule(criteria, set())}
    assert "BROKEN_EXCLUSION_REFERENCE" in codes
    assert "INVALID_STATE_CODE" in codes

