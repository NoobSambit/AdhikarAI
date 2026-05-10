from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import Household, Profile
from app.schemas.agent import HouseholdMemberProfileModel
from app.schemas.household import CreateHouseholdMemberRequest
from app.services.profiles import profile_to_schema


async def create_household_member(
    household_id: UUID, request: CreateHouseholdMemberRequest, db: AsyncSession
) -> HouseholdMemberProfileModel:
    household = await db.get(Household, household_id)
    if household is None or household.organisation_id != request.organisation_id:
        raise ApiError(404, "HOUSEHOLD_NOT_FOUND", "Household was not found.", "household_id")
    profile = Profile(
        organisation_id=request.organisation_id,
        household_id=household_id,
        display_name=request.display_name,
        relationship_to_primary=request.relationship_to_primary,
        age=request.age,
        gender=request.gender,
        caste_category=request.caste_category,
        annual_income=request.annual_income,
        land_holding_acres=request.land_holding_acres,
        occupation_type=request.occupation_type,
        marital_status=request.marital_status,
        state_code=request.state_code or household.state_code,
        district=request.district or household.district,
        existing_scheme_ids=request.existing_scheme_ids,
        custom_attributes=request.custom_attributes,
        profile_completeness=request.profile_completeness,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile_to_schema(profile)


async def delete_household_member(household_id: UUID, profile_id: UUID, organisation_id: UUID, db: AsyncSession) -> dict:
    result = await db.execute(
        delete(Profile).where(
            Profile.id == profile_id,
            Profile.household_id == household_id,
            Profile.organisation_id == organisation_id,
        )
    )
    if result.rowcount == 0:
        raise ApiError(404, "PROFILE_NOT_FOUND", "Profile was not found.", "profile_id")
    await db.commit()
    return {"deleted": True, "profile_id": str(profile_id)}
