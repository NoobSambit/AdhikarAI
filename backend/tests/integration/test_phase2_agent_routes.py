from types import SimpleNamespace
from uuid import UUID

import pytest

from app.api.routes.agent_sessions import create_agent_session, get_agent_session, post_agent_message
from app.schemas.agent import ChatInputModel, ChatOutputModel, CreateSessionRequest, CreateSessionResponse


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_session_create_resume_and_rest_fallback(monkeypatch):
    calls = {"created": 0, "message": 0}

    async def fake_get_or_create(request, db):
        calls["created"] += 1
        return CreateSessionResponse(
            session_id=request.session_id or "sess_test",
            profile_id=UUID("00000000-0000-0000-0000-000000000002"),
            household_id=UUID("00000000-0000-0000-0000-000000000003"),
            greeting="Namaste. Tell me about your situation, and I will check schemes for you.",
            profile_completeness=0,
        )

    async def fake_handle_turn(input_message, db):
        calls["message"] += 1
        return ChatOutputModel(
            type="question",
            content="How old are you?",
            profile_completeness=15,
            session_id=input_message.session_id,
            payload={"asked_field": "self:age"},
        )

    async def fake_get_state(session_id, organisation_id, db):
        return {"session_id": session_id, "organisation_id": str(organisation_id), "profile_completeness": 15}

    monkeypatch.setattr("app.api.routes.agent_sessions.get_or_create_session", fake_get_or_create)
    monkeypatch.setattr("app.api.routes.agent_sessions.handle_chat_turn", fake_handle_turn)
    monkeypatch.setattr("app.api.routes.agent_sessions.get_session_state", fake_get_state)

    created = await create_agent_session(CreateSessionRequest(organisation_id=ORG_ID), db=None)
    message = await post_agent_message(
        ChatInputModel(session_id=created.session_id, organisation_id=ORG_ID, message="I am a farmer."),
        db=None,
    )
    state = await get_agent_session(created.session_id, ORG_ID, db=None)

    assert calls == {"created": 1, "message": 1}
    assert message.content.count("?") == 1
    assert state["profile_completeness"] == 15
