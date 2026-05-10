from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.agent import HouseholdMemberProfileModel
from app.schemas.household import CreateHouseholdMemberRequest
from app.services.households import create_household_member, delete_household_member

router = APIRouter()


@router.post("/households/{household_id}/members", response_model=HouseholdMemberProfileModel)
async def create_household_member_route(
    household_id: UUID, request: CreateHouseholdMemberRequest, db: AsyncSession = Depends(get_db)
) -> HouseholdMemberProfileModel:
    return await create_household_member(household_id, request, db)


@router.delete("/households/{household_id}/members/{profile_id}")
async def delete_household_member_route(
    household_id: UUID, profile_id: UUID, organisation_id: UUID, db: AsyncSession = Depends(get_db)
) -> dict:
    return await delete_household_member(household_id, profile_id, organisation_id, db)
