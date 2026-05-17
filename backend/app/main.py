from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from app.api.routes import (
    admin_index,
    admin_ingestion,
    admin_schemes,
    agent_sessions,
    document_check,
    health,
    households,
    phase4,
    profile_match,
    profiles,
    schemes,
    translate,
    tts,
    voice,
    ws_chat,
)
from app.core.config import get_settings
from app.core.errors import ApiError, api_error_handler, new_request_id
from app.services.jobs.scheduler import build_scheduler


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AdhikarAI API", version="phase-4")
    app.add_exception_handler(ApiError, api_error_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
        request_id = getattr(request.state, "request_id", new_request_id())
        first = exc.errors()[0] if exc.errors() else {"loc": ["body"], "msg": "Invalid request."}
        return ORJSONResponse(
            {
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": first["msg"],
                    "field": ".".join(str(part) for part in first["loc"]),
                    "request_id": request_id,
                }
            },
            status_code=422,
        )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(health.router)
    app.include_router(agent_sessions.router)
    app.include_router(ws_chat.router)
    app.include_router(profiles.router)
    app.include_router(households.router)
    app.include_router(document_check.router)
    app.include_router(profile_match.router)
    app.include_router(schemes.router)
    app.include_router(admin_schemes.router)
    app.include_router(admin_ingestion.router)
    app.include_router(admin_index.router)
    app.include_router(voice.router)
    app.include_router(translate.router)
    app.include_router(tts.router)
    app.include_router(phase4.router)

    if settings.enable_scheduler:
        scheduler = build_scheduler()

        @app.on_event("startup")
        async def start_scheduler() -> None:
            if not scheduler.running:
                scheduler.start()

        @app.on_event("shutdown")
        async def stop_scheduler() -> None:
            if scheduler.running:
                scheduler.shutdown()

    return app


app = create_app()
