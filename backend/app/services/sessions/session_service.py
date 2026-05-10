from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.completeness import compute_profile_completeness
from app.agent.extraction import DeterministicFactExtractor, ExtractedFact
from app.agent.life_events import detect_life_event
from app.agent.question_selection import select_next_question
from app.agent.result_formatter import format_match_result
from app.core.config import get_settings
from app.core.errors import ApiError, new_request_id
from app.db.models import ConversationMessage, ConversationSession, Household, Profile, ProfileEvent, ZeroMatchEvent
from app.schemas.agent import (
    AgentStateModel,
    ChatInputModel,
    ChatOutputModel,
    CreateSessionRequest,
    CreateSessionResponse,
    HouseholdMemberProfileModel,
)
from app.schemas.profile import MatchProfileRequest, UserProfileInputModel
from app.services.eligibility.matcher import match_profile
from app.services.schemes import active_scheme_rules, ensure_organisation
from app.services.sessions.redis_store import RedisSessionStore, session_redis_key

SESSION_TTL_SECONDS = 2_592_000


def _store() -> RedisSessionStore:
    settings = get_settings()
    return RedisSessionStore(settings.redis_url, SESSION_TTL_SECONDS)


def _profile_model(profile: Profile | None) -> HouseholdMemberProfileModel:
    if profile is None:
        return HouseholdMemberProfileModel(id="self")
    return HouseholdMemberProfileModel(
        id=str(profile.id),
        display_name=profile.display_name,
        relationship_to_primary=profile.relationship_to_primary,
        age=profile.age,
        gender=profile.gender,
        caste_category=profile.caste_category,
        annual_income=profile.annual_income,
        land_holding_acres=float(profile.land_holding_acres) if profile.land_holding_acres is not None else None,
        occupation_type=profile.occupation_type,
        marital_status=profile.marital_status,
        state_code=profile.state_code,
        district=profile.district,
        existing_scheme_ids=profile.existing_scheme_ids or [],
        custom_attributes=profile.custom_attributes or {},
        profile_completeness=profile.profile_completeness,
    )


def _profile_input(profile: dict) -> UserProfileInputModel:
    return UserProfileInputModel(
        age=profile.get("age"),
        gender=profile.get("gender"),
        caste_category=profile.get("caste_category"),
        annual_income=profile.get("annual_income"),
        land_holding_acres=profile.get("land_holding_acres"),
        occupation_type=profile.get("occupation_type"),
        marital_status=profile.get("marital_status"),
        state_code=profile.get("state_code"),
        district=profile.get("district"),
        existing_scheme_ids=profile.get("existing_scheme_ids") or [],
        custom_attributes=profile.get("custom_attributes") or {},
    )


async def _session_row(db: AsyncSession, organisation_id: UUID, session_id: str) -> ConversationSession | None:
    return await db.scalar(
        select(ConversationSession).where(
            ConversationSession.organisation_id == organisation_id,
            ConversationSession.session_id == session_id,
        )
    )


async def _resolve_organisation_id(db: AsyncSession, session_id: str, organisation_id: UUID | None) -> UUID:
    if organisation_id is not None:
        return organisation_id
    rows = await db.scalars(select(ConversationSession).where(ConversationSession.session_id == session_id))
    matches = rows.all()
    if not matches:
        raise ApiError(404, "SESSION_NOT_FOUND", "This conversation was not found.", "session_id")
    if len(matches) > 1:
        raise ApiError(422, "ORGANISATION_REQUIRED", "Please include organisation_id for this session.", "organisation_id")
    return matches[0].organisation_id


