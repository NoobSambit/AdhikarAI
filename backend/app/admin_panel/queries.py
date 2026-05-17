from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.dashboard.rbac import DashboardActor, require_actor_permission
from app.db.models import ConversationMessage, Profile, QualityFlag, UnmatchedQuery, VoiceTurn


async def unmatched_query_groups(db: AsyncSession, actor: DashboardActor) -> list[dict]:
    require_actor_permission(actor, "analytics:read")
    stmt = (
        select(
            UnmatchedQuery.normalized_query_text,
            func.count(UnmatchedQuery.id),
            func.array_agg(func.distinct(UnmatchedQuery.language_code)),
            func.max(UnmatchedQuery.created_at),
        )
        .group_by(UnmatchedQuery.normalized_query_text)
        .order_by(func.count(UnmatchedQuery.id).desc())
    )
    if actor.role != "super_admin":
        stmt = stmt.where(UnmatchedQuery.organisation_id == actor.organisation_id)
    rows = (await db.execute(stmt)).all()
    return [
        {
            "normalized_query_text": text,
            "frequency": int(count),
            "languages": languages or [],
            "latest_at": latest,
        }
        for text, count, languages, latest in rows
    ]


async def analytics(db: AsyncSession, actor: DashboardActor, organisation_id: UUID | None = None) -> dict:
    require_actor_permission(actor, "analytics:read")
    org_id = organisation_id if actor.role == "super_admin" and organisation_id else actor.organisation_id
    messages = int(await db.scalar(select(func.count()).select_from(ConversationMessage).where(ConversationMessage.organisation_id == org_id)) or 0)
    avg = await db.scalar(select(func.avg(Profile.profile_completeness)).where(Profile.organisation_id == org_id))
    voice = int(await db.scalar(select(func.count()).select_from(VoiceTurn).where(VoiceTurn.organisation_id == org_id)) or 0)
    text_count = max(messages - voice, 0)
    total = voice + text_count
    return {
        "query_volume": {"daily": [{"date": datetime.now(timezone.utc).date().isoformat(), "count": messages}]},
        "language_breakdown": [],
        "top_matched_schemes": [],
        "top_near_miss_schemes": [],
        "average_profile_completeness": float(avg or 0),
        "voice_vs_text_usage_ratio": {"voice": (voice / total) if total else 0, "text": (text_count / total) if total else 0},
    }


async def list_quality_flags(db: AsyncSession, actor: DashboardActor) -> list[dict]:
    require_actor_permission(actor, "quality:review")
    stmt = select(QualityFlag)
    if actor.role != "super_admin":
        stmt = stmt.where(QualityFlag.organisation_id == actor.organisation_id)
    rows = await db.scalars(stmt.order_by(QualityFlag.created_at.desc()))
    return [
        {
            "id": str(row.id),
            "flag_type": row.flag_type,
            "severity": row.severity,
            "details": row.details,
            "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        }
        for row in rows.all()
    ]


async def review_quality_flag(db: AsyncSession, actor: DashboardActor, flag_id: UUID, notes: str) -> dict:
    require_actor_permission(actor, "quality:review")
    flag = await db.get(QualityFlag, flag_id)
    if flag is None or (actor.role != "super_admin" and flag.organisation_id != actor.organisation_id):
        raise ApiError(404, "QUALITY_FLAG_NOT_FOUND", "Quality flag was not found.", "flag_id")
    flag.reviewed_by = actor.member_id
    flag.reviewed_at = datetime.now(timezone.utc)
    flag.review_notes = notes
    await db.commit()
    return {"id": flag.id, "reviewed_at": flag.reviewed_at}
