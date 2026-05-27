from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.dashboard.audit import add_audit_log
from app.dashboard.rbac import DashboardActor, assert_beneficiary_access, require_actor_permission
from app.db.models import (
    ApplicationStatus,
    ApplicationStatusEvent,
    Beneficiary,
    BeneficiaryFollowup,
    BeneficiaryNote,
    BeneficiarySchemeAssignment,
    DocumentChecklistItem,
    Profile,
    Scheme,
)
from app.schemas.phase5 import (
    ApplicationStatusUpdateRequest,
    BeneficiaryDetailResponse,
    BeneficiaryListResponse,
    BeneficiaryResponse,
    CreateBeneficiaryRequest,
    FollowupRequest,
    FollowupUpdateRequest,
    UpdateBeneficiaryRequest,
)
from app.services.phase4 import assert_no_aadhaar_payload


PROFILE_FIELDS = {
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
}


def _profile_payload(profile: Profile) -> dict[str, Any]:
    return {field: getattr(profile, field) for field in PROFILE_FIELDS if hasattr(profile, field)}


async def _get_beneficiary(db: AsyncSession, actor: DashboardActor, beneficiary_id: UUID) -> Beneficiary:
    beneficiary = await db.get(Beneficiary, beneficiary_id)
    if beneficiary is None or beneficiary.deleted_at is not None:
        raise ApiError(404, "BENEFICIARY_NOT_FOUND", "Beneficiary was not found.", "beneficiary_id")
    assert_beneficiary_access(actor, beneficiary.organisation_id, beneficiary.assigned_operator_id)
    return beneficiary


def _scope_stmt(stmt: Select, actor: DashboardActor) -> Select:
    if actor.role != "super_admin":
        stmt = stmt.where(Beneficiary.organisation_id == actor.organisation_id)
    if actor.role == "operator":
        stmt = stmt.where(Beneficiary.assigned_operator_id == actor.member_id)
    return stmt.where(Beneficiary.deleted_at.is_(None))


async def _status_rows(db: AsyncSession, organisation_id: UUID, profile_id: UUID) -> list[dict[str, Any]]:
    rows = await db.scalars(
        select(ApplicationStatus).where(
            ApplicationStatus.organisation_id == organisation_id,
            ApplicationStatus.profile_id == profile_id,
        )
    )
    return [{"id": str(row.id), "scheme_id": row.scheme_id, "status": row.status} for row in rows.all()]


async def _open_followup(db: AsyncSession, organisation_id: UUID, beneficiary_id: UUID) -> dict[str, Any] | None:
    row = await db.scalar(
        select(BeneficiaryFollowup)
        .where(
            BeneficiaryFollowup.organisation_id == organisation_id,
            BeneficiaryFollowup.beneficiary_id == beneficiary_id,
            BeneficiaryFollowup.status == "open",
        )
        .order_by(BeneficiaryFollowup.due_date.asc())
        .limit(1)
    )
    if row is None:
        return None
    return {"id": str(row.id), "due_date": row.due_date.isoformat(), "reason": row.reason, "status": row.status}


async def beneficiary_response(db: AsyncSession, row: Beneficiary) -> BeneficiaryResponse:
    return BeneficiaryResponse(
        id=row.id,
        name=row.name,
        phone_e164=row.phone_e164,
        state_code=row.state_code,
        language_code=row.language_code,
        village=row.village,
        district=row.district,
        profile_id=row.profile_id,
        assigned_operator_id=row.assigned_operator_id,
        application_statuses=await _status_rows(db, row.organisation_id, row.profile_id),
        follow_up=await _open_followup(db, row.organisation_id, row.id),
    )


