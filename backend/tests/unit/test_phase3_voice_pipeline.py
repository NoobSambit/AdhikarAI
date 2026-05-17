from types import SimpleNamespace
from uuid import UUID

import pytest

from app.schemas.agent import ChatOutputModel
from app.schemas.voice import AsrResponseModel, VoiceTurnRequestModel
from app.voice.pipeline import VoicePipeline


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


class FakeASRProvider:
    def __init__(self, confidence: float, detected_language_code: str = "hi") -> None:
        self.confidence = confidence
        self.detected_language_code = detected_language_code

    async def transcribe(self, audio: bytes, mime_type: str, language_hint: str | None) -> AsrResponseModel:
        return AsrResponseModel(
            transcript="main bihar se kisan hoon",
            detected_language_code=self.detected_language_code,
            confidence=self.confidence,
            duration_ms=1000,
            provider="groq",
        )


class PassthroughTranslator:
    calls: list[tuple[str, str, str]]

    def __init__(self) -> None:
        self.calls = []

    async def translate(self, request, db=None, organisation_id=None, conversation_session_id=None):
        self.calls.append((request.text, request.source_lang, request.target_lang))
        return SimpleNamespace(
            translated_text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider="local_indictrans2",
            cached=False,
        )


class FakeTTS:
    async def synthesize_to_url(self, request, db=None, organisation_id=None, conversation_session_id=None):
        return SimpleNamespace(
            audio_url="/voice/tts/audio/test",
            audio_mime_type="audio/wav",
            provider="local_indictts",
            cached=False,
        )


@pytest.mark.asyncio
async def test_low_confidence_blocks_agent_call():
    calls = {"agent": 0}

    async def fake_agent(input_message, db):
        calls["agent"] += 1
        return ChatOutputModel(
            type="question",
            content="How old are you?",
            profile_completeness=10,
            session_id=input_message.session_id,
        )

    pipeline = VoicePipeline(
        asr_provider=FakeASRProvider(0.69),
        translator=PassthroughTranslator(),
        tts=FakeTTS(),
        chat_handler=fake_agent,
        min_confidence=0.70,
    )

    response = await pipeline.run_voice_turn(
        VoiceTurnRequestModel(organisation_id=ORG_ID, session_id="sess_test", selected_language_code="hi"),
        audio=b"audio",
        mime_type="audio/webm",
        db=None,
    )

    assert response.type == "low_confidence"
    assert response.content
    assert calls["agent"] == 0


@pytest.mark.asyncio
async def test_language_override_wins_over_asr_detected_language():
    async def fake_agent(input_message, db):
        return ChatOutputModel(
            type="question",
            content="How old are you?",
            profile_completeness=10,
            session_id=input_message.session_id,
        )

    pipeline = VoicePipeline(
        asr_provider=FakeASRProvider(0.91, detected_language_code="hi"),
        translator=PassthroughTranslator(),
        tts=FakeTTS(),
        chat_handler=fake_agent,
        min_confidence=0.70,
    )

    response = await pipeline.run_voice_turn(
        VoiceTurnRequestModel(organisation_id=ORG_ID, session_id="sess_test", selected_language_code="mr"),
        audio=b"audio",
        mime_type="audio/webm",
        db=None,
    )

    assert response.selected_language_code == "mr"
    assert response.detected_language_code == "hi"
