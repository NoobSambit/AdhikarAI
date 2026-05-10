from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.agent import PatchProfileRequest, PatchProfileResponse
from app.services.profiles import patch_profile

router = APIRouter()


@router.patch("/profile/{profile_id}", response_model=PatchProfileResponse)
async def patch_profile_route(profile_id: UUID, request: PatchProfileRequest, db: AsyncSession = Depends(get_db)) -> PatchProfileResponse:
    return await patch_profile(profile_id, request, db)