async def list_beneficiaries(
    db: AsyncSession,
    actor: DashboardActor,
    q: str | None = None,
    state_code: str | None = None,
    status: str | None = None,
    assigned_operator_id: UUID | None = None,
    followup_due: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> BeneficiaryListResponse:
    require_actor_permission(actor, "beneficiary:read")
    stmt = _scope_stmt(select(Beneficiary), actor)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Beneficiary.name).like(pattern), func.lower(Beneficiary.phone_e164).like(pattern), func.lower(Beneficiary.village).like(pattern)))
    if state_code:
        stmt = stmt.where(Beneficiary.state_code == state_code)
    if assigned_operator_id and actor.role != "operator":
        stmt = stmt.where(Beneficiary.assigned_operator_id == assigned_operator_id)
    if status:
        stmt = stmt.join(ApplicationStatus, ApplicationStatus.profile_id == Beneficiary.profile_id).where(ApplicationStatus.status == status)
    if followup_due in {"today", "overdue", "all"}:
        stmt = stmt.join(BeneficiaryFollowup, BeneficiaryFollowup.beneficiary_id == Beneficiary.id).where(BeneficiaryFollowup.status == "open")
        if followup_due == "today":
            stmt = stmt.where(BeneficiaryFollowup.due_date == date.today())
        elif followup_due == "overdue":
            stmt = stmt.where(BeneficiaryFollowup.due_date < date.today())
    total = int(await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = await db.scalars(stmt.order_by(Beneficiary.updated_at.desc()).limit(limit).offset(offset))
    return BeneficiaryListResponse(items=[await beneficiary_response(db, row) for row in rows.all()], total=total)


async def create_beneficiary(db: AsyncSession, actor: DashboardActor, request: CreateBeneficiaryRequest) -> BeneficiaryResponse:
    require_actor_permission(actor, "beneficiary:write")
    assert_no_aadhaar_payload(request.model_dump(mode="json"))
    assigned_operator_id = request.assigned_operator_id or (actor.member_id if actor.role == "operator" else None)
    if actor.role == "operator" and assigned_operator_id != actor.member_id:
        raise ApiError(403, "ASSIGNMENT_DENIED", "Operators can assign only to themselves.", "assigned_operator_id")
    profile_data = {key: value for key, value in request.profile.items() if key in PROFILE_FIELDS}
    profile = Profile(
        organisation_id=actor.organisation_id,
        display_name=request.name,
        state_code=request.state_code,
        district=request.district,
        **profile_data,
    )
    db.add(profile)
    await db.flush()
    beneficiary = Beneficiary(
        organisation_id=actor.organisation_id,
        profile_id=profile.id,
        assigned_operator_id=assigned_operator_id,
        name=request.name,
        phone_e164=request.phone_e164,
        state_code=request.state_code,
        language_code=request.language_code,
        village=request.village,
        district=request.district,
        source="operator",
    )
    db.add(beneficiary)
    await db.flush()
    add_audit_log(db, actor, "beneficiary.create", "beneficiary", str(beneficiary.id), after={"name": beneficiary.name, "profile_id": str(profile.id)})
    await db.commit()
    await db.refresh(beneficiary)
    return await beneficiary_response(db, beneficiary)


async def get_beneficiary_detail(db: AsyncSession, actor: DashboardActor, beneficiary_id: UUID) -> BeneficiaryDetailResponse:
    require_actor_permission(actor, "beneficiary:read")
    beneficiary = await _get_beneficiary(db, actor, beneficiary_id)
    profile = await db.get(Profile, beneficiary.profile_id)
    notes = await db.scalars(select(BeneficiaryNote).where(BeneficiaryNote.beneficiary_id == beneficiary.id).order_by(BeneficiaryNote.created_at.desc()))
    followups = await db.scalars(select(BeneficiaryFollowup).where(BeneficiaryFollowup.beneficiary_id == beneficiary.id).order_by(BeneficiaryFollowup.due_date.asc()))
    assignments = await db.scalars(select(BeneficiarySchemeAssignment).where(BeneficiarySchemeAssignment.beneficiary_id == beneficiary.id))
    base = await beneficiary_response(db, beneficiary)
    return BeneficiaryDetailResponse(
        **base.model_dump(),
        profile=_profile_payload(profile) if profile else {},
        notes=[{"id": str(row.id), "note": row.note, "created_at": row.created_at.isoformat()} for row in notes.all()],
        followups=[{"id": str(row.id), "due_date": row.due_date.isoformat(), "reason": row.reason, "status": row.status} for row in followups.all()],
        assigned_schemes=[{"id": str(row.id), "scheme_id": row.scheme_id, "assignment_source": row.assignment_source} for row in assignments.all()],
        document_checklist=await document_review_items(db, actor, beneficiary.id),
    )


async def update_beneficiary(db: AsyncSession, actor: DashboardActor, beneficiary_id: UUID, request: UpdateBeneficiaryRequest) -> BeneficiaryResponse:
    require_actor_permission(actor, "beneficiary:write")
    assert_no_aadhaar_payload(request.model_dump(mode="json", exclude_none=True))
    beneficiary = await _get_beneficiary(db, actor, beneficiary_id)
    before = {"name": beneficiary.name, "assigned_operator_id": str(beneficiary.assigned_operator_id) if beneficiary.assigned_operator_id else None}
    for field in ["name", "phone_e164", "state_code", "language_code", "village", "district", "assigned_operator_id"]:
        value = getattr(request, field)
        if value is not None:
            if field == "assigned_operator_id" and actor.role == "operator" and value != actor.member_id:
                raise ApiError(403, "ASSIGNMENT_DENIED", "Operators can assign only to themselves.", field)
            setattr(beneficiary, field, value)
    if request.profile:
        profile = await db.get(Profile, beneficiary.profile_id)
        if profile:
            for key, value in request.profile.items():
                if key in PROFILE_FIELDS:
                    setattr(profile, key, value)
    add_audit_log(db, actor, "beneficiary.update", "beneficiary", str(beneficiary.id), before=before, after={"name": beneficiary.name})
    await db.commit()
    await db.refresh(beneficiary)
    return await beneficiary_response(db, beneficiary)


async def add_note(db: AsyncSession, actor: DashboardActor, beneficiary_id: UUID, note: str) -> dict[str, Any]:
    require_actor_permission(actor, "beneficiary:write")
    beneficiary = await _get_beneficiary(db, actor, beneficiary_id)
    row = BeneficiaryNote(organisation_id=beneficiary.organisation_id, beneficiary_id=beneficiary.id, author_member_id=actor.member_id, note=note)
    db.add(row)
    await db.flush()
    add_audit_log(db, actor, "beneficiary.note.create", "beneficiary", str(beneficiary.id), after={"note_id": str(row.id)})
    await db.commit()
    return {"id": row.id, "note": row.note}


async def add_followup(db: AsyncSession, actor: DashboardActor, beneficiary_id: UUID, request: FollowupRequest) -> dict[str, Any]:
    require_actor_permission(actor, "beneficiary:write")
    beneficiary = await _get_beneficiary(db, actor, beneficiary_id)
    row = BeneficiaryFollowup(
        organisation_id=beneficiary.organisation_id,
        beneficiary_id=beneficiary.id,
        assigned_operator_id=beneficiary.assigned_operator_id,
        due_date=request.due_date,
        reason=request.reason,
    )
    db.add(row)
    await db.flush()
    add_audit_log(db, actor, "beneficiary.followup.create", "beneficiary", str(beneficiary.id), after={"followup_id": str(row.id)})
    await db.commit()
    return {"id": row.id, "due_date": row.due_date, "status": row.status}


async def update_followup(db: AsyncSession, actor: DashboardActor, followup_id: UUID, request: FollowupUpdateRequest) -> dict[str, Any]:
    followup = await db.get(BeneficiaryFollowup, followup_id)
    if followup is None:
        raise ApiError(404, "FOLLOWUP_NOT_FOUND", "Follow-up was not found.", "followup_id")
    beneficiary = await _get_beneficiary(db, actor, followup.beneficiary_id)
    followup.status = request.status
    followup.completed_at = datetime.now(timezone.utc) if request.status == "completed" else None
    add_audit_log(db, actor, "beneficiary.followup.update", "beneficiary", str(beneficiary.id), after={"followup_id": str(followup.id), "status": followup.status})
    await db.commit()
    return {"id": followup.id, "status": followup.status}


async def update_application_status(db: AsyncSession, actor: DashboardActor, status_id: UUID, request: ApplicationStatusUpdateRequest) -> dict[str, Any]:
    row = await db.get(ApplicationStatus, status_id)
    if row is None:
        raise ApiError(404, "APPLICATION_STATUS_NOT_FOUND", "Application status was not found.", "status_id")
    beneficiary = await db.scalar(select(Beneficiary).where(Beneficiary.organisation_id == row.organisation_id, Beneficiary.profile_id == row.profile_id))
    if beneficiary is None:
        raise ApiError(404, "BENEFICIARY_NOT_FOUND", "Beneficiary was not found.", "beneficiary_id")
    assert_beneficiary_access(actor, beneficiary.organisation_id, beneficiary.assigned_operator_id)
    old_status = row.status
    row.status = request.status
    row.notes = request.notes
    row.source = "operator"
    db.add(ApplicationStatusEvent(organisation_id=row.organisation_id, application_status_id=row.id, old_status=old_status, new_status=row.status, source="operator", notes=request.notes))
    add_audit_log(db, actor, "application_status.update", "application_status", str(row.id), before={"status": old_status}, after={"status": row.status})
    await db.commit()
    return {"id": row.id, "status": row.status}


async def status_board(db: AsyncSession, actor: DashboardActor, state_code: str | None = None) -> dict[str, list[dict[str, Any]]]:
    require_actor_permission(actor, "beneficiary:read")
    stmt = _scope_stmt(select(Beneficiary, ApplicationStatus).join(ApplicationStatus, ApplicationStatus.profile_id == Beneficiary.profile_id), actor)
    if state_code:
        stmt = stmt.where(Beneficiary.state_code == state_code)
    rows = (await db.execute(stmt)).all()
    columns = {"not_started": [], "documents_gathering": [], "submitted": [], "approved": []}
    for beneficiary, status in rows:
        column = "submitted" if status.status == "pending" else status.status
        if column in columns:
            columns[column].append({"status_id": str(status.id), "beneficiary_id": str(beneficiary.id), "name": beneficiary.name, "scheme_id": status.scheme_id, "status": status.status})
    return columns


async def scheme_guide(db: AsyncSession, actor: DashboardActor) -> list[dict[str, Any]]:
    require_actor_permission(actor, "scheme:read")
    stmt = select(Scheme).where(Scheme.is_active.is_(True), Scheme.status == "active")
    if actor.role != "super_admin":
        stmt = stmt.where(Scheme.organisation_id == actor.organisation_id)
    rows = await db.scalars(stmt.order_by(Scheme.name))
    return [
        {
            "id": row.id,
            "name": row.name,
            "plain_language_summary": row.plain_language_summary,
            "state_code": row.state_code,
            "benefit_amount": row.benefit_amount,
            "application_url": row.application_url,
        }
        for row in rows.all()
    ]


async def document_review_items(db: AsyncSession, actor: DashboardActor, beneficiary_id: UUID) -> list[dict[str, Any]]:
    beneficiary = await _get_beneficiary(db, actor, beneficiary_id)
    rows = await db.scalars(select(DocumentChecklistItem).where(DocumentChecklistItem.organisation_id == beneficiary.organisation_id, DocumentChecklistItem.profile_id == beneficiary.profile_id))
    return [{"id": str(row.id), "document_name": row.document_name, "status": row.status, "metadata": row.metadata_} for row in rows.all()]
