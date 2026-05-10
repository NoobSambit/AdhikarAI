from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin_token
from app.db.session import get_db
from app.schemas.scheme import ArchiveSchemeRequest, CreateSchemeRequest, PublishSchemeRequest, UpdateSchemeRequest
from app.services.schemes import archive_scheme, create_scheme, publish_scheme, update_scheme

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin_token)])


@router.post("/schemes", status_code=201)
async def create(request: CreateSchemeRequest, db: AsyncSession = Depends(get_db)):
    return await create_scheme(db, request)


@router.patch("/schemes/{scheme_id}")
async def patch(scheme_id: str, request: UpdateSchemeRequest, db: AsyncSession = Depends(get_db)):
    return await update_scheme(db, scheme_id, request)


@router.post("/schemes/{scheme_id}/publish")
async def publish(scheme_id: str, request: PublishSchemeRequest, db: AsyncSession = Depends(get_db)):
    return await publish_scheme(db, request.organisation_id, scheme_id)


@router.post("/schemes/{scheme_id}/archive")
async def archive(scheme_id: str, request: ArchiveSchemeRequest, db: AsyncSession = Depends(get_db)):
    return await archive_scheme(db, request.organisation_id, scheme_id, request.reason)

