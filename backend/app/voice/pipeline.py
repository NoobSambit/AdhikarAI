from collections.abc import Awaitable, Callable
import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ConversationSession, UserLanguagePreference, VoiceTurn
from app.schemas.agent import ChatInputModel, ChatOutputModel
from app.schemas.translation import TranslateRequestModel
from app.schemas.tts import TtsRequestModel
from app.schemas.voice import VoiceTurnRequestModel, VoiceTurnResponseModel
from app.services.sessions.session_service import handle_chat_turn
from app.voice.localized_messages import localized_message
from app.voice.providers.base import ASRProvider

ChatHandler = Callable[[ChatInputModel, AsyncSession | None], Awaitable[ChatOutputModel]]


class VoicePipeline:
    def __init__(
        self,
        asr_provider: ASRProvider,
        translator,
        tts,
        chat_handler: ChatHandler | None = None,
        min_confidence: float = 0.70,
    ) -> None:
        self.asr_provider = asr_provider
        self.translator = translator
        self.tts = tts
        self.chat_handler = chat_handler or handle_chat_turn
        self.min_confidence = min_confidence

    async def run_voice_turn(
        self,
        request: VoiceTurnRequestModel,
        audio: bytes,
        mime_type: str,
        db: AsyncSession | None,
    ) -> VoiceTurnResponseModel:
        total_started = time.monotonic()
        timings: dict[str, int] = {}
        session_row = await _session_row(db, request.organisation_id, request.session_id)
        asr_started = time.monotonic()
        asr = await self.asr_provider.transcribe(audio, mime_type, request.selected_language_code)
        timings["asr_ms"] = _elapsed_ms(asr_started)
        selected_language = request.selected_language_code or asr.detected_language_code

        if asr.confidence < self.min_confidence:
            timings["total_ms"] = _elapsed_ms(total_started)
            await _persist_voice_turn(
                db,
                request,
                session_row,
                mime_type,
                len(audio),
                asr.transcript,
                asr.transcript,
                asr.detected_language_code,
                asr.provider,
                asr.confidence,
                "low_confidence",
                timings,
            )
            return VoiceTurnResponseModel(
                type="low_confidence",
                transcript=asr.transcript,
                detected_language_code=asr.detected_language_code,
                selected_language_code=selected_language,
                confidence=asr.confidence,
                content=localized_message(selected_language, "low_confidence"),
                profile_completeness=session_row.profile_completeness if session_row else 0,
                timings=timings,
            )

        english_text = asr.transcript
        if selected_language != "en":
            translate_started = time.monotonic()
            translated = await self.translator.translate(
                TranslateRequestModel(text=asr.transcript, source_lang=selected_language, target_lang="en"),
                db=db,
                organisation_id=request.organisation_id,
                conversation_session_id=session_row.id if session_row else None,
            )
            timings["translation_to_en_ms"] = _elapsed_ms(translate_started)
            english_text = translated.translated_text

        agent_started = time.monotonic()
        agent_response = await self.chat_handler(
            ChatInputModel(
                organisation_id=request.organisation_id,
                session_id=request.session_id,
                message=english_text,
                language_code=selected_language,
            ),
            db,
        )
        timings["agent_ms"] = _elapsed_ms(agent_started)

        localized_content = agent_response.content
        if selected_language != "en":
            translate_started = time.monotonic()
            translated = await self.translator.translate(
                TranslateRequestModel(text=agent_response.content, source_lang="en", target_lang=selected_language),
                db=db,
                organisation_id=request.organisation_id,
                conversation_session_id=session_row.id if session_row else None,
            )
            timings["translation_from_en_ms"] = _elapsed_ms(translate_started)
            localized_content = translated.translated_text

        tts_started = time.monotonic()
        tts_response = await self.tts.synthesize_to_url(
            TtsRequestModel(text=localized_content, language_code=selected_language),
            db=db,
            organisation_id=request.organisation_id,
            conversation_session_id=session_row.id if session_row else None,
        )
        timings["tts_ms"] = _elapsed_ms(tts_started)
        timings["total_ms"] = _elapsed_ms(total_started)

        await _persist_language_preference(db, request, session_row, selected_language)
        await _persist_voice_turn(
            db,
            request,
            session_row,
            mime_type,
            len(audio),
            asr.transcript,
            english_text,
            asr.detected_language_code,
            asr.provider,
            asr.confidence,
            "agent_completed",
            timings,
        )
        if db is not None:
            await db.commit()

        return VoiceTurnResponseModel(
            type=agent_response.type,
            transcript=asr.transcript,
            detected_language_code=asr.detected_language_code,
            selected_language_code=selected_language,
            confidence=asr.confidence,
            content=localized_content,
            profile_completeness=agent_response.profile_completeness,
            audio_url=tts_response.audio_url,
            timings=timings,
            payload=agent_response.payload,
        )


async def _session_row(db: AsyncSession | None, organisation_id: UUID, session_id: str) -> ConversationSession | None:
    if db is None:
        return None
    return await db.scalar(
        select(ConversationSession).where(
            ConversationSession.organisation_id == organisation_id,
            ConversationSession.session_id == session_id,
        )
    )


async def _persist_voice_turn(
    db: AsyncSession | None,
    request: VoiceTurnRequestModel,
    session_row: ConversationSession | None,
    mime_type: str,
    size_bytes: int,
    transcript: str | None,
    normalized_transcript: str | None,
    detected_language_code: str | None,
    provider: str,
    confidence: float | None,
    status: str,
    timings: dict[str, int],
) -> None:
    if db is None or session_row is None:
        return
    db.add(
        VoiceTurn(
            organisation_id=request.organisation_id,
            conversation_session_id=session_row.id,
            profile_id=session_row.active_profile_id,
            provider=provider,
            input_audio_mime_type=mime_type,
            input_audio_duration_ms=request.client_duration_ms,
            input_audio_size_bytes=size_bytes,
            transcript=transcript,
            normalized_transcript=normalized_transcript,
            detected_language_code=detected_language_code,
            selected_language_code=request.selected_language_code,
            asr_confidence=confidence,
            status=status,
            timings=timings,
        )
    )
    if status == "low_confidence":
        await db.commit()


async def _persist_language_preference(
    db: AsyncSession | None,
    request: VoiceTurnRequestModel,
    session_row: ConversationSession | None,
    language_code: str,
) -> None:
    if db is None:
        return
    profile_id = session_row.active_profile_id if session_row else None
    existing = None
    if profile_id is not None:
        existing = await db.scalar(
            select(UserLanguagePreference).where(
                UserLanguagePreference.organisation_id == request.organisation_id,
                UserLanguagePreference.profile_id == profile_id,
            )
        )
    if existing:
        existing.language_code = language_code
        existing.source = "selector"
        existing.session_id = request.session_id
        return
    db.add(
        UserLanguagePreference(
            organisation_id=request.organisation_id,
            profile_id=profile_id,
            session_id=request.session_id,
            language_code=language_code,
            source="selector",
        )
    )


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
