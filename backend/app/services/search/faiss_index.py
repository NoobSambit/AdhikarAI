import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import faiss
import numpy as np
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import FaissIndex, Scheme, SchemeEmbedding
from app.schemas.scheme import EligibilityCriteriaModel
from app.services.schemes import ensure_organisation, latest_rule
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


def _rule_keywords(rule: EligibilityCriteriaModel) -> str:
    parts: list[str] = []
    parts.extend(rule.occupation_types or [])
    parts.extend(rule.gender or [])
    parts.extend(rule.marital_status or [])
    parts.extend(rule.state_codes or [])
    for document in rule.required_documents:
        parts.append(document.name)
        for substitute in document.accepted_substitutes:
            parts.append(substitute.name)
            parts.append(substitute.issuing_authority)
    for criterion in rule.custom_criteria:
        parts.append(criterion.field.replace("_", " "))
        parts.append(str(criterion.value).replace("_", " "))
        parts.append(criterion.how_to_qualify)
    return " ".join(parts)


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
    rules = [EligibilityCriteriaModel.model_validate((await latest_rule(db, org.id, scheme.id)).criteria) for scheme in schemes]
    texts = [scheme_embedding_text(scheme, _rule_keywords(rule)) for scheme, rule in zip(schemes, rules)]
    content_hash = hashlib.sha256(json.dumps([(s.id, t) for s, t in zip(schemes, texts)], sort_keys=True).encode()).hexdigest()
    provider = get_embedding_provider()
    vectors = provider.embed(texts) if texts else []
    dimension = len(vectors[0]) if vectors else 0
    index_dir = Path(settings.faiss_index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    storage_path = index_dir / f"{org.id}_{index_name}.faiss"
    ids_path = index_dir / f"{org.id}_{index_name}.ids.json"
    if vectors:
        matrix = np.asarray(vectors, dtype="float32")
        faiss.normalize_L2(matrix)
        index = faiss.IndexFlatIP(dimension)
        index.add(matrix)
    else:
        index = faiss.IndexFlatIP(1)
    faiss.write_index(index, str(storage_path))
    ids_path.write_text(json.dumps([scheme.id for scheme in schemes]), encoding="utf-8")
    await db.execute(
        update(FaissIndex)
        .where(FaissIndex.organisation_id == org.id, FaissIndex.index_name == index_name)
        .values(is_active=False)
    )
    await db.execute(
        delete(FaissIndex).where(
            FaissIndex.organisation_id == org.id,
            FaissIndex.index_name == index_name,
            FaissIndex.content_hash == content_hash,
        )
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
    metadata = await _active_metadata(db, org.id)
    rebuilt = False
    if metadata is None or not Path(metadata.storage_path).exists():
        try:
            await rebuild_faiss_index(db, str(org.id))
            rebuilt = True
            metadata = await _active_metadata(db, org.id)
        except Exception:
            return await fallback_text_search(db, org.id, query, limit)
    if metadata and Path(metadata.storage_path).exists():
        try:
            ids_path = Path(metadata.storage_path).with_suffix(".ids.json")
            scheme_ids = json.loads(ids_path.read_text(encoding="utf-8"))
            if not scheme_ids:
                return []
            index = faiss.read_index(str(metadata.storage_path))
            provider = get_embedding_provider()
            query_vector = np.asarray(provider.embed([query]), dtype="float32")
            faiss.normalize_L2(query_vector)
            distances, indices = index.search(query_vector, min(limit, len(scheme_ids)))
            scores = [(scheme_ids[row_index], float(score)) for score, row_index in zip(distances[0], indices[0]) if row_index >= 0]
            schemes = await db.scalars(select(Scheme).where(Scheme.id.in_([scheme_id for scheme_id, _ in scores])))
            by_id = {scheme.id: scheme for scheme in schemes.all()}
            return [
                SearchResult(scheme_id, by_id[scheme_id].name, float(score), "faiss")
                for scheme_id, score in scores
                if scheme_id in by_id
            ]
        except Exception:
            if not rebuilt:
                try:
                    await rebuild_faiss_index(db, str(org.id))
                    return await search_schemes(db, organisation_id, query, limit)
                except Exception:
                    pass
    return await fallback_text_search(db, org.id, query, limit)


async def _active_metadata(db: AsyncSession, organisation_id: UUID) -> FaissIndex | None:
    return await db.scalar(
        select(FaissIndex)
        .where(FaissIndex.organisation_id == organisation_id, FaissIndex.index_name == "schemes_active", FaissIndex.is_active.is_(True))
        .order_by(FaissIndex.built_at.desc())
        .limit(1)
    )


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
