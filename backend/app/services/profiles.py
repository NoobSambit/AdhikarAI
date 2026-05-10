from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.completeness import compute_profile_completeness
from app.core.errors import ApiError, new_request_id
from app.db.models import Profile, ProfileEvent
from app.schemas.agent import HouseholdMemberProfileModel, PatchProfileRequest, PatchProfileResponse
from app.schemas.profile import MatchProfileRequest, UserProfileInputModel
from app.services.eligibility.matcher import match_profile
from app.services.schemes import active_scheme_rules

PATCHABLE_FIELDS = {
    "display_name",
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


def profile_to_schema(profile: Profile) -> HouseholdMemberProfileModel:
    return HouseholdMemberProfileModel(
        id=str(profile.id),
        display_name=profile.display_name,
        relationship_to_primary=profile.relationship_to_primary,
        age=profile.age,
        gender=profile.gender,
        caste_category=profile.caste_category,
        annual_income=profile.annual_income,
        land_holding_acres=float(profile.land_holding_acres) if profile.land_holding_acres is not None else None,
        occupation_type=profile.occupation_type,
        marital_status=profile.marital_status,
        state_code=profile.state_code,
        district=profile.district,
        existing_scheme_ids=profile.existing_scheme_ids or [],
        custom_attributes=profile.custom_attributes or {},
        profile_completeness=profile.profile_completeness,
    )


def _profile_payload(profile: Profile) -> dict:
    return profile_to_schema(profile).model_dump(mode="json")


async def patch_profile(profile_id: UUID, request: PatchProfileRequest, db: AsyncSession) -> PatchProfileResponse:
    profile = await db.get(Profile, profile_id)
    if profile is None or profile.organisation_id != request.organisation_id:
        raise ApiError(404, "PROFILE_NOT_FOUND", "Profile was not found.", "profile_id")

    unknown = sorted(set(request.fields) - PATCHABLE_FIELDS)
    if unknown:
        raise ApiError(422, "INVALID_PROFILE_PATCH", "Profile patch contains an unsupported field.", unknown[0])

    previous: dict = {}
    new_values: dict = {}
    changed: list[str] = []
    for field, value in request.fields.items():
        old = getattr(profile, field)
        if field == "custom_attributes" and isinstance(value, dict):
            merged = {**(old or {}), **value}
            value = merged
        if old != value:
            previous[field] = jsonable_encoder(old)
            new_values[field] = value
            changed.append(field)
            setattr(profile, field, value)

    rules = [item.rule for item in await active_scheme_rules(db, str(request.organisation_id))]
    payload = _profile_payload(profile)
    profile.profile_completeness = compute_profile_completeness(payload, rules)
    payload["profile_completeness"] = profile.profile_completeness
    match_result = await match_profile(
        MatchProfileRequest(
            organisation_id=str(request.organisation_id),
            profile=UserProfileInputModel(
                age=profile.age,
                gender=profile.gender,
                caste_category=profile.caste_category,
                annual_income=profile.annual_income,
                land_holding_acres=float(profile.land_holding_acres) if profile.land_holding_acres is not None else None,
                occupation_type=profile.occupation_type,
                marital_status=profile.marital_status,
                state_code=profile.state_code,
                district=profile.district,
                existing_scheme_ids=profile.existing_scheme_ids or [],
                custom_attributes=profile.custom_attributes or {},
            ),
            include_incomplete=True,
            limit=10,
        ),
        db,
        new_request_id(),
    )
    snapshot = match_result.model_dump(mode="json")
    profile.last_match_snapshot = snapshot
    if changed:
        db.add(
            ProfileEvent(
                organisation_id=request.organisation_id,
                profile_id=profile.id,
                event_type="profile_update",
                source=request.source,
                changed_fields={field: True for field in changed},
                previous_values=previous,
                new_values=new_values,
            )
        )
    await db.commit()
    await db.refresh(profile)
    return PatchProfileResponse(
        profile=profile_to_schema(profile),
        changed_fields=changed,
        profile_completeness=profile.profile_completeness,
        match_snapshot=snapshot,
    )
