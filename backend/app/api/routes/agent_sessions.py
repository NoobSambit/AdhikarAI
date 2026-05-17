from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.rate_limit.service import check_guest_limit
from app.schemas.agent import ChatInputModel, ChatOutputModel, CreateSessionRequest, CreateSessionResponse
from app.services.sessions.session_service import get_or_create_session, get_session_state, handle_chat_turn

router = APIRouter()


@router.post("/agent/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_agent_session(request: CreateSessionRequest, db: AsyncSession = Depends(get_db)) -> CreateSessionResponse:
    return await get_or_create_session(request, db)


@router.get("/agent/sessions/{session_id}")
async def get_agent_session(session_id: str, organisation_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    return await get_session_state(session_id, organisation_id, db)


@router.post("/agent/message", response_model=ChatOutputModel)
async def post_agent_message(request: ChatInputModel, db: AsyncSession = Depends(get_db)) -> ChatOutputModel:
    if request.organisation_id is not None:
        await check_guest_limit(request.organisation_id, request.session_id)
    return await handle_chat_turn(request, db)
