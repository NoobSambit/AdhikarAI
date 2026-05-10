from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import ListResponse
from app.services.schemes import get_scheme_detail, list_schemes
from app.services.search.faiss_index import search_schemes

router = APIRouter()


@router.get("/schemes", response_model=ListResponse)
async def schemes(
    organisation_id: str,
    status: str | None = None,
    state_code: str | None = None,
    category_code: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ListResponse:
    items, total = await list_schemes(db, organisation_id, status, state_code, category_code, limit, offset)
    return ListResponse(items=[{"id": item.id, "name": item.name, "status": item.status, "is_active": item.is_active} for item in items], limit=limit, offset=offset, total=total)


@router.get("/schemes/search")
async def search(organisation_id: str, q: str, limit: int = Query(default=10, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    results = await search_schemes(db, organisation_id, q, limit)
    return {"items": [result.__dict__ for result in results]}


@router.get("/schemes/{scheme_id}")
async def scheme_detail(scheme_id: str, organisation_id: str, db: AsyncSession = Depends(get_db)):
    return await get_scheme_detail(db, organisation_id, scheme_id)
