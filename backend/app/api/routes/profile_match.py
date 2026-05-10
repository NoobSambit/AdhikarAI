from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.match import MatchProfileResponse
from app.schemas.profile import MatchProfileRequest
from app.services.eligibility.matcher import match_profile

router = APIRouter()


@router.post("/profile/match", response_model=MatchProfileResponse)
async def profile_match(request_body: MatchProfileRequest, request: Request, db: AsyncSession = Depends(get_db)) -> MatchProfileResponse:
    return await match_profile(request_body, db, request.state.request_id)

