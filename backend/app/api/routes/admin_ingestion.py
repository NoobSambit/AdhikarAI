from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin_token
from app.db.session import get_db
from app.schemas.ingestion import MySchemeIngestionRequest, MySchemeIngestionResponse
from app.services.ingestion.myscheme import start_myscheme_ingestion

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin_token)])


@router.post("/ingestion/myscheme", response_model=MySchemeIngestionResponse)
async def myscheme(request: MySchemeIngestionRequest, db: AsyncSession = Depends(get_db)) -> MySchemeIngestionResponse:
    return await start_myscheme_ingestion(db, request)