async def _state_from_db(db: AsyncSession, row: ConversationSession) -> AgentStateModel:
    profile = await db.get(Profile, row.active_profile_id or row.primary_profile_id)
    members = []
    if row.household_id:
        rows = await db.scalars(
            select(Profile).where(Profile.organisation_id == row.organisation_id, Profile.household_id == row.household_id)
        )
        members = [_profile_model(item) for item in rows.all()]
    messages = await db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.organisation_id == row.organisation_id, ConversationMessage.conversation_session_id == row.id)
        .order_by(ConversationMessage.created_at)
    )
    user_profile = _profile_model(profile)
    return AgentStateModel(
        session_id=row.session_id,
        organisation_id=str(row.organisation_id),
        messages=[{"role": item.role, "content": item.content} for item in messages.all()],
        user_profile=user_profile,
        household={"id": str(row.household_id) if row.household_id else None, "members": members},
        active_member_id=str(profile.id) if profile else "self",
        asked_fields=row.asked_fields or [],
        remaining_required_fields=row.remaining_required_fields or [],
        confidence_score=float(row.confidence_score),
        profile_completeness=row.profile_completeness,
        language_code=row.language_code,
    )


async def get_or_create_session(request: CreateSessionRequest, db: AsyncSession) -> CreateSessionResponse:
    await ensure_organisation(db, str(request.organisation_id))
    session_id = request.session_id or f"sess_{uuid4().hex}"
    key = session_redis_key(str(request.organisation_id), session_id)
    row = await _session_row(db, request.organisation_id, session_id)
    now = datetime.now(timezone.utc)

    if row:
        if row.expires_at <= now:
            raise ApiError(410, "SESSION_EXPIRED", "This conversation has expired. Please start again.", "session_id")
        state = await _state_from_db(db, row)
        await _store().write_state(key, state.model_dump(mode="json"))
        profile = await db.get(Profile, row.primary_profile_id)
        name = profile.display_name if profile else None
        greeting = (
            f"Namaste {name}. I remember your profile. Do you want to continue checking schemes for you or someone in your family?"
            if name
            else "Namaste. I remember your previous answers."
        )
        return CreateSessionResponse(
            session_id=session_id,
            profile_id=row.primary_profile_id,
            household_id=row.household_id,
            greeting=greeting,
            profile_completeness=row.profile_completeness,
        )

    household = Household(organisation_id=request.organisation_id)
    db.add(household)
    await db.flush()
    profile = Profile(organisation_id=request.organisation_id, household_id=household.id, relationship_to_primary="self")
    db.add(profile)
    await db.flush()
    row = ConversationSession(
        organisation_id=request.organisation_id,
        session_id=session_id,
        household_id=household.id,
        primary_profile_id=profile.id,
        active_profile_id=profile.id,
        language_code=request.language_code,
        redis_key=key,
        expires_at=now + timedelta(seconds=SESSION_TTL_SECONDS),
    )
    db.add(row)
    await db.commit()
    state = AgentStateModel(
        session_id=session_id,
        organisation_id=str(request.organisation_id),
        user_profile=_profile_model(profile),
        household={"id": str(household.id), "members": [_profile_model(profile)]},
        active_member_id=str(profile.id),
        language_code=request.language_code,
    )
    await _store().write_state(key, state.model_dump(mode="json"))
    return CreateSessionResponse(
        session_id=session_id,
        profile_id=profile.id,
        household_id=household.id,
        greeting="Namaste. Tell me about your situation, and I will check schemes for you.",
        profile_completeness=0,
    )


async def get_session_state(session_id: str, organisation_id: UUID, db: AsyncSession) -> dict:
    key = session_redis_key(str(organisation_id), session_id)
    cached = await _store().read_state(key)
    if cached:
        return cached["state"]
    row = await _session_row(db, organisation_id, session_id)
    if row is None:
        raise ApiError(404, "SESSION_NOT_FOUND", "This conversation was not found.", "session_id")
    if row.expires_at <= datetime.now(timezone.utc):
        raise ApiError(410, "SESSION_EXPIRED", "This conversation has expired. Please start again.", "session_id")
    state = await _state_from_db(db, row)
    await _store().write_state(key, state.model_dump(mode="json"))
    return state.model_dump(mode="json")


