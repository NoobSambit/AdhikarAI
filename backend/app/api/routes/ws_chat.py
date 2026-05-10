from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.agent import ChatInputModel
from app.services.sessions.session_service import handle_chat_turn

router = APIRouter()


async def _db_session() -> AsyncSession:
    async for session in get_db():
        return session
    raise RuntimeError("Database session unavailable")


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, db: AsyncSession = Depends(_db_session)) -> None:
    await websocket.accept()
    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except ValueError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "Message format is not valid.",
                        "profile_completeness": 0,
                        "session_id": "",
                        "payload": {"code": "INVALID_JSON"},
                    }
                )
                await websocket.close(code=4400)
                return
            try:
                input_message = ChatInputModel.model_validate(raw)
            except ValidationError as exc:
                too_long = any(error.get("type") == "string_too_long" for error in exc.errors())
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "Please send a shorter message." if too_long else "Message format is not valid.",
                        "profile_completeness": 0,
                        "session_id": raw.get("session_id", "") if isinstance(raw, dict) else "",
                        "payload": {"code": "MESSAGE_TOO_LONG" if too_long else "INVALID_JSON"},
                    }
                )
                if not too_long:
                    await websocket.close(code=4400)
                    return
                continue
            output = await handle_chat_turn(input_message, db)
            await websocket.send_json(output.model_dump(mode="json"))
    except WebSocketDisconnect:
        return
