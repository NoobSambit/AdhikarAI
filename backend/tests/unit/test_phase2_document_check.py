from app.services.documents.document_matcher import check_document_sufficiency
from app.schemas.scheme import DocumentSubstituteModel, EligibilityCriteriaModel, RequiredDocumentModel


def test_document_check_accepts_alias():
    criteria = EligibilityCriteriaModel(
        required_documents=[RequiredDocumentModel(name="Aadhaar", is_mandatory=True)]
    )

    result = check_document_sufficiency(criteria, ["Aadhar card"])

    assert result.is_sufficient is True
    assert result.matched_documents == ["Aadhar card"]


def test_document_check_accepts_substitute():
    criteria = EligibilityCriteriaModel(
        required_documents=[
            RequiredDocumentModel(
                name="Bank passbook",
                is_mandatory=True,
                accepted_substitutes=[
                    DocumentSubstituteModel(
                        name="Bank statement",
                        instructions="Use a recent bank statement.",
                        estimated_cost_inr=0,
                        estimated_time_days=1,
                        issuing_authority="Bank",
                    )
                ],
            )
        ]
    )

    result = check_document_sufficiency(criteria, ["bank statement"])

    assert result.is_sufficient is True
    assert result.substitutes_available[0]["substitute"] == "Bank statement"


def test_document_check_missing_no_substitute():
    criteria = EligibilityCriteriaModel(
        required_documents=[RequiredDocumentModel(name="Income certificate", is_mandatory=True)]
    )

    result = check_document_sufficiency(criteria, ["Aadhaar"])

    assert result.is_sufficient is False
    assert result.missing[0].name == "Income certificate"
    assert "income certificate" in result.missing[0].original_document_instructions.lower()