def _merge_fact(profile: dict, fact: ExtractedFact) -> bool:
    if fact.confidence < 0.75:
        return False
    if fact.field.startswith("custom_attributes."):
        key = fact.field.split(".", 1)[1]
        profile.setdefault("custom_attributes", {})[key] = fact.value
        return True
    profile[fact.field] = fact.value
    return True


async def _persist_profile(db: AsyncSession, profile_id: UUID, profile_data: dict, organisation_id: UUID, source: str) -> Profile:
    profile = await db.get(Profile, profile_id)
    if profile is None or profile.organisation_id != organisation_id:
        raise ApiError(404, "PROFILE_NOT_FOUND", "Profile was not found.", "profile_id")
    previous = {}
    new_values = {}
    changed = []
    for field in [
        "display_name",
        "age",
        "gender",
        "caste_category",
        "annual_income",
        "land_holding_acres",
        "occupation_type",
        "marital_status",
        "state_code",
        "district",
        "existing_scheme_ids",
        "custom_attributes",
        "profile_completeness",
    ]:
        value = profile_data.get(field)
        if value is not None and getattr(profile, field) != value:
            previous[field] = jsonable_encoder(getattr(profile, field))
            new_values[field] = value
            changed.append(field)
            setattr(profile, field, value)
    if changed:
        db.add(
            ProfileEvent(
                organisation_id=organisation_id,
                profile_id=profile.id,
                event_type="profile_update",
                source=source,
                changed_fields={field: True for field in changed},
                previous_values=previous,
                new_values=new_values,
            )
        )
    await db.flush()
    return profile


async def _run_match(db: AsyncSession, organisation_id: UUID, profile_data: dict) -> dict:
    result = await match_profile(
        MatchProfileRequest(
            organisation_id=str(organisation_id),
            profile=_profile_input(profile_data),
            include_incomplete=True,
            limit=10,
        ),
        db,
        new_request_id(),
    )
    return result.model_dump(mode="json")


