from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    request_id: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ListResponse(BaseModel):
    items: list[Any]
    limit: int
    offset: int
    total: int

