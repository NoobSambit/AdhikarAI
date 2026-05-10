from fastapi import Header

from app.core.config import get_settings
from app.core.errors import ApiError


async def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != get_settings().admin_api_token:
        raise ApiError(
            status_code=401,
            code="ADMIN_TOKEN_INVALID",
            message="Admin token is invalid.",
            field="X-Admin-Token",
        )