async def handle_chat_turn(input_message: ChatInputModel, db: AsyncSession) -> ChatOutputModel:
    organisation_id = await _resolve_organisation_id(db, input_message.session_id, input_message.organisation_id)
    if len(input_message.message) > 2000:
        return ChatOutputModel(
            type="error",
            content="Please send a shorter message.",
            profile_completeness=0,
            session_id=input_message.session_id,
            payload={"code": "MESSAGE_TOO_LONG"},
        )
    state_dict = await get_session_state(input_message.session_id, organisation_id, db)
    state = AgentStateModel.model_validate(state_dict)
    row = await _session_row(db, organisation_id, input_message.session_id)
    if row is None:
        raise ApiError(404, "SESSION_NOT_FOUND", "This conversation was not found.", "session_id")

    state.messages.append({"role": "user", "content": input_message.message})
    db.add(
        ConversationMessage(
            organisation_id=organisation_id,
            conversation_session_id=row.id,
            role="user",
            content=input_message.message,
            language_code=input_message.language_code,
        )
    )
    extracted = DeterministicFactExtractor().extract(input_message.message)
    if extracted.active_member_reference != "self":
        member = await db.scalar(
            select(Profile).where(
                Profile.organisation_id == organisation_id,
                Profile.household_id == row.household_id,
                Profile.relationship_to_primary == extracted.active_member_reference,
            )
        )
        if member is None:
            member = Profile(
                organisation_id=organisation_id,
                household_id=row.household_id,
                display_name=extracted.active_member_reference,
                relationship_to_primary=extracted.active_member_reference,
            )
            db.add(member)
            await db.flush()
        row.active_profile_id = member.id
        state.active_member_id = str(member.id)
        state.user_profile = _profile_model(member)
    profile_data = state.user_profile.model_dump(mode="json")
    life_event = detect_life_event(input_message.message)
    if life_event:
        for field, value in life_event.profile_patch.items():
            profile_data[field] = value
        if life_event.member_patch and row.household_id:
            child = Profile(
                organisation_id=organisation_id,
                household_id=row.household_id,
                display_name=life_event.member_patch.get("relationship_to_primary"),
                relationship_to_primary=life_event.member_patch.get("relationship_to_primary", "child"),
                age=life_event.member_patch.get("age"),
                gender=life_event.member_patch.get("gender"),
            )
            db.add(child)
            await db.flush()
            db.add(
                ProfileEvent(
                    organisation_id=organisation_id,
                    profile_id=child.id,
                    event_type=life_event.event_type,
                    source="conversation",
                    changed_fields={field: True for field in life_event.member_patch},
                    previous_values={},
                    new_values=life_event.member_patch,
                )
            )
    for fact in extracted.facts:
        _merge_fact(profile_data, fact)

    rules = [item.rule for item in await active_scheme_rules(db, str(organisation_id))]
    completeness = compute_profile_completeness(profile_data, rules)
    profile_data["profile_completeness"] = completeness
    state.profile_completeness = completeness
    state.user_profile = HouseholdMemberProfileModel.model_validate(profile_data)
    state.turn_count_since_result += 1

    match_snapshot = await _run_match(db, organisation_id, profile_data)
    should_return_result = (
        completeness >= 75
        and (
            match_snapshot["matched_schemes"]
            or match_snapshot["near_miss_schemes"]
            or not match_snapshot["incomplete_schemes"][:10]
        )
    ) or state.turn_count_since_result >= get_settings().agent_max_questions_before_result

    if should_return_result:
        content = format_match_result(type("MatchResult", (), match_snapshot)()) if False else _format_snapshot(match_snapshot)
        output_type = "result"
        payload = match_snapshot
        state.turn_count_since_result = 0
        if not match_snapshot["matched_schemes"] and not match_snapshot["near_miss_schemes"]:
            db.add(
                ZeroMatchEvent(
                    organisation_id=organisation_id,
                    conversation_session_id=row.id,
                    profile_id=row.active_profile_id,
                    original_query_text=input_message.message,
                    language_code=input_message.language_code,
                    profile_snapshot=profile_data,
                )
            )
    else:
        question = select_next_question(state, rules)
        if question.asked_key not in state.asked_fields:
            state.asked_fields.append(question.asked_key)
        content = question.text
        output_type = "question"
        payload = {"asked_field": question.asked_key}

    state.messages.append({"role": "assistant", "content": content})
    await _persist_profile(db, UUID(state.active_member_id), profile_data, organisation_id, "conversation")
    row.profile_completeness = state.profile_completeness
    row.confidence_score = max((fact.confidence for fact in extracted.facts), default=0)
    row.asked_fields = state.asked_fields
    row.remaining_required_fields = state.remaining_required_fields
    row.language_code = input_message.language_code
    row.expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS)
    db.add(
        ConversationMessage(
            organisation_id=organisation_id,
            conversation_session_id=row.id,
            role="assistant",
            content=content,
            language_code=input_message.language_code,
            structured_payload=payload or {},
        )
    )
    await db.commit()
    await _store().write_state(row.redis_key, state.model_dump(mode="json"))
    return ChatOutputModel(
        type=output_type,
        content=content,
        profile_completeness=state.profile_completeness,
        session_id=input_message.session_id,
        payload=payload,
    )


def _format_snapshot(snapshot: dict) -> str:
    if snapshot["matched_schemes"]:
        first = snapshot["matched_schemes"][0]["scheme"]["name"]
        count = len(snapshot["matched_schemes"])
        return f"You appear eligible for {count} scheme{'s' if count != 1 else ''}. The strongest match is {first}."
    if snapshot["near_miss_schemes"]:
        first = snapshot["near_miss_schemes"][0]["scheme"]["name"]
        return f"You are close to qualifying for {first}. I will show what is missing."
    return (
        "I could not find a matching scheme from the current list. "
        "You can try again after adding income, caste, disability, or pregnancy details."
    )
