import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.agent_sessions import create_agent_session, get_agent_session, post_agent_message

from app.db.models import ConversationSession, EligibilityRule, Organisation, Profile, Scheme
from app.schemas.agent import ChatInputModel, CreateSessionRequest
from app.schemas.scheme import CustomCriterionModel, EligibilityCriteriaModel


@pytest.mark.asyncio
async def test_session_create_real_agent_candidates_and_match_snapshot(monkeypatch, tmp_path, db_session: AsyncSession, organisation: Organisation):
    monkeypatch.setenv("REDIS_URL", "memory://")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("FAISS_INDEX_DIR", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()
    await _seed_agent_schemes(db_session, organisation)

    created = await create_agent_session(CreateSessionRequest(organisation_id=organisation.id), db=db_session)
    message = await post_agent_message(
        ChatInputModel(session_id=created.session_id, organisation_id=organisation.id, message="I need help for pregnant woman first child"),
        db=db_session,
    )
    state = await get_agent_session(created.session_id, organisation.id, db=db_session)

    maternity_ids = {f"{organisation.id}-maternity_cash", f"{organisation.id}-mother_nutrition", f"{organisation.id}-first_child"}
    assert maternity_ids.issubset(set(message.payload["candidate_scheme_ids"]))
    assert message.payload["candidate_search_mode"] == "faiss"
    assert message.type == "question"
    assert message.payload["asked_field"].split(":", 1)[1] in {"age", "annual_income", "custom_attributes.is_pregnant", "custom_attributes.child_order"}
    assert state["profile_completeness"] > 0

    result = await post_agent_message(
        ChatInputModel(
            session_id=created.session_id,
            organisation_id=organisation.id,
            message="profile_facts: state_code=IN-BR; age=24; gender=female; annual_income=50000; is_pregnant=true; child_order=1",
        ),
        db=db_session,
    )
    row = await db_session.scalar(select(ConversationSession).where(ConversationSession.session_id == created.session_id))
    profile = await db_session.get(Profile, row.active_profile_id)
    await db_session.refresh(profile)

    assert result.type == "result"
    assert result.payload["matched_schemes"]
    assert result.payload["near_miss_schemes"] == []
    assert "incomplete_schemes" in result.payload
    assert profile.last_match_snapshot == result.payload


async def _seed_agent_schemes(db: AsyncSession, organisation: Organisation) -> None:
    cases = [
        (
            "maternity_cash",
            "Pregnant Woman Maternity Cash Benefit",
            "Cash support for pregnant women and first child care.",
            EligibilityCriteriaModel(
                gender=["female"],
                min_age=18,
                max_annual_income=100000,
                custom_criteria=[
                    CustomCriterionModel(field="is_pregnant", operator="equals", value=True, how_to_qualify="Must be pregnant."),
                    CustomCriterionModel(field="child_order", operator="lte", value=2, how_to_qualify="Only first two children are covered."),
                ],
            ),
        ),
        (
            "mother_nutrition",
            "Pregnant Mother Nutrition Support",
            "Food and nutrition support for a pregnant woman.",
            EligibilityCriteriaModel(
                gender=["female"],
                custom_criteria=[CustomCriterionModel(field="is_pregnant", operator="equals", value=True, how_to_qualify="Must be pregnant.")],
            ),
        ),
        (
            "first_child",
            "First Child Birth Support",
            "Support for a woman during first child birth.",
            EligibilityCriteriaModel(
                gender=["female"],
                custom_criteria=[CustomCriterionModel(field="child_order", operator="lte", value=1, how_to_qualify="This is for the first child.")],
            ),
        ),
        (
            "farmer",
            "Small Farmer Input Support",
            "Seed support for farmers.",
            EligibilityCriteriaModel(occupation_types=["farmer"]),
        ),
    ]
    for suffix, name, description, rule in cases:
        scheme_id = f"{organisation.id}-{suffix}"
        db.add(
            Scheme(
                id=scheme_id,
                organisation_id=organisation.id,
                name=name,
                description=description,
                plain_language_summary=description,
                ministry="Ministry",
                benefit_type="cash_transfer",
                benefit_amount="INR 1,000",
                is_active=True,
                status="active",
            )
        )
        db.add(EligibilityRule(organisation_id=organisation.id, scheme_id=scheme_id, version=1, criteria=rule.model_dump(mode="json"), is_active=True))
    await db.commit()
