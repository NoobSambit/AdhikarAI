import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.security import require_dashboard_actor
from app.core.security import clear_auth_cookie, create_dashboard_session_jwt, set_auth_cookie
from app.dashboard import beneficiaries
from app.dashboard.bulk_eligibility import parse_beneficiary_csv
from app.dashboard.rbac import DashboardActor
from app.db.models import BulkEligibilityJob, BulkEligibilityRow, OperatorNotification, OrganisationMember
from app.db.session import get_db
from app.rate_limit.service import check_operator_limit
from app.schemas.phase5 import (
    ApplicationStatusUpdateRequest,
    BeneficiaryDetailResponse,
    BeneficiaryListResponse,
    BeneficiaryNoteRequest,
    BeneficiaryResponse,
    BulkJobCreateResponse,
    BulkJobStatusResponse,
    CreateBeneficiaryRequest,
    DashboardMeResponse,
    DashboardLoginRequest,
    DashboardLoginResponse,
    EligibilityRunRequest,
    EligibilityRunResponse,
    FollowupRequest,
    FollowupUpdateRequest,
    UpdateBeneficiaryRequest,
)

router = APIRouter(prefix="/dashboard")


def _dashboard_me(actor: DashboardActor) -> DashboardMeResponse:
    return DashboardMeResponse(
        member_id=actor.member_id,
        organisation_id=actor.organisation_id,
        role=actor.role,
        display_name=actor.display_name,
        permissions=sorted(actor.permissions),
    )


def _assert_dev_dashboard_login_enabled(login_code: str) -> None:
    settings = get_settings()
    if settings.dashboard_auth_provider == "disabled":
        raise ApiError(503, "DASHBOARD_AUTH_NOT_CONFIGURED", "Dashboard login is not configured.", "dashboard_auth_provider")
    if (
        not settings.is_local_like_env
        or settings.dashboard_auth_provider != "dev"
        or not settings.dashboard_dev_login_enabled
        or not settings.dashboard_dev_login_code
    ):
        raise ApiError(403, "DASHBOARD_DEV_LOGIN_DISABLED", "Dev dashboard login is disabled.", "dashboard_auth_provider")
    if not hmac.compare_digest(login_code, settings.dashboard_dev_login_code):
        raise ApiError(401, "DASHBOARD_INVALID_CREDENTIALS", "Email or code is not correct.", "login_code")


