from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.translation import TranslateRequestModel, TranslateResponseModel
from app.translation.providers import get_translation_client

router = APIRouter()


@router.post("/translate", response_model=TranslateResponseModel)
async def post_translate(request: TranslateRequestModel, db: AsyncSession = Depends(get_db)) -> TranslateResponseModel:
    return await get_translation_client().translate(request, db=db)
