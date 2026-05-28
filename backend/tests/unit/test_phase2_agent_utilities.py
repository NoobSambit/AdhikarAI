import pytest

from app.agent.graph import build_agent_graph
from app.agent.completeness import compute_profile_completeness
from app.agent.extraction import (
    DeterministicFactExtractor,
    ExtractedFact,
    extract_facts,
    merge_confirmed_pending_fact,
    prepare_pending_confirmation,
)
from app.agent.life_events import detect_life_event
from app.agent.question_selection import select_next_question
from app.schemas.agent import AgentStateModel
from app.schemas.scheme import EligibilityCriteriaModel


def test_select_question_skips_asked_field():
    state = AgentStateModel(
        session_id="sess_test",
        organisation_id="00000000-0000-0000-0000-000000000001",
        active_member_id="self",
        asked_fields=["self:age"],
    )
    rules = [EligibilityCriteriaModel(min_age=18, max_annual_income=120000)]

    question = select_next_question(state, rules)

    assert question.field != "age"
    assert question.field == "annual_income"
    assert question.asked_key == "self:annual_income"


def test_one_question_per_turn_text():
    state = AgentStateModel(
        session_id="sess_test",
        organisation_id="00000000-0000-0000-0000-000000000001",
        active_member_id="self",
    )

    question = select_next_question(state, [EligibilityCriteriaModel(min_age=18, max_annual_income=120000)])

    assert question.text.count("?") == 1


def test_completeness_score_weighted():
    profile = {"state_code": "IN-BR", "age": 34, "gender": "female"}
    rules = [EligibilityCriteriaModel(min_age=18, gender=["female"], max_annual_income=120000)]

    assert compute_profile_completeness(profile, rules) == 57


def test_profile_extraction_confidence_thresholds():
    extractor = DeterministicFactExtractor()

    extracted = extractor.extract("I am 62 and from Uttar Pradesh. I do farming.")

    values = {fact.field: fact for fact in extracted.facts}
    assert values["age"].confidence >= 0.75
    assert values["state_code"].value == "IN-UP"
    assert values["occupation_type"].value == "farmer"


def test_structured_profile_extraction_maps_guest_profile_facts():
    extractor = DeterministicFactExtractor()

    extracted = extractor.extract(
        "profile_facts: state_code=IN-BR; age=35; gender=female; "
        "occupation_type=farmer; annual_income=72000; land_holding_acres=1.5; "
        "has_bank_account=true; has_land_record=false; ration_card_type=bpl"
    )

    values = {fact.field: fact.value for fact in extracted.facts}
    assert values["state_code"] == "IN-BR"
    assert values["age"] == 35
    assert values["gender"] == "female"
    assert values["occupation_type"] == "farmer"
    assert values["annual_income"] == 72000
    assert values["land_holding_acres"] == 1.5
    assert values["custom_attributes.has_bank_account"] is True
    assert values["custom_attributes.has_land_record"] is False
    assert values["custom_attributes.ration_card_type"] == "bpl"
    assert values["custom_attributes.is_bpl"] is True
    assert values["custom_attributes.poor_household"] is True


def test_structured_profile_extraction_still_blocks_sensitive_values():
    extractor = DeterministicFactExtractor()

    extracted = extractor.extract("profile_facts: state_code=IN-BR; bank_account_number=123456789; otp=123456")

    assert extracted.facts == []


def test_life_event_marriage():
    event = detect_life_event("I got married last week.")

    assert event is not None
    assert event.event_type == "marriage"
    assert event.profile_patch == {"marital_status": "married"}


def test_life_event_child_birth():
    event = detect_life_event("I had a baby girl last month.")

    assert event is not None
    assert event.event_type == "child_birth"
    assert event.member_patch["relationship_to_primary"] == "child"
    assert event.member_patch["gender"] == "female"


