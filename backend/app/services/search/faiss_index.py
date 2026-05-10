import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import FaissIndex, Scheme, SchemeEmbedding
from app.services.schemes import ensure_organisation
from app.services.search.embeddings import get_embedding_provider


@dataclass(frozen=True, slots=True)
class SearchResult:
    scheme_id: str
    name: str
    score: float
    search_mode: str


@dataclass(frozen=True, slots=True)
class FaissBuildResult:
    index_name: str
    scheme_count: int
    embedding_model: str
    status: str


def scheme_embedding_text(scheme: Scheme, rule_keywords: str = "") -> str:
    return " ".join(
        part
        for part in [
            scheme.name,
            scheme.description,
            scheme.plain_language_summary,
            scheme.benefit_type,
            scheme.benefit_amount,
            scheme.ministry,
            rule_keywords,
        ]
        if part
    )


async def active_search_schemes(db: AsyncSession, organisation_id: UUID) -> list[Scheme]:
    rows = await db.scalars(
        select(Scheme).where(
            Scheme.organisation_id == organisation_id,
            Scheme.is_active.is_(True),
            Scheme.status == "active",
        )
    )
    return list(rows.all())


async def rebuild_faiss_index(db: AsyncSession, organisation_id: str, index_name: str = "schemes_active") -> FaissBuildResult:
    org = await ensure_organisation(db, organisation_id)
    settings = get_settings()
    schemes = await active_search_schemes(db, org.id)
    texts = [scheme_embedding_text(scheme) for scheme in schemes]
    content_hash = hashlib.sha256(json.dumps([(s.id, t) for s, t in zip(schemes, texts)], sort_keys=True).encode()).hexdigest()
    provider = get_embedding_provider()
    vectors = provider.embed(texts) if texts else []
    dimension = len(vectors[0]) if vectors else 0
    index_dir = Path(settings.faiss_index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    storage_path = index_dir / f"{org.id}_{index_name}.json"
    payload = {"scheme_ids": [scheme.id for scheme in schemes], "vectors": vectors}
    storage_path.write_text(json.dumps(payload), encoding="utf-8")
    await db.execute(
        update(FaissIndex)
        .where(FaissIndex.organisation_id == org.id, FaissIndex.index_name == index_name)
        .values(is_active=False)
    )
    db.add(
        FaissIndex(
            organisation_id=org.id,
            index_name=index_name,
            embedding_model=settings.embedding_model,
            vector_dimension=dimension,
            storage_path=str(storage_path),
            content_hash=content_hash,
            scheme_count=len(schemes),
            is_active=True,
        )
    )
    await db.execute(
        delete(SchemeEmbedding).where(
            SchemeEmbedding.organisation_id == org.id,
            SchemeEmbedding.embedding_model == settings.embedding_model,
        )
    )
    for scheme, text, vector in zip(schemes, texts, vectors):
        db.add(
            SchemeEmbedding(
                organisation_id=org.id,
                scheme_id=scheme.id,
                embedding_model=settings.embedding_model,
                embedding_json=vector,
                embedding_text=text,
                embedding_hash=hashlib.sha256(text.encode()).hexdigest(),
            )
        )
    await db.commit()
    return FaissBuildResult(index_name, len(schemes), settings.embedding_model, "rebuilt")


async def search_schemes(db: AsyncSession, organisation_id: str, query: str, limit: int = 10) -> list[SearchResult]:
    org = await ensure_organisation(db, organisation_id)
    settings = get_settings()
    metadata = await db.scalar(
        select(FaissIndex)
        .where(FaissIndex.organisation_id == org.id, FaissIndex.index_name == "schemes_active", FaissIndex.is_active.is_(True))
        .order_by(FaissIndex.built_at.desc())
        .limit(1)
    )
    if metadata and Path(metadata.storage_path).exists():
        try:
            payload = json.loads(Path(metadata.storage_path).read_text(encoding="utf-8"))
            provider = get_embedding_provider()
            query_vector = provider.embed([query])[0]
            scores = []
            for scheme_id, vector in zip(payload["scheme_ids"], payload["vectors"]):
                score = sum(left * right for left, right in zip(query_vector, vector))
                scores.append((scheme_id, score))
            scores.sort(key=lambda item: item[1], reverse=True)
            schemes = await db.scalars(select(Scheme).where(Scheme.id.in_([scheme_id for scheme_id, _ in scores[:limit]])))
            by_id = {scheme.id: scheme for scheme in schemes.all()}
            return [
                SearchResult(scheme_id, by_id[scheme_id].name, float(score), "faiss")
                for scheme_id, score in scores[:limit]
                if scheme_id in by_id
            ]
        except Exception:
            pass
    return await fallback_text_search(db, org.id, query, limit)


async def fallback_text_search(db: AsyncSession, organisation_id: UUID, query: str, limit: int) -> list[SearchResult]:
    pattern = f"%{query}%"
    rows = await db.scalars(
        select(Scheme)
        .where(
            Scheme.organisation_id == organisation_id,
            Scheme.is_active.is_(True),
            Scheme.status == "active",
            (Scheme.name.ilike(pattern)) | (Scheme.description.ilike(pattern)) | (Scheme.plain_language_summary.ilike(pattern)),
        )
        .order_by(Scheme.name)
        .limit(limit)
    )
    return [SearchResult(scheme.id, scheme.name, 0.5, "fallback_text") for scheme in rows.all()]
