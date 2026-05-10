import re

from app.schemas.document_check import DocumentCheckResponse, MissingDocumentModel
from app.schemas.scheme import EligibilityCriteriaModel, RequiredDocumentModel
from app.services.documents.guidance import original_document_instructions

ALIASES = {
    "aadhaar": {"aadhaar", "aadhar", "aadhaar card", "aadhar card"},
    "bank passbook": {"bank passbook", "passbook", "bank statement", "account statement"},
    "ration card": {"ration card", "pds card", "bpl card"},
}


def normalize_document_name(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip().lower())
    for canonical, aliases in ALIASES.items():
        if cleaned in aliases:
            return canonical
    return cleaned


def _matches(required_name: str, available: list[str]) -> str | None:
    required = normalize_document_name(required_name)
    for item in available:
        if normalize_document_name(item) == required:
            return item
    return None


def _exact_match(required_name: str, available: list[str]) -> str | None:
    required = required_name.strip().lower()
    for item in available:
        if item.strip().lower() == required:
            return item
    return None


def _substitute_match(document: RequiredDocumentModel, available: list[str]) -> tuple[dict, str] | None:
    for substitute in document.accepted_substitutes:
        matched = _matches(substitute.name, available)
        if matched:
            return substitute.model_dump(mode="json"), matched
    return None


def check_document_sufficiency(criteria: EligibilityCriteriaModel, documents_available: list[str]) -> DocumentCheckResponse:
    available = [item for item in documents_available if item.strip()]
    missing: list[MissingDocumentModel] = []
    substitutes_available: list[dict] = []
    matched_documents: list[str] = []

    for document in criteria.required_documents:
        if not document.is_mandatory:
            continue
        direct_match = _exact_match(document.name, available)
        if direct_match:
            matched_documents.append(direct_match)
            continue
        substitute = _substitute_match(document, available)
        if substitute:
            substitute_payload, matched = substitute
            matched_documents.append(matched)
            substitutes_available.append({"for_document": document.name, "substitute": substitute_payload["name"]})
            continue
        direct_alias_match = _matches(document.name, available)
        if direct_alias_match:
            matched_documents.append(direct_alias_match)
            continue
        missing.append(
            MissingDocumentModel(
                name=document.name,
                accepted_substitutes=[item.model_dump(mode="json") for item in document.accepted_substitutes],
                original_document_instructions=original_document_instructions(document.name),
            )
        )

    return DocumentCheckResponse(
        is_sufficient=not missing,
        missing=missing,
        substitutes_available=substitutes_available,
        matched_documents=matched_documents,
    )
