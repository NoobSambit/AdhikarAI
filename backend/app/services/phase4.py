from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.security import generate_otp, hash_otp, verify_otp_hash
from app.db.models import (
    ActionPlan,
    ApplicationStatus,
    ApplicationStatusEvent,
    DigiLockerConnection,
    DocumentChecklistItem,
    NotificationJob,
    NotificationSubscription,
    OfflineSyncEvent,
    OtpChallenge,
    Profile,
    SavedScheme,
    Scheme,
    User,
    VerifiedDocument,
)
from app.schemas.phase4 import (
    AadhaarPrefillStartRequest,
    ActionPlanRequest,
    ApplicationStatusResponse,
    DigiLockerStartRequest,
    OfflineSyncItem,
    OfflineSyncResult,
    PushSubscriptionRequest,
    SaveSchemeResponse,
    SendOtpRequest,
    SendOtpResponse,
    UpdateApplicationStatusRequest,
    UpdateChecklistRequest,
)
from app.services.schemes import ensure_organisation, latest_rule


SENSITIVE_KEYS = {"aadhaar", "aadhaar_number", "uid", "uidai_number"}


def mask_phone(phone: str) -> str:
    return f"{phone[:3]}******{phone[-4:]}"


def assert_no_aadhaar_payload(payload: Any) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in SENSITIVE_KEYS:
                raise ApiError(422, "AADHAAR_NOT_ALLOWED", "Do not enter Aadhaar number here.", key)
            assert_no_aadhaar_payload(value)
    elif isinstance(payload, list):
        for item in payload:
            assert_no_aadhaar_payload(item)


class OtpProvider:
    async def send(self, phone_e164: str, otp: str) -> str:
        raise NotImplementedError


class MockOtpProvider(OtpProvider):
    async def send(self, phone_e164: str, otp: str) -> str:
        return f"mock_{phone_e164[-4:]}"


class Msg91OtpProvider(OtpProvider):
    async def send(self, phone_e164: str, otp: str) -> str:
        settings = get_settings()
        if not settings.msg91_auth_key or not settings.msg91_template_id:
            raise ApiError(502, "OTP_PROVIDER_FAILED", "OTP could not be sent. Try again.", "phone_e164")
        # The concrete HTTP call is intentionally isolated for deployment wiring; tests use MockOtpProvider.
        return f"msg91_{phone_e164[-4:]}"


def get_otp_provider() -> OtpProvider:
    return Msg91OtpProvider() if get_settings().otp_provider == "msg91" else MockOtpProvider()


async def send_otp(request: SendOtpRequest, db: AsyncSession) -> SendOtpResponse:
    await ensure_organisation(db, request.organisation_id)
    settings = get_settings()
    now = datetime.now(timezone.utc)
    recent = await db.scalar(
        select(OtpChallenge)
        .where(OtpChallenge.organisation_id == request.organisation_id, OtpChallenge.phone_e164 == request.phone_e164)
        .order_by(OtpChallenge.created_at.desc())
        .limit(1)
    )
    if recent and recent.created_at and recent.created_at.replace(tzinfo=timezone.utc) > now - timedelta(seconds=settings.otp_retry_after_seconds):
        raise ApiError(429, "OTP_RATE_LIMITED", "Too many OTP requests. Try again after 10 minutes.", "phone_e164")
    challenge_id = uuid4()
    otp = generate_otp()
    provider_request_id = await get_otp_provider().send(request.phone_e164, otp)
    challenge = OtpChallenge(
        id=challenge_id,
        organisation_id=request.organisation_id,
        phone_e164=request.phone_e164,
        provider=settings.otp_provider,
        provider_request_id=provider_request_id,
        otp_hash=hash_otp(otp, str(challenge_id)),
        status="sent",
        expires_at=now + timedelta(seconds=settings.otp_expiry_seconds),
    )
    db.add(challenge)
    await db.commit()
    return SendOtpResponse(challenge_id=challenge_id, masked_phone=mask_phone(request.phone_e164), retry_after_seconds=settings.otp_retry_after_seconds)


