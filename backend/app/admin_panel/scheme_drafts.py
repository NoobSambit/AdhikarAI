from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.dashboard.rbac import DashboardActor, require_actor_permission
from app.db.models import EligibilityRule, OperatorNotification, Scheme, SchemeAuditLog, SchemeDraft, SchemeVersion
from app.schemas.scheme import CreateSchemeRequest, EligibilityCriteriaModel
from app.services.eligibility.validation import validate_rule
from app.services.schemes import known_scheme_ids, latest_rule, scheme_to_snapshot


def diff_dict(old: dict[str, Any], new: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for key in sorted(set(old) | set(new)):
        path = f"{prefix}.{key}" if prefix else key
        old_value = old.get(key)
        new_value = new.get(key)
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            changes.extend(diff_dict(old_value, new_value, path))
        elif old_value != new_value:
            changes.append({"path": path, "old": old_value, "new": new_value})
    return changes


async def validate_draft_payload(db: AsyncSession, actor: DashboardActor, payload: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    scheme_payload = payload.get("scheme") or {}
    rule_payload = payload.get("eligibility_rule") or scheme_payload.get("eligibility_rule") or {}
    try:
        criteria = EligibilityCriteriaModel.model_validate(rule_payload)
    except Exception as exc:
        return {"errors": [{"code": "RULE_INVALID", "field": "eligibility_rule", "message": str(exc)}], "warnings": []}
    known_ids = await known_scheme_ids(db, actor.organisation_id)
    scheme_id = scheme_payload.get("id")
    issues = validate_rule(criteria, known_ids - {scheme_id} if scheme_id else known_ids)
    return {
        "errors": [{"code": issue.code, "field": issue.field, "message": issue.message} for issue in issues],
        "warnings": [],
    }


async def create_scheme_draft(db: AsyncSession, actor: DashboardActor, payload: dict[str, Any], change_summary: str) -> dict[str, Any]:
    require_actor_permission(actor, "scheme:write")
    validation = await validate_draft_payload(db, actor, payload)
    if validation["errors"]:
        raise ApiError(422, "DRAFT_VALIDATION_FAILED", "Draft has validation errors.", "draft_payload", validation)
    scheme_id = (payload.get("scheme") or {}).get("id")
    draft = SchemeDraft(
        organisation_id=actor.organisation_id,
        scheme_id=scheme_id,
        draft_payload={**payload, "change_summary": change_summary},
        validation_result=validation,
        status="draft",
        created_by=actor.member_id,
    )
    db.add(draft)
    await db.flush()
    db.add(
        SchemeAuditLog(
            organisation_id=actor.organisation_id,
            scheme_id=scheme_id,
            draft_id=draft.id,
            action="create_draft",
            changed_by=actor.member_id,
            after_snapshot=payload,
            diff={},
            change_summary=change_summary,
        )
    )
    await db.commit()
    return {"draft_id": draft.id, "status": draft.status, "validation_result": validation}


async def preview_scheme_draft(db: AsyncSession, actor: DashboardActor, draft_id: UUID) -> dict[str, Any]:
    require_actor_permission(actor, "scheme:write")
    draft = await db.get(SchemeDraft, draft_id)
    if draft is None or draft.organisation_id != actor.organisation_id:
        raise ApiError(404, "DRAFT_NOT_FOUND", "Draft was not found.", "draft_id")
    validation = await validate_draft_payload(db, actor, draft.draft_payload)
    before: dict[str, Any] = {}
    if draft.scheme_id:
        scheme = await db.get(Scheme, draft.scheme_id)
        if scheme and scheme.organisation_id == actor.organisation_id:
            before["scheme"] = scheme_to_snapshot(scheme)
            before["eligibility_rule"] = (await latest_rule(db, actor.organisation_id, draft.scheme_id, active_only=False)).criteria
    diff = {
        "scheme": diff_dict(before.get("scheme", {}), draft.draft_payload.get("scheme", {})),
        "eligibility_rule": diff_dict(before.get("eligibility_rule", {}), draft.draft_payload.get("eligibility_rule", {})),
    }
    draft.status = "previewed"
    draft.validation_result = validation
    await db.commit()
    return {"validation_result": validation, "diff": diff, "sample_impact": {"profiles_tested": 0, "newly_eligible": 0, "newly_ineligible": 0}}


async def publish_scheme_draft(db: AsyncSession, actor: DashboardActor, draft_id: UUID) -> dict[str, Any]:
    require_actor_permission(actor, "scheme:publish")
    draft = await db.get(SchemeDraft, draft_id)
    if draft is None or draft.organisation_id != actor.organisation_id:
        raise ApiError(404, "DRAFT_NOT_FOUND", "Draft was not found.", "draft_id")
    if draft.status == "published":
        raise ApiError(409, "DRAFT_ALREADY_PUBLISHED", "Draft is already published.", "draft_id")
    validation = await validate_draft_payload(db, actor, draft.draft_payload)
    if validation["errors"]:
        raise ApiError(422, "DRAFT_VALIDATION_FAILED", "Publish is blocked by validation errors.", "draft_payload", validation)
    scheme_payload = dict(draft.draft_payload.get("scheme") or {})
    rule_payload = draft.draft_payload.get("eligibility_rule") or scheme_payload.pop("eligibility_rule", {})
    request = CreateSchemeRequest.model_validate({**scheme_payload, "organisation_id": str(actor.organisation_id), "eligibility_rule": rule_payload})
    scheme = await db.get(Scheme, request.id)
    before = scheme_to_snapshot(scheme) if scheme else None
    version = 1
    if scheme is None:
        scheme = Scheme(
            id=request.id,
            organisation_id=actor.organisation_id,
            category_id=None,
            name=request.name,
            description=request.description,
            plain_language_summary=request.plain_language_summary,
            ministry=request.ministry,
            state_code=request.state_code,
            benefit_type=request.benefit_type,
            benefit_amount=request.benefit_amount,
            application_url=request.application_url,
            is_active=True,
            status="active",
            valid_from=request.valid_from,
            valid_until=request.valid_until,
            source_url=request.source_url,
            external_source=request.external_source,
            external_id=request.external_id,
            verification_status=request.verification_status,
            source_last_checked_at=request.source_last_checked_at,
        )
        db.add(scheme)
    else:
        active_rule = await latest_rule(db, actor.organisation_id, scheme.id, active_only=False)
        version = active_rule.version + 1
        db.add(SchemeVersion(organisation_id=actor.organisation_id, scheme_id=scheme.id, version=version, scheme_snapshot=scheme_to_snapshot(scheme), rule_snapshot=active_rule.criteria, change_summary=draft.draft_payload.get("change_summary", "Scheme draft publish.")))
        for field in ["name", "description", "plain_language_summary", "ministry", "state_code", "benefit_type", "benefit_amount", "application_url", "valid_from", "valid_until", "source_url", "verification_status"]:
            setattr(scheme, field, getattr(request, field))
        scheme.status = "active"
        scheme.is_active = True
        await db.execute(update(EligibilityRule).where(EligibilityRule.organisation_id == actor.organisation_id, EligibilityRule.scheme_id == scheme.id).values(is_active=False))
    db.add(EligibilityRule(organisation_id=actor.organisation_id, scheme_id=scheme.id, version=version, criteria=request.eligibility_rule.model_dump(mode="json"), is_active=True))
    draft.status = "published"
    draft.validation_result = validation
    db.add(
        SchemeAuditLog(
            organisation_id=actor.organisation_id,
            scheme_id=scheme.id,
            draft_id=draft.id,
            action="publish",
            changed_by=actor.member_id,
            before_snapshot=before,
            after_snapshot={"scheme": scheme_to_snapshot(scheme), "eligibility_rule": request.eligibility_rule.model_dump(mode="json")},
            diff={},
            change_summary=draft.draft_payload.get("change_summary", "Scheme draft publish."),
        )
    )
    db.add(
        OperatorNotification(
            organisation_id=actor.organisation_id,
            state_code=scheme.state_code,
            notification_type="scheme_updated",
            title="Scheme updated",
            body=f"{scheme.name} was updated.",
            payload={"scheme_id": scheme.id},
        )
    )
    await db.commit()
    return {"draft_id": draft.id, "scheme_id": scheme.id, "status": "published", "validation_result": validation}
