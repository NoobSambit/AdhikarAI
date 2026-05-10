from datetime import date
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import EligibilityRule, Organisation, Scheme, SchemeCategory, SchemeStatusEvent, SchemeVersion
from app.schemas.scheme import (
    AdminSchemeResponse,
    CreateSchemeRequest,
    EligibilityCriteriaModel,
    SchemeDetailModel,
    SchemeSummaryModel,
    UpdateSchemeRequest,
)
from app.services.eligibility.validation import validate_rule


async def ensure_organisation(db: AsyncSession, organisation_id: str) -> Organisation:
    org = await db.get(Organisation, UUID(organisation_id))
    if org is None:
        raise ApiError(404, "ORGANISATION_NOT_FOUND", "Organisation was not found.", "organisation_id")
    return org


async def known_scheme_ids(db: AsyncSession, organisation_id: UUID) -> set[str]:
    rows = await db.scalars(select(Scheme.id).where(Scheme.organisation_id == organisation_id))
    return set(rows.all())


def raise_first_rule_issue(criteria: EligibilityCriteriaModel, known_ids: set[str]) -> None:
    issues = validate_rule(criteria, known_ids)
    if not issues:
        return
    issue = issues[0]
    status = 422
    raise ApiError(status, issue.code, issue.message, issue.field, [item.__dict__ for item in issues])


async def _category_id(db: AsyncSession, organisation_id: UUID, code: str | None):
    if code is None:
        return None
    category = await db.scalar(
        select(SchemeCategory).where(
            SchemeCategory.organisation_id == organisation_id,
            SchemeCategory.code == code,
        )
    )
    return category.id if category else None


async def create_scheme(db: AsyncSession, request: CreateSchemeRequest) -> AdminSchemeResponse:
    org = await ensure_organisation(db, request.organisation_id)
    if await db.get(Scheme, request.id):
        raise ApiError(409, "SCHEME_ID_EXISTS", "Scheme ID already exists.", "id")
    ids = await known_scheme_ids(db, org.id)
    raise_first_rule_issue(request.eligibility_rule, ids)
    scheme = Scheme(
        id=request.id,
        organisation_id=org.id,
        category_id=await _category_id(db, org.id, request.category_code),
        name=request.name,
        description=request.description,
        plain_language_summary=request.plain_language_summary,
        ministry=request.ministry,
        state_code=request.state_code,
        benefit_type=request.benefit_type,
        benefit_amount=request.benefit_amount,
        application_url=request.application_url,
        is_active=False,
        status="draft",
        valid_from=request.valid_from,
        valid_until=request.valid_until,
        source_url=request.source_url,
        external_source=request.external_source,
        external_id=request.external_id,
        verification_status=request.verification_status,
        source_last_checked_at=request.source_last_checked_at,
    )
    db.add(scheme)
    db.add(EligibilityRule(organisation_id=org.id, scheme_id=request.id, version=1, criteria=request.eligibility_rule.model_dump(mode="json"), is_active=True))
    await db.commit()
    return AdminSchemeResponse(id=request.id, version=1, status="draft")


async def update_scheme(db: AsyncSession, scheme_id: str, request: UpdateSchemeRequest) -> AdminSchemeResponse:
    org = await ensure_organisation(db, request.organisation_id)
    scheme = await db.get(Scheme, scheme_id)
    if scheme is None or scheme.organisation_id != org.id:
        raise ApiError(404, "SCHEME_NOT_FOUND", "Scheme was not found.", "id")
    active_rule = await latest_rule(db, org.id, scheme_id, active_only=False)
    merged_rule = request.eligibility_rule or EligibilityCriteriaModel.model_validate(active_rule.criteria)
    ids = await known_scheme_ids(db, org.id)
    raise_first_rule_issue(merged_rule, ids - {scheme_id})
    version = (active_rule.version if active_rule else 0) + 1
    db.add(
        SchemeVersion(
            organisation_id=org.id,
            scheme_id=scheme_id,
            version=version,
            scheme_snapshot=scheme_to_snapshot(scheme),
            rule_snapshot=active_rule.criteria if active_rule else {},
            change_summary=request.change_summary,
        )
    )
    for field in [
        "name",
        "description",
        "plain_language_summary",
        "ministry",
        "state_code",
        "benefit_type",
        "benefit_amount",
        "application_url",
        "valid_from",
        "valid_until",
        "source_url",
        "verification_status",
    ]:
        value = getattr(request, field)
        if value is not None:
            setattr(scheme, field, value)
    scheme.category_id = await _category_id(db, org.id, request.category_code) if request.category_code else scheme.category_id
    scheme.status = "active" if request.publish else "draft"
    scheme.is_active = request.publish
    await db.execute(update(EligibilityRule).where(EligibilityRule.organisation_id == org.id, EligibilityRule.scheme_id == scheme_id).values(is_active=False))
    db.add(EligibilityRule(organisation_id=org.id, scheme_id=scheme_id, version=version, criteria=merged_rule.model_dump(mode="json"), is_active=True))
    await db.commit()
    return AdminSchemeResponse(id=scheme_id, version=version, status=scheme.status)


def scheme_to_snapshot(scheme: Scheme) -> dict:
    return {
        "id": scheme.id,
        "name": scheme.name,
        "description": scheme.description,
        "status": scheme.status,
        "is_active": scheme.is_active,
        "valid_until": scheme.valid_until.isoformat() if scheme.valid_until else None,
    }