@pytest.mark.asyncio
async def test_llm_extraction_returns_facts_beyond_regex(monkeypatch):
    async def fake_json(*_args, **_kwargs):
        return {"facts": [{"field": "custom_attributes.is_pregnant", "value": True, "confidence": 0.91}], "active_member_reference": "self"}

    monkeypatch.setattr("app.agent.extraction._call_llm_json", fake_json)

    extracted = await extract_facts("My delivery is expected soon")

    assert extracted.facts[0].field == "custom_attributes.is_pregnant"
    assert extracted.facts[0].value is True


@pytest.mark.asyncio
async def test_llm_json_repair_retry_succeeds(monkeypatch):
    calls = {"count": 0}

    async def fake_json(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("bad json")
        return {"facts": [{"field": "age", "value": 24, "confidence": 0.88}], "active_member_reference": "self"}

    monkeypatch.setattr("app.agent.extraction._call_llm_json", fake_json)

    extracted = await extract_facts("age twenty four")

    assert calls["count"] == 2
    assert extracted.facts[0].field == "age"


@pytest.mark.asyncio
async def test_sensitive_llm_fields_are_dropped(monkeypatch):
    async def fake_json(*_args, **_kwargs):
        return {
            "facts": [
                {"field": "aadhaar_number", "value": "123412341234", "confidence": 0.95},
                {"field": "age", "value": 29, "confidence": 0.95},
            ]
        }

    monkeypatch.setattr("app.agent.extraction._call_llm_json", fake_json)

    extracted = await extract_facts("my aadhaar is 123412341234 and age is 29")

    assert [fact.field for fact in extracted.facts] == ["age"]


def test_medium_confidence_fact_waits_for_confirmation():
    profile = {}
    state = AgentStateModel(session_id="sess", organisation_id="00000000-0000-0000-0000-000000000001")
    fact = ExtractedFact("age", 42, 0.61)

    pending = prepare_pending_confirmation(state, [fact], profile)

    assert pending is not None
    assert state.pending_confirmation["fact"]["field"] == "age"
    assert "age" not in profile


def test_confirmation_yes_merges_and_no_discards():
    yes_state = AgentStateModel(
        session_id="sess",
        organisation_id="00000000-0000-0000-0000-000000000001",
        pending_confirmation={"fact": {"field": "age", "value": 42, "confidence": 0.61, "member_reference": "self"}},
    )
    profile = {}

    assert merge_confirmed_pending_fact(yes_state, "yes", profile) is True
    assert profile["age"] == 42
    assert yes_state.pending_confirmation is None

    no_state = AgentStateModel(
        session_id="sess",
        organisation_id="00000000-0000-0000-0000-000000000001",
        pending_confirmation={"fact": {"field": "age", "value": 42, "confidence": 0.61, "member_reference": "self"}},
    )
    profile = {}

    assert merge_confirmed_pending_fact(no_state, "no", profile) is False
    assert profile == {}
    assert no_state.pending_confirmation is None


@pytest.mark.asyncio
async def test_graph_executes_real_node_order():
    order = []

    async def node(name):
        async def _inner(state):
            order.append(name)
            return state

        return _inner

    graph = build_agent_graph(
        {
            "load_session": await node("load_session"),
            "extract_profile_facts": await node("extract_profile_facts"),
            "detect_life_event": await node("detect_life_event"),
            "process_pending_confirmation": await node("process_pending_confirmation"),
            "retrieve_semantic_candidates": await node("retrieve_semantic_candidates"),
            "merge_profile_update": await node("merge_profile_update"),
            "compute_profile_completeness": await node("compute_profile_completeness"),
            "run_eligibility_match": await node("run_eligibility_match"),
            "choose_response": await node("choose_response"),
            "persist_session": await node("persist_session"),
        }
    )

    await graph.ainvoke({"profile_completeness": 0})

    assert order == [
        "load_session",
        "extract_profile_facts",
        "detect_life_event",
        "process_pending_confirmation",
        "retrieve_semantic_candidates",
        "merge_profile_update",
        "compute_profile_completeness",
        "run_eligibility_match",
        "choose_response",
        "persist_session",
    ]