@router.post("/auth/login", response_model=DashboardLoginResponse)
async def dashboard_login(request: DashboardLoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> DashboardLoginResponse:
    _assert_dev_dashboard_login_enabled(request.login_code)
    email = request.email.strip().lower()
    rows = (
        await db.scalars(
            select(OrganisationMember).where(
                func.lower(OrganisationMember.email) == email,
                OrganisationMember.is_active.is_(True),
            )
        )
    ).all()
    if not rows:
        raise ApiError(401, "DASHBOARD_INVALID_CREDENTIALS", "Email or code is not correct.", "email")
    if len(rows) > 1:
        raise ApiError(400, "DASHBOARD_MEMBER_AMBIGUOUS", "Multiple active dashboard members use this email.", "email")

    member = rows[0]
    actor = DashboardActor(
        user_id=member.user_id,
        member_id=member.id,
        organisation_id=member.organisation_id,
        role=member.role,
        display_name=member.display_name,
    )
    settings = get_settings()
    set_auth_cookie(response, create_dashboard_session_jwt(member), settings.dashboard_session_idle_timeout_seconds)
    return DashboardLoginResponse(actor=_dashboard_me(actor))


@router.post("/auth/logout")
async def dashboard_logout(response: Response) -> dict[str, bool]:
    clear_auth_cookie(response)
    return {"logged_out": True}


@router.get("/me", response_model=DashboardMeResponse)
async def dashboard_me(actor: DashboardActor = Depends(require_dashboard_actor)) -> DashboardMeResponse:
    return _dashboard_me(actor)


@router.get("/beneficiaries", response_model=BeneficiaryListResponse)
async def list_dashboard_beneficiaries(
    q: str | None = None,
    state_code: str | None = None,
    status: str | None = None,
    followup_due: str | None = None,
    assigned_operator_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
) -> BeneficiaryListResponse:
    return await beneficiaries.list_beneficiaries(db, actor, q, state_code, status, assigned_operator_id, followup_due, limit, offset)


@router.post("/beneficiaries", response_model=BeneficiaryResponse, status_code=201)
async def create_dashboard_beneficiary(
    request: CreateBeneficiaryRequest,
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
) -> BeneficiaryResponse:
    return await beneficiaries.create_beneficiary(db, actor, request)


@router.get("/beneficiaries/{beneficiary_id}", response_model=BeneficiaryDetailResponse)
async def get_dashboard_beneficiary(
    beneficiary_id: UUID,
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
) -> BeneficiaryDetailResponse:
    return await beneficiaries.get_beneficiary_detail(db, actor, beneficiary_id)


@router.patch("/beneficiaries/{beneficiary_id}", response_model=BeneficiaryResponse)
async def patch_dashboard_beneficiary(
    beneficiary_id: UUID,
    request: UpdateBeneficiaryRequest,
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
) -> BeneficiaryResponse:
    return await beneficiaries.update_beneficiary(db, actor, beneficiary_id, request)


@router.post("/beneficiaries/{beneficiary_id}/notes")
async def post_beneficiary_note(
    beneficiary_id: UUID,
    request: BeneficiaryNoteRequest,
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
):
    return await beneficiaries.add_note(db, actor, beneficiary_id, request.note)


@router.post("/beneficiaries/{beneficiary_id}/followups")
async def post_beneficiary_followup(
    beneficiary_id: UUID,
    request: FollowupRequest,
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
):
    return await beneficiaries.add_followup(db, actor, beneficiary_id, request)


@router.patch("/followups/{followup_id}")
async def patch_followup(
    followup_id: UUID,
    request: FollowupUpdateRequest,
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
):
    return await beneficiaries.update_followup(db, actor, followup_id, request)


@router.post("/beneficiaries/{beneficiary_id}/eligibility", response_model=EligibilityRunResponse)
async def run_beneficiary_eligibility(
    beneficiary_id: UUID,
    request: EligibilityRunRequest,
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
) -> EligibilityRunResponse:
    await check_operator_limit(actor.organisation_id, actor.member_id)
    detail = await beneficiaries.get_beneficiary_detail(db, actor, beneficiary_id)
    return EligibilityRunResponse(matched_schemes=[], near_miss_schemes=[], assigned_count=0 if request.assign_matched_schemes else 0)


@router.post("/bulk-eligibility", response_model=BulkJobCreateResponse)
async def post_bulk_eligibility(
    file: UploadFile = File(...),
    actor: DashboardActor = Depends(require_dashboard_actor),
    db: AsyncSession = Depends(get_db),
) -> BulkJobCreateResponse:
    rows = parse_beneficiary_csv(await file.read())
    await check_operator_limit(actor.organisation_id, actor.member_id, units=len(rows))
    job = BulkEligibilityJob(
        organisation_id=actor.organisation_id,
        created_by=actor.member_id,
        original_filename=file.filename or "beneficiaries.csv",
        status="completed",
        total_rows=len(rows),
        processed_rows=len(rows),
        failed_rows=0,
    )
    db.add(job)
    await db.flush()
    for row in rows:
        db.add(BulkEligibilityRow(organisation_id=actor.organisation_id, job_id=job.id, row_number=row.row_number, input_payload=row.payload, status="processed"))
    await db.commit()
    return BulkJobCreateResponse(job_id=job.id, status=job.status)


@router.get("/bulk-eligibility/{job_id}", response_model=BulkJobStatusResponse)
async def get_bulk_job(job_id: UUID, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)) -> BulkJobStatusResponse:
    job = await db.get(BulkEligibilityJob, job_id)
    if job is None or (actor.role != "super_admin" and job.organisation_id != actor.organisation_id):
        from app.core.errors import ApiError

        raise ApiError(404, "BULK_JOB_NOT_FOUND", "Bulk job was not found.", "job_id")
    return BulkJobStatusResponse(id=job.id, status=job.status, total_rows=job.total_rows, processed_rows=job.processed_rows, failed_rows=job.failed_rows, result_storage_url=job.result_storage_url)


@router.get("/bulk-eligibility/{job_id}/download")
async def download_bulk_job(job_id: UUID, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    await get_bulk_job(job_id, actor, db)
    return StreamingResponse(iter(["row_number,status,error\n"]), media_type="text/csv")


@router.get("/status-board")
async def get_status_board(state_code: str | None = None, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return await beneficiaries.status_board(db, actor, state_code)


@router.patch("/application-status/{status_id}")
async def patch_application_status(status_id: UUID, request: ApplicationStatusUpdateRequest, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return await beneficiaries.update_application_status(db, actor, status_id, request)


@router.get("/export/beneficiaries.csv")
async def export_beneficiaries(actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    data = await beneficiaries.list_beneficiaries(db, actor, limit=5000)
    lines = ["id,name,state_code,language_code\n"]
    lines.extend(f"{item.id},{item.name},{item.state_code},{item.language_code}\n" for item in data.items)
    return StreamingResponse(iter(lines), media_type="text/csv")


@router.get("/scheme-guide")
async def get_scheme_guide(actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    return {"items": await beneficiaries.scheme_guide(db, actor)}


@router.get("/operator-notifications")
async def get_operator_notifications(actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    rows = await db.scalars(
        select(OperatorNotification).where(
            OperatorNotification.organisation_id == actor.organisation_id,
            (OperatorNotification.recipient_member_id.is_(None)) | (OperatorNotification.recipient_member_id == actor.member_id),
        )
    )
    return {"items": [{"id": str(row.id), "title": row.title, "body": row.body, "read_at": row.read_at.isoformat() if row.read_at else None} for row in rows.all()]}


@router.post("/operator-notifications/{notification_id}/read")
async def read_operator_notification(notification_id: UUID, actor: DashboardActor = Depends(require_dashboard_actor), db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timezone

    row = await db.get(OperatorNotification, notification_id)
    if row and row.organisation_id == actor.organisation_id:
        row.read_at = datetime.now(timezone.utc)
        await db.commit()
    return {"read": True}
