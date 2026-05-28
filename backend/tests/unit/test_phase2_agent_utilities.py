from app.agent.completeness import compute_profile_completeness
from app.agent.extraction import DeterministicFactExtractor
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