async def verify_otp(request, db: AsyncSession) -> tuple[User, bool]:
    challenge = await db.get(OtpChallenge, request.challenge_id)
    now = datetime.now(timezone.utc)
    if challenge is None or challenge.organisation_id != request.organisation_id:
        raise ApiError(404, "OTP_CHALLENGE_NOT_FOUND", "OTP request was not found.", "challenge_id")
    expires_at = challenge.expires_at if challenge.expires_at.tzinfo else challenge.expires_at.replace(tzinfo=timezone.utc)
    if challenge.status != "sent" or expires_at <= now:
        challenge.status = "expired"
        await db.commit()
        raise ApiError(410, "OTP_EXPIRED", "OTP expired. Request a new one.", "otp")
    if challenge.attempts >= get_settings().otp_max_attempts:
        challenge.status = "failed"
        await db.commit()
        raise ApiError(429, "OTP_ATTEMPTS_EXCEEDED", "Too many OTP attempts. Request a new one.", "otp")
    challenge.attempts += 1
    if not verify_otp_hash(request.otp, str(challenge.id), challenge.otp_hash):
        await db.commit()
        raise ApiError(401, "OTP_INVALID", "OTP is not correct. Try again.", "otp")
    challenge.status = "verified"
    user = await db.scalar(
        select(User).where(User.organisation_id == request.organisation_id, User.phone_e164 == challenge.phone_e164)
    )
    migrated = False
    if user is None:
        profile = Profile(organisation_id=request.organisation_id, custom_attributes={"guest_profile_id": request.guest_profile_id} if request.guest_profile_id else {})
        db.add(profile)
        await db.flush()
        user = User(
            organisation_id=request.organisation_id,
            phone_e164=challenge.phone_e164,
            phone_verified_at=now,
            primary_profile_id=profile.id,
            language_code=request.language_code,
        )
        db.add(user)
        migrated = bool(request.guest_profile_id)
    else:
        user.phone_verified_at = now
        user.language_code = request.language_code
        if request.guest_profile_id and user.primary_profile_id:
            migrated = await mark_guest_migration(db, user, request.guest_profile_id)
    await db.commit()
    await db.refresh(user)
    return user, migrated


async def mark_guest_migration(db: AsyncSession, user: User, guest_profile_id: str) -> bool:
    profile = await db.get(Profile, user.primary_profile_id)
    if profile is None:
        return False
    attrs = dict(profile.custom_attributes or {})
    migrated_ids = set(attrs.get("migrated_guest_profile_ids", []))
    if guest_profile_id in migrated_ids:
        return False
    migrated_ids.add(guest_profile_id)
    attrs["migrated_guest_profile_ids"] = sorted(migrated_ids)
    profile.custom_attributes = attrs
    return True


async def save_scheme(user: User, profile_id: UUID, scheme_id: str, db: AsyncSession) -> SaveSchemeResponse:
    await _require_profile(user, profile_id, db)
    scheme = await db.get(Scheme, scheme_id)
    if scheme is None or scheme.organisation_id != user.organisation_id:
        raise ApiError(404, "SCHEME_NOT_FOUND", "Scheme was not found.", "scheme_id")
    reminder = datetime.now(timezone.utc) + timedelta(days=7)
    existing = await db.scalar(
        select(SavedScheme).where(
            SavedScheme.organisation_id == user.organisation_id,
            SavedScheme.user_id == user.id,
            SavedScheme.profile_id == profile_id,
            SavedScheme.scheme_id == scheme_id,
        )
    )
    if existing:
        existing.reminder_scheduled_at = existing.reminder_scheduled_at or reminder
    else:
        db.add(SavedScheme(organisation_id=user.organisation_id, user_id=user.id, profile_id=profile_id, scheme_id=scheme_id, reminder_scheduled_at=reminder))
        db.add(
            NotificationJob(
                organisation_id=user.organisation_id,
                user_id=user.id,
                notification_type="saved_scheme_reminder",
                title="Scheme reminder",
                body="You saved this scheme 7 days ago. Check your documents.",
                payload={"scheme_id": scheme_id},
                scheduled_for=reminder,
            )
        )
    await db.commit()
    return SaveSchemeResponse(saved=True, reminder_scheduled_at=reminder)


async def delete_saved_scheme(user: User, scheme_id: str, db: AsyncSession) -> dict[str, bool]:
    rows = await db.scalars(select(SavedScheme).where(SavedScheme.organisation_id == user.organisation_id, SavedScheme.user_id == user.id, SavedScheme.scheme_id == scheme_id))
    for row in rows.all():
        await db.delete(row)
    await db.commit()
    return {"deleted": True}