async def latest_rule(db: AsyncSession, organisation_id: UUID, scheme_id: str, active_only: bool = True) -> EligibilityRule:
    stmt = select(EligibilityRule).where(
        EligibilityRule.organisation_id == organisation_id,
        EligibilityRule.scheme_id == scheme_id,
    )
    if active_only:
        stmt = stmt.where(EligibilityRule.is_active.is_(True))
    rule = await db.scalar(stmt.order_by(EligibilityRule.version.desc()).limit(1))
    if rule is None:
        raise ApiError(404, "RULE_NOT_FOUND", "Eligibility rule was not found.", "eligibility_rule")
    return rule


async def publish_scheme(db: AsyncSession, organisation_id: str, scheme_id: str) -> AdminSchemeResponse:
    org = await ensure_organisation(db, organisation_id)
    scheme = await db.get(Scheme, scheme_id)
    if scheme is None or scheme.organisation_id != org.id:
        raise ApiError(404, "SCHEME_NOT_FOUND", "Scheme was not found.", "id")
    old = scheme.status
    scheme.status = "active"
    scheme.is_active = True
    db.add(SchemeStatusEvent(organisation_id=org.id, scheme_id=scheme_id, old_status=old, new_status="active", reason="Published by admin."))
    rule = await latest_rule(db, org.id, scheme_id)
    await db.commit()
    return AdminSchemeResponse(id=scheme_id, version=rule.version, status="active")


async def archive_scheme(db: AsyncSession, organisation_id: str, scheme_id: str, reason: str) -> AdminSchemeResponse:
    org = await ensure_organisation(db, organisation_id)
    scheme = await db.get(Scheme, scheme_id)
    if scheme is None or scheme.organisation_id != org.id:
        raise ApiError(404, "SCHEME_NOT_FOUND", "Scheme was not found.", "id")
    old = scheme.status
    scheme.status = "archived"
    scheme.is_active = False
    db.add(SchemeStatusEvent(organisation_id=org.id, scheme_id=scheme_id, old_status=old, new_status="archived", reason=reason))
    rule = await latest_rule(db, org.id, scheme_id, active_only=False)
    await db.commit()
    return AdminSchemeResponse(id=scheme_id, version=rule.version, status="archived")


async def list_schemes(
    db: AsyncSession,
    organisation_id: str,
    status: str | None,
    state_code: str | None,
    category_code: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Scheme], int]:
    org = await ensure_organisation(db, organisation_id)
    stmt: Select = select(Scheme).where(Scheme.organisation_id == org.id)
    if status:
        stmt = stmt.where(Scheme.status == status)
    if state_code:
        stmt = stmt.where(Scheme.state_code == state_code)
    if category_code:
        stmt = stmt.join(SchemeCategory, Scheme.category_id == SchemeCategory.id).where(SchemeCategory.code == category_code)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await db.scalars(stmt.order_by(Scheme.name).limit(limit).offset(offset))
    return list(rows.all()), int(total or 0)


async def get_scheme_detail(db: AsyncSession, organisation_id: str, scheme_id: str) -> SchemeDetailModel:
    org = await ensure_organisation(db, organisation_id)
    scheme = await db.get(Scheme, scheme_id)
    if scheme is None or scheme.organisation_id != org.id:
        raise ApiError(404, "SCHEME_NOT_FOUND", "Scheme was not found.", "id")
    rule = await latest_rule(db, org.id, scheme_id, active_only=False)
    criteria = EligibilityCriteriaModel.model_validate(rule.criteria)
    return SchemeDetailModel(
        id=scheme.id,
        name=scheme.name,
        description=scheme.description,
        ministry=scheme.ministry,
        state_code=scheme.state_code,
        benefit_type=scheme.benefit_type,
        benefit_amount=scheme.benefit_amount,
        application_url=scheme.application_url,
        is_active=scheme.is_active,
        valid_until=scheme.valid_until,
        required_documents=criteria.required_documents,
        plain_language_summary=scheme.plain_language_summary,
        status=scheme.status,
        valid_from=scheme.valid_from,
        source_url=scheme.source_url,
        verification_status=scheme.verification_status,
        source_last_checked_at=scheme.source_last_checked_at,
        eligibility_rule=criteria,
    )


async def active_scheme_rules(db: AsyncSession, organisation_id: str):
    org = await ensure_organisation(db, organisation_id)
    today = date.today()
    schemes = await db.scalars(
        select(Scheme)
        .where(
            Scheme.organisation_id == org.id,
            Scheme.is_active.is_(True),
            Scheme.status == "active",
            (Scheme.valid_until.is_(None)) | (Scheme.valid_until >= today),
        )
        .order_by(Scheme.name)
    )
    output = []
    for scheme in schemes.all():
        rule = await latest_rule(db, org.id, scheme.id)
        output.append(SimpleNamespace(scheme=scheme, rule=EligibilityCriteriaModel.model_validate(rule.criteria)))
    return output


def scheme_summary(scheme: Scheme, criteria: EligibilityCriteriaModel) -> SchemeSummaryModel:
    return SchemeSummaryModel(
        id=scheme.id,
        name=scheme.name,
        description=scheme.description,
        ministry=scheme.ministry,
        state_code=scheme.state_code,
        benefit_type=scheme.benefit_type,
        benefit_amount=scheme.benefit_amount,
        application_url=scheme.application_url,
        is_active=scheme.is_active,
        valid_until=scheme.valid_until,
        required_documents=criteria.required_documents,
    )
