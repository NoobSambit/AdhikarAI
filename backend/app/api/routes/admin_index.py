from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin_token
from app.db.session import get_db
from app.schemas.admin import IndexRebuildRequest, IndexRebuildResponse
from app.services.search.faiss_index import rebuild_faiss_index

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin_token)])


@router.post("/index/rebuild", response_model=IndexRebuildResponse)
async def rebuild(request: IndexRebuildRequest, db: AsyncSession = Depends(get_db)) -> IndexRebuildResponse:
    result = await rebuild_faiss_index(db, request.organisation_id, request.index_name)
    return IndexRebuildResponse(**result.__dict__)

