from uuid import UUID

import pytest
from starlette.datastructures import UploadFile

from app.api.routes.voice import post_voice_asr, post_voice_turn
from app.schemas.agent import ChatOutputModel
from app.schemas.voice import AsrResponseModel


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


class FakeUpload:
    filename = "voice.webm"
    content_type = "audio/webm"

    async def read(self) -> bytes:
        return b"audio"


@pytest.mark.asyncio
async def test_post_voice_asr_with_mocked_provider(monkeypatch):
    class FakeProvider:
        async def transcribe(self, audio, mime_type, language_hint):
            return AsrResponseModel(
                transcript="I am a farmer from Bihar.",
                detected_language_code="en",
                confidence=0.9,
                duration_ms=900,
                provider="groq",
            )

    monkeypatch.setattr("app.api.routes.voice.get_asr_provider", lambda: FakeProvider())

    response = await post_voice_asr(
        organisation_id=ORG_ID,
        session_id="sess_test",
        language_code="en",
        audio=FakeUpload(),
        client_duration_ms=None,
    )

    assert response.transcript == "I am a farmer from Bihar."
    assert response.provider == "groq"


@pytest.mark.asyncio
async def test_post_voice_turn_rest_fallback_with_mocked_pipeline(monkeypatch):
    async def fake_agent(input_message, db):
        return ChatOutputModel(
            type="question",
            content="How old are you?",
            profile_completeness=20,
            session_id=input_message.session_id,
            payload={"asked_field": "self:age"},
        )

    class FakeProvider:
        async def transcribe(self, audio, mime_type, language_hint):
            return AsrResponseModel(
                transcript="I am a farmer from Bihar.",
                detected_language_code="en",
                confidence=0.9,
                duration_ms=900,
                provider="groq",
            )

    class FakeTTS:
        async def synthesize_to_url(self, request, db=None, organisation_id=None, conversation_session_id=None):
            return type(
                "TtsResponse",
                (),
                {
                    "audio_url": "/voice/tts/audio/test",
                    "audio_mime_type": "audio/wav",
                    "provider": "local_indictts",
                    "cached": False,
                },
            )()

    monkeypatch.setattr("app.api.routes.voice.get_asr_provider", lambda: FakeProvider())
    monkeypatch.setattr("app.api.routes.voice.get_tts_client", lambda: FakeTTS())
    monkeypatch.setattr("app.voice.pipeline.handle_chat_turn", fake_agent)

    response = await post_voice_turn(
        organisation_id=ORG_ID,
        session_id="sess_test",
        selected_language_code="en",
        audio=FakeUpload(),
        client_duration_ms=None,
        db=None,
    )

    assert response.type == "question"
    assert response.transcript == "I am a farmer from Bihar."
    assert response.audio_url
