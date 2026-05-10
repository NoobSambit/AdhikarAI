from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.document_check import DocumentCheckRequest, DocumentCheckResponse
from app.services.documents.service import check_documents

router = APIRouter()


@router.post("/schemes/{scheme_id}/document-check", response_model=DocumentCheckResponse)
async def document_check_route(scheme_id: str, request: DocumentCheckRequest, db: AsyncSession = Depends(get_db)) -> DocumentCheckResponse:
    return await check_documents(scheme_id, request, db)
