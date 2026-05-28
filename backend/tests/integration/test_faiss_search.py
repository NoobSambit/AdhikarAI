from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import EligibilityRule, FaissIndex, Organisation, Scheme
from app.schemas.scheme import CustomCriterionModel, EligibilityCriteriaModel, RequiredDocumentModel
from app.services.search.embeddings import HashEmbeddingProvider
from app.services.search.faiss_index import rebuild_faiss_index, search_schemes


def test_hash_embedding_provider_is_lightweight_and_deterministic():
    provider = HashEmbeddingProvider()
    first = provider.embed(["pregnant woman"])[0]
    second = provider.embed(["pregnant woman"])[0]
    assert first == second
    assert len(first) == provider.dimension


async def _seed_search_schemes(db: AsyncSession, organisation: Organisation) -> None:
    rows = [
        (
            Scheme(
                id=f"{organisation.id}-maternity",
                organisation_id=organisation.id,
                name="Maternity Benefit Support",
                description="Cash support for pregnant women and first child nutrition.",
                plain_language_summary="Help for a pregnant woman before and after birth.",
                ministry="Women and Child Development",
                benefit_type="cash_transfer",
                benefit_amount="INR 5,000",
                is_active=True,
                status="active",
            ),
            EligibilityCriteriaModel(
                gender=["female"],
                min_age=18,
                custom_criteria=[
                    CustomCriterionModel(
                        field="is_pregnant",
                        operator="equals",
                        value=True,
                        how_to_qualify="This scheme is for pregnant women.",
                    )
                ],
                required_documents=[RequiredDocumentModel(name="MCP card", is_mandatory=True)],
            ),
        ),
        (
            Scheme(
                id=f"{organisation.id}-farmer",
                organisation_id=organisation.id,
                name="Farmer Input Support",
                description="Support for small farmers buying seeds.",
                plain_language_summary="Help for farmer families.",
                ministry="Agriculture",
                benefit_type="subsidy",
                benefit_amount="INR 2,000",
                is_active=True,
                status="active",
            ),
            EligibilityCriteriaModel(occupation_types=["farmer"], max_land_holding_acres=2),
        ),
        (
            Scheme(
                id=f"{organisation.id}-student",
                organisation_id=organisation.id,
                name="Girl Student Scholarship",
                description="Scholarship for girls in school.",
                plain_language_summary="Education support for girls.",
                ministry="Education",
                benefit_type="scholarship",
                benefit_amount="INR 1,000",
                is_active=True,
                status="active",
            ),
            EligibilityCriteriaModel(gender=["female"], max_age=18),
        ),
    ]
    for scheme, rule in rows:
        db.add(scheme)
        db.add(EligibilityRule(organisation_id=organisation.id, scheme_id=scheme.id, version=1, criteria=rule.model_dump(mode="json"), is_active=True))
    await db.commit()


@pytest.mark.asyncio
async def test_builds_real_faiss_index_files(monkeypatch, tmp_path, db_session, organisation):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("FAISS_INDEX_DIR", str(tmp_path))
    get_settings.cache_clear()
    await _seed_search_schemes(db_session, organisation)

    result = await rebuild_faiss_index(db_session, str(organisation.id))

    assert result.scheme_count == 3
    assert (tmp_path / f"{organisation.id}_schemes_active.faiss").exists()
    assert (tmp_path / f"{organisation.id}_schemes_active.ids.json").exists()


@pytest.mark.asyncio
async def test_search_rebuilds_and_returns_faiss(monkeypatch, tmp_path, db_session, organisation):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("FAISS_INDEX_DIR", str(tmp_path))
    get_settings.cache_clear()
    await _seed_search_schemes(db_session, organisation)

    results = await search_schemes(db_session, str(organisation.id), "pregnant woman", limit=3)

    assert results
    assert {item.search_mode for item in results} == {"faiss"}
    assert any("maternity" in item.scheme_id for item in results)


@pytest.mark.asyncio
async def test_missing_index_file_triggers_one_rebuild(monkeypatch, tmp_path, db_session, organisation):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("FAISS_INDEX_DIR", str(tmp_path))
    get_settings.cache_clear()
    await _seed_search_schemes(db_session, organisation)
    await rebuild_faiss_index(db_session, str(organisation.id))
    (tmp_path / f"{organisation.id}_schemes_active.faiss").unlink()

    results = await search_schemes(db_session, str(organisation.id), "pregnant woman", limit=3)

    assert results
    assert {item.search_mode for item in results} == {"faiss"}
    assert (tmp_path / f"{organisation.id}_schemes_active.faiss").exists()


@pytest.mark.asyncio
async def test_rebuild_failure_falls_back_to_text(monkeypatch, tmp_path, db_session, organisation):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("FAISS_INDEX_DIR", str(tmp_path))
    get_settings.cache_clear()
    await _seed_search_schemes(db_session, organisation)

    async def fail_rebuild(*_args, **_kwargs):
        raise RuntimeError("forced rebuild failure")

    monkeypatch.setattr("app.services.search.faiss_index.rebuild_faiss_index", fail_rebuild)
    db_session.add(
        FaissIndex(
            organisation_id=organisation.id,
            index_name="schemes_active",
            embedding_model="hash",
            vector_dimension=64,
            storage_path=str(tmp_path / f"{uuid4().hex}.faiss"),
            content_hash=uuid4().hex,
            scheme_count=3,
            is_active=True,
        )
    )
    await db_session.commit()

    results = await search_schemes(db_session, str(organisation.id), "pregnant woman", limit=3)

    assert results
    assert {item.search_mode for item in results} == {"fallback_text"}
