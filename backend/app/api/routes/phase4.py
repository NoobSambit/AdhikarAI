from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_session_jwt, require_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.phase4 import (
    AadhaarPrefillStartRequest,
    AadhaarPrefillStartResponse,
    ActionPlanRequest,
    ActionPlanResponse,
    ApplicationStatusResponse,
    AuthUserModel,
    ChecklistResponse,
    DigiLockerCallbackResponse,
    DigiLockerStartRequest,
    DigiLockerStartResponse,
    MeResponse,
    OfflineSyncRequest,
    OfflineSyncResponse,
    PushSubscriptionRequest,
    PushSubscriptionResponse,
    SaveSchemeRequest,
    SaveSchemeResponse,
    SendOtpRequest,
    SendOtpResponse,
    UpdateApplicationStatusRequest,
    UpdateChecklistRequest,
    UpdateProfileSettingsRequest,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from app.services import phase4

router = APIRouter()


def _auth_user(user: User) -> AuthUserModel:
    return AuthUserModel(
        id=user.id,
        phone_e164=user.phone_e164,
        language_code=user.language_code,
        primary_profile_id=user.primary_profile_id,
        high_contrast_enabled=user.high_contrast_enabled,
        font_size=user.font_size,
        notification_opt_in=user.notification_opt_in,
    )


@router.post("/auth/send-otp", response_model=SendOtpResponse)
async def post_send_otp(request: SendOtpRequest, db: AsyncSession = Depends(get_db)) -> SendOtpResponse:
    return await phase4.send_otp(request, db)


@router.post("/auth/verify-otp", response_model=VerifyOtpResponse)
async def post_verify_otp(request: VerifyOtpRequest, response: Response, db: AsyncSession = Depends(get_db)) -> VerifyOtpResponse:
    user, migrated = await phase4.verify_otp(request, db)
    settings = get_settings()
    response.set_cookie(
        settings.auth_cookie_name,
        create_session_jwt(user),
        max_age=settings.auth_jwt_ttl_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    return VerifyOtpResponse(user=_auth_user(user), migrated_guest_profile=migrated)


@router.get("/me", response_model=MeResponse)
async def get_me(user: User = Depends(require_user)) -> MeResponse:
    return MeResponse(user=_auth_user(user), primary_profile={"id": str(user.primary_profile_id)} if user.primary_profile_id else None)


@router.patch("/me", response_model=MeResponse)
async def patch_me(request: UpdateProfileSettingsRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> MeResponse:
    if request.language_code is not None:
        user.language_code = request.language_code
    if request.high_contrast_enabled is not None:
        user.high_contrast_enabled = request.high_contrast_enabled
    if request.font_size is not None:
        user.font_size = request.font_size
    if request.notification_opt_in is not None:
        user.notification_opt_in = request.notification_opt_in
    if request.guest_profile_id:
        await phase4.mark_guest_migration(db, user, request.guest_profile_id)
    await db.commit()
    await db.refresh(user)
    return MeResponse(user=_auth_user(user), primary_profile={"id": str(user.primary_profile_id)} if user.primary_profile_id else None)


@router.delete("/me")
async def delete_me(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    return await phase4.delete_account(user, db)


@router.post("/saved-schemes", response_model=SaveSchemeResponse)
async def post_saved_scheme(request: SaveSchemeRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> SaveSchemeResponse:
    return await phase4.save_scheme(user, request.profile_id, request.scheme_id, db)


@router.delete("/saved-schemes/{scheme_id}")
async def delete_saved_scheme(scheme_id: str, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    return await phase4.delete_saved_scheme(user, scheme_id, db)


@router.patch("/checklists", response_model=ChecklistResponse)
async def patch_checklists(request: UpdateChecklistRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> ChecklistResponse:
    return await phase4.update_checklist(user, request, db)


@router.post("/digilocker/start", response_model=DigiLockerStartResponse)
async def post_digilocker_start(request: DigiLockerStartRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await phase4.start_digilocker(user, request, db)


@router.get("/digilocker/callback", response_model=DigiLockerCallbackResponse)
async def get_digilocker_callback(profile_id: UUID, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await phase4.finish_digilocker(user, profile_id, db)


@router.post("/aadhaar/prefill/start", response_model=AadhaarPrefillStartResponse)
async def post_aadhaar_prefill_start(request: AadhaarPrefillStartRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await phase4.start_aadhaar_prefill(user, request, db)


@router.patch("/application-status", response_model=ApplicationStatusResponse)
async def patch_application_status(
    request: UpdateApplicationStatusRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationStatusResponse:
    return await phase4.update_application_status(user, request, db)


@router.post("/notifications/subscribe", response_model=PushSubscriptionResponse)
async def post_notifications_subscribe(request: PushSubscriptionRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    return await phase4.subscribe_notifications(user, request, db)


@router.post("/action-plans", response_model=ActionPlanResponse)
async def post_action_plans(request: ActionPlanRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> ActionPlanResponse:
    return await phase4.create_action_plan(user, request, db)


@router.post("/offline-sync", response_model=OfflineSyncResponse)
async def post_offline_sync(request: OfflineSyncRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)) -> OfflineSyncResponse:
    return OfflineSyncResponse(results=await phase4.process_offline_sync(user, request.events, db))
