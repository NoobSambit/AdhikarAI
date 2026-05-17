from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.voice import AsrResponseModel, VoiceTurnRequestModel, VoiceTurnResponseModel, VoiceWsStartMessageModel
from app.translation.providers import get_translation_client
from app.tts.providers import get_tts_client
from app.voice.audio_utils import validate_audio_upload
from app.voice.pipeline import VoicePipeline
from app.voice.providers import get_asr_provider

router = APIRouter()


async def _db_session() -> AsyncSession:
    async for session in get_db():
        return session
    raise RuntimeError("Database session unavailable")


@router.post("/voice/asr", response_model=AsrResponseModel)
async def post_voice_asr(
    organisation_id: UUID = Form(...),
    session_id: str = Form(...),
    language_code: str = Form(...),
    audio: UploadFile = File(...),
    client_duration_ms: int | None = Form(default=None),
) -> AsrResponseModel:
    settings = get_settings()
    audio_bytes = await audio.read()
    validate_audio_upload(audio_bytes, audio.content_type, settings.voice_max_upload_mb)
    return await get_asr_provider().transcribe(audio_bytes, audio.content_type or "audio/webm", language_code)


@router.post("/voice/turn", response_model=VoiceTurnResponseModel)
async def post_voice_turn(
    organisation_id: UUID = Form(...),
    session_id: str = Form(...),
    selected_language_code: str = Form(...),
    audio: UploadFile = File(...),
    client_duration_ms: int | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> VoiceTurnResponseModel:
    settings = get_settings()
    audio_bytes = await audio.read()
    validate_audio_upload(audio_bytes, audio.content_type, settings.voice_max_upload_mb)
    pipeline = VoicePipeline(
        asr_provider=get_asr_provider(),
        translator=get_translation_client(),
        tts=get_tts_client(),
        min_confidence=settings.asr_min_confidence,
    )
    return await pipeline.run_voice_turn(
        VoiceTurnRequestModel(
            organisation_id=organisation_id,
            session_id=session_id,
            selected_language_code=selected_language_code,
            client_duration_ms=client_duration_ms,
        ),
        audio_bytes,
        audio.content_type or "audio/webm",
        db,
    )


@router.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket, db: AsyncSession = Depends(_db_session)) -> None:
    await websocket.accept()
    start: VoiceWsStartMessageModel | None = None
    chunks: list[bytes] = []
    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"] is not None:
                if start is None:
                    await websocket.send_json({"type": "error", "content": "Start recording first, or type your message.", "payload": {"code": "VOICE_START_REQUIRED"}})
                    continue
                chunks.append(message["bytes"])
                continue
            raw = message.get("text")
            if raw is None:
                continue
            try:
                import json

                payload = json.loads(raw)
            except ValueError:
                await websocket.send_json({"type": "error", "content": "Voice message format is not valid. You can type your message.", "payload": {"code": "INVALID_JSON"}})
                await websocket.close(code=4400)
                return
            if payload.get("type") == "start":
                try:
                    start = VoiceWsStartMessageModel.model_validate(payload)
                except ValidationError:
                    await websocket.send_json({"type": "error", "content": "Voice message format is not valid. You can type your message.", "payload": {"code": "INVALID_JSON"}})
                    await websocket.close(code=4400)
                    return
                chunks = []
                await websocket.send_json({"type": "partial_status", "stage": "asr", "content": "Listening..."})
            elif payload.get("type") == "end":
                if start is None:
                    await websocket.send_json({"type": "error", "content": "Start recording first, or type your message.", "payload": {"code": "VOICE_START_REQUIRED"}})
                    continue
                audio = b"".join(chunks)
                settings = get_settings()
                validate_audio_upload(audio, start.mime_type, settings.voice_max_upload_mb)
                pipeline = VoicePipeline(get_asr_provider(), get_translation_client(), get_tts_client(), min_confidence=settings.asr_min_confidence)
                response = await pipeline.run_voice_turn(
                    VoiceTurnRequestModel(
                        organisation_id=start.organisation_id,
                        session_id=start.session_id,
                        selected_language_code=start.selected_language_code,
                    ),
                    audio,
                    start.mime_type,
                    db,
                )
                await websocket.send_json(response.model_dump(mode="json"))
                start = None
                chunks = []
            else:
                await websocket.send_json({"type": "error", "content": "Voice message format is not valid. You can type your message.", "payload": {"code": "INVALID_JSON"}})
    except WebSocketDisconnect:
        return
