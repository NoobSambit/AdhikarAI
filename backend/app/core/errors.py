from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.responses import ORJSONResponse


def new_request_id() -> str:
    return f"req_{uuid4().hex[:12].upper()}"


@dataclass(slots=True)
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    field: str | None = None
    details: Any | None = None


def error_body(error: ApiError, request_id: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": error.code,
            "message": error.message,
            "field": error.field,
            "request_id": request_id,
        }
    }
    if error.details is not None:
        payload["error"]["details"] = error.details
        if isinstance(error.details, dict) and "retry_after_seconds" in error.details:
            payload["error"]["retry_after_seconds"] = error.details["retry_after_seconds"]
    return payload


async def api_error_handler(request: Request, exc: ApiError) -> ORJSONResponse:
    request_id = getattr(request.state, "request_id", new_request_id())
    return ORJSONResponse(error_body(exc, request_id), status_code=exc.status_code)
