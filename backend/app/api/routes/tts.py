from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.session import get_db
from app.schemas.tts import TtsRequestModel, TtsResponseModel
from app.tts.providers import get_tts_client

router = APIRouter()


@router.post("/tts", response_model=TtsResponseModel)
async def post_tts(request: TtsRequestModel, db: AsyncSession = Depends(get_db)) -> TtsResponseModel:
    return await get_tts_client().synthesize_to_url(request, db=db)


@router.get("/voice/tts/audio/{cache_key:path}")
async def get_tts_audio(cache_key: str) -> Response:
    audio = await get_tts_client().get_audio(cache_key)
    if not audio:
        raise ApiError(404, "TTS_AUDIO_NOT_FOUND", "Voice audio expired. You can replay after trying again.", "cache_key")
    return Response(content=audio["audio"], media_type=audio["mime_type"])