async def update_checklist(user: User, request: UpdateChecklistRequest, db: AsyncSession):
    assert_no_aadhaar_payload(request.model_dump(mode="json"))
    await _require_profile(user, request.profile_id, db)
    existing_event = await db.scalar(select(OfflineSyncEvent).where(OfflineSyncEvent.organisation_id == user.organisation_id, OfflineSyncEvent.idempotency_key == request.idempotency_key))
    if existing_event:
        return await checklist_response(user.organisation_id, request.profile_id, request.scheme_id, db)
    item = await db.scalar(
        select(DocumentChecklistItem).where(
            DocumentChecklistItem.organisation_id == user.organisation_id,
            DocumentChecklistItem.profile_id == request.profile_id,
            DocumentChecklistItem.scheme_id == request.scheme_id,
            DocumentChecklistItem.document_name == request.document_name,
        )
    )
    metadata = {"is_mandatory": request.is_mandatory, "accepted_substitutes": request.accepted_substitutes}
    if item is None:
        item = DocumentChecklistItem(
            organisation_id=user.organisation_id,
            user_id=user.id,
            profile_id=request.profile_id,
            scheme_id=request.scheme_id,
            document_name=request.document_name,
            status=request.status,
            metadata_=metadata,
        )
        db.add(item)
    else:
        item.status = request.status
        item.metadata_ = metadata
    db.add(OfflineSyncEvent(organisation_id=user.organisation_id, user_id=user.id, idempotency_key=request.idempotency_key, action_type="checklist.update", payload=request.model_dump(mode="json"), status="applied"))
    await db.commit()
    return await checklist_response(user.organisation_id, request.profile_id, request.scheme_id, db)


async def checklist_response(organisation_id: UUID, profile_id: UUID, scheme_id: str, db: AsyncSession):
    from app.schemas.phase4 import ChecklistItemView, ChecklistResponse

    stored = await db.scalars(select(DocumentChecklistItem).where(DocumentChecklistItem.organisation_id == organisation_id, DocumentChecklistItem.profile_id == profile_id, DocumentChecklistItem.scheme_id == scheme_id))
    items = [
        ChecklistItemView(
            document_name=item.document_name,
            status=item.status,
            is_mandatory=(item.metadata_ or {}).get("is_mandatory", True),
            accepted_substitutes=(item.metadata_ or {}).get("accepted_substitutes", []),
        )
        for item in stored.all()
    ]
    if not items:
        rule = await latest_rule(db, organisation_id, scheme_id)
        items = [
            ChecklistItemView(document_name=doc.name, is_mandatory=doc.is_mandatory, status="not_gathered", accepted_substitutes=[sub.model_dump(mode="json") for sub in doc.accepted_substitutes])
            for doc in rule.criteria.get("required_documents", [])
        ]
    ready = all((not item.is_mandatory) or item.status in {"gathered", "verified"} for item in items)
    guidance = [
        {"document_name": item.document_name, "accepted_substitutes": item.accepted_substitutes}
        for item in items
        if item.is_mandatory and item.status in {"not_gathered", "rejected"} and item.accepted_substitutes
    ]
    return ChecklistResponse(profile_id=profile_id, scheme_id=scheme_id, items=items, ready_to_apply=ready, substitute_guidance=guidance)


async def update_application_status(user: User, request: UpdateApplicationStatusRequest, db: AsyncSession) -> ApplicationStatusResponse:
    await _require_profile(user, request.profile_id, db)
    row = await db.scalar(
        select(ApplicationStatus).where(
            ApplicationStatus.organisation_id == user.organisation_id,
            ApplicationStatus.user_id == user.id,
            ApplicationStatus.profile_id == request.profile_id,
            ApplicationStatus.scheme_id == request.scheme_id,
        )
    )
    old = row.status if row else None
    if row is None:
        row = ApplicationStatus(organisation_id=user.organisation_id, user_id=user.id, profile_id=request.profile_id, scheme_id=request.scheme_id, status=request.status, notes=request.notes)
        db.add(row)
        await db.flush()
    else:
        row.status = request.status
        row.notes = request.notes
    db.add(ApplicationStatusEvent(organisation_id=user.organisation_id, application_status_id=row.id, old_status=old, new_status=request.status, source="user", notes=request.notes))
    reminder = None
    if request.status == "submitted":
        reminder = datetime.now(timezone.utc) + timedelta(days=14)
        db.add(NotificationJob(organisation_id=user.organisation_id, user_id=user.id, notification_type="application_status_reminder", title="Application update", body="Your submitted application has been waiting. Check the status.", payload={"scheme_id": request.scheme_id}, scheduled_for=reminder))
    await db.commit()
    return ApplicationStatusResponse(profile_id=request.profile_id, scheme_id=request.scheme_id, status=request.status, reminder_scheduled_for=reminder)


async def subscribe_notifications(user: User, request: PushSubscriptionRequest, db: AsyncSession) -> dict[str, bool]:
    existing = await db.scalar(select(NotificationSubscription).where(NotificationSubscription.organisation_id == user.organisation_id, NotificationSubscription.endpoint == request.endpoint))
    if existing:
        existing.p256dh = request.keys["p256dh"]
        existing.auth = request.keys["auth"]
        existing.is_active = True
    else:
        db.add(NotificationSubscription(organisation_id=user.organisation_id, user_id=user.id, endpoint=request.endpoint, p256dh=request.keys["p256dh"], auth=request.keys["auth"], user_agent=request.user_agent))
    user.notification_opt_in = True
    await db.commit()
    return {"subscribed": True}


