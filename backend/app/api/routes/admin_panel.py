from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin_panel.queries import analytics, list_quality_flags, review_quality_flag, unmatched_query_groups
from app.admin_panel.scheme_drafts import create_scheme_draft, preview_scheme_draft, publish_scheme_draft
from app.core.security import require_dashboard_actor
from app.dashboard.rbac import DashboardActor, require_actor_permission
from app.db.session import get_db
from app.schemas.phase5 import ReviewQualityFlagRequest, SchemeDraftRequest

router = APIRouter(prefix="/admin")


@router.get("/unmatched-queries")
async def get_unmatched_queries(actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return {"items": await unmatched_query_groups(db, actor)}


@router.get("/unmatched-queries.csv")
async def get_unmatched_queries_csv(actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    from fastapi.responses import StreamingResponse

    rows = await unmatched_query_groups(db, actor)
    lines = ["normalized_query_text,frequency,languages,latest_at\n"]
    lines.extend(f"{row['normalized_query_text']},{row['frequency']},{'|'.join(row['languages'])},{row['latest_at']}\n" for row in rows)
    return StreamingResponse(iter(lines), media_type="text/csv")


@router.post("/scheme-drafts")
async def post_scheme_draft(request: SchemeDraftRequest, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return await create_scheme_draft(db, actor, request.draft_payload, request.change_summary)


@router.post("/scheme-drafts/{draft_id}/preview")
async def preview_draft(draft_id: UUID, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return await preview_scheme_draft(db, actor, draft_id)


@router.post("/scheme-drafts/{draft_id}/publish")
async def publish_draft(draft_id: UUID, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return await publish_scheme_draft(db, actor, draft_id)


@router.get("/schemes/{scheme_id}/history")
async def scheme_history(scheme_id: str, actor: DashboardActor = Depends(require_dashboard_actor)):
    require_actor_permission(actor, "scheme:read")
    return {"items": [], "scheme_id": scheme_id}


@router.get("/analytics")
async def get_admin_analytics(organisation_id: UUID | None = None, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return await analytics(db, actor, organisation_id)


@router.get("/quality-flags")
async def get_quality_flags(actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return {"items": await list_quality_flags(db, actor)}


@router.post("/quality-flags/{flag_id}/review")
async def post_quality_review(flag_id: UUID, request: ReviewQualityFlagRequest, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return await review_quality_flag(db, actor, flag_id, request.review_notes)
