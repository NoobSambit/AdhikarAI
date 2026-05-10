from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import DocumentCheckEvent, Profile
from app.schemas.document_check import DocumentCheckRequest, DocumentCheckResponse
from app.schemas.scheme import EligibilityCriteriaModel
from app.services.documents.document_matcher import check_document_sufficiency
from app.services.schemes import latest_rule


async def check_documents(scheme_id: str, request: DocumentCheckRequest, db: AsyncSession) -> DocumentCheckResponse:
    if request.profile_id:
        profile = await db.get(Profile, request.profile_id)
        if profile is None or profile.organisation_id != request.organisation_id:
            raise ApiError(404, "PROFILE_NOT_FOUND", "Profile was not found.", "profile_id")
    rule = await latest_rule(db, request.organisation_id, scheme_id)
    result = check_document_sufficiency(EligibilityCriteriaModel.model_validate(rule.criteria), request.documents_available)
    db.add(
        DocumentCheckEvent(
            organisation_id=request.organisation_id,
            profile_id=request.profile_id,
            scheme_id=scheme_id,
            documents_available=request.documents_available,
            result=result.model_dump(mode="json"),
        )
    )
    await db.commit()
    return result