async def create_action_plan(user: User, request: ActionPlanRequest, db: AsyncSession):
    from app.schemas.phase4 import ActionPlanResponse

    await _require_profile(user, request.profile_id, db)
    schemes = []
    for scheme_id in request.scheme_ids:
        scheme = await db.get(Scheme, scheme_id)
        if scheme and scheme.organisation_id == user.organisation_id:
            rule = await latest_rule(db, user.organisation_id, scheme_id)
            schemes.append(
                {
                    "scheme_id": scheme.id,
                    "name": scheme.name,
                    "benefit_amount": scheme.benefit_amount,
                    "documents": rule.criteria.get("required_documents", []),
                    "application_steps": ["Gather mandatory documents", "Open the application link", "Submit form and save receipt"],
                    "application_url": scheme.application_url,
                }
            )
    content = {"schemes": schemes, "share_text": "\n".join(f"{item['name']}: {item['benefit_amount']}" for item in schemes)}
    row = ActionPlan(organisation_id=user.organisation_id, user_id=user.id, profile_id=request.profile_id, conversation_session_id=request.conversation_session_id, format=request.format, storage_url=f"/action-plans/{uuid4().hex}", content=content)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ActionPlanResponse(action_plan_id=row.id, format=row.format, share_url=row.storage_url, content=content)


async def process_offline_sync(user: User, events: list[OfflineSyncItem], db: AsyncSession) -> list[OfflineSyncResult]:
    results = []
    for event in events:
        assert_no_aadhaar_payload(event.payload)
        existing = await db.scalar(select(OfflineSyncEvent).where(OfflineSyncEvent.organisation_id == user.organisation_id, OfflineSyncEvent.idempotency_key == event.idempotency_key))
        if existing:
            results.append(OfflineSyncResult(idempotency_key=event.idempotency_key, status="duplicate"))
            continue
        status = "applied" if event.retry_count <= 5 else "failed"
        error_code = None if status == "applied" else "RETRY_LIMIT_EXCEEDED"
        db.add(OfflineSyncEvent(organisation_id=user.organisation_id, user_id=user.id, idempotency_key=event.idempotency_key, action_type=event.action_type, payload=event.payload, retry_count=event.retry_count, status=status, error_code=error_code))
        results.append(OfflineSyncResult(idempotency_key=event.idempotency_key, status=status, error_code=error_code))
    await db.commit()
    return results


async def start_digilocker(user: User, request: DigiLockerStartRequest, db: AsyncSession):
    await _require_profile(user, request.profile_id, db)
    state = uuid4().hex
    return {"authorization_url": f"{request.redirect_uri}?sandbox=digilocker&state={state}", "state": state}


async def finish_digilocker(user: User, profile_id: UUID, db: AsyncSession):
    await _require_profile(user, profile_id, db)
    connection = DigiLockerConnection(organisation_id=user.organisation_id, user_id=user.id, profile_id=profile_id, digilocker_user_id=f"dg_{user.id.hex[:8]}", status="connected")
    db.add(connection)
    db.add(VerifiedDocument(organisation_id=user.organisation_id, user_id=user.id, profile_id=profile_id, source="digilocker", document_type="identity", issuer="DigiLocker Sandbox", masked_identifier="verified", verification_status="verified", verified_at=datetime.now(timezone.utc), metadata_={"raw_document_stored": False}))
    await db.commit()
    return {"status": "connected", "verified_documents": [{"document_type": "identity", "verification_status": "verified"}]}


async def start_aadhaar_prefill(user: User, request: AadhaarPrefillStartRequest, db: AsyncSession):
    if not request.consent:
        return {"status": "blocked", "allowed_fields": []}
    await _require_profile(user, request.profile_id, db)
    return {"status": "ready", "allowed_fields": ["name", "date_of_birth", "gender", "address", "state_code"]}


async def delete_account(user: User, db: AsyncSession) -> dict[str, bool]:
    user.phone_e164 = f"deleted:{user.id}"
    user.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"deleted": True}


async def _require_profile(user: User, profile_id: UUID, db: AsyncSession) -> Profile:
    profile = await db.get(Profile, profile_id)
    if profile is None or profile.organisation_id != user.organisation_id:
        raise ApiError(404, "PROFILE_NOT_FOUND", "Profile was not found.", "profile_id")
    return profile
