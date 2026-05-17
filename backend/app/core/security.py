import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.dashboard.rbac import DashboardActor
from app.db.models import OrganisationMember, User
from app.db.session import get_db


async def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != get_settings().admin_api_token:
        raise ApiError(
            status_code=401,
            code="ADMIN_TOKEN_INVALID",
            message="Admin token is invalid.",
            field="X-Admin-Token",
        )


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64url(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_session_jwt(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "org": str(user.organisation_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.auth_jwt_ttl_seconds)).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.auth_jwt_secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def _sign_payload(payload: dict) -> str:
    settings = get_settings()
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.auth_jwt_secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def create_dashboard_session_jwt(member: OrganisationMember) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(member.user_id or member.admin_user_id),
        "member_id": str(member.id),
        "org": str(member.organisation_id),
        "role": member.role,
        "typ": "dashboard",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.auth_jwt_ttl_seconds)).timestamp()),
    }
    return _sign_payload(payload)


def decode_session_jwt(token: str) -> dict:
    settings = get_settings()
    try:
        header_payload, signature = token.rsplit(".", 1)
        expected = _b64url(hmac.new(settings.auth_jwt_secret.encode(), header_payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        payload = json.loads(_unb64url(header_payload.split(".", 1)[1]))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError
        return payload
    except Exception as exc:
        raise ApiError(401, "NOT_AUTHENTICATED", "Please login with phone to continue.", "session") from exc


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str, challenge_id: str) -> str:
    settings = get_settings()
    salt = f"{challenge_id}:{settings.auth_jwt_secret}".encode()
    digest = hashlib.pbkdf2_hmac("sha256", otp.encode(), salt, 120_000)
    return _b64url(digest)


def verify_otp_hash(otp: str, challenge_id: str, otp_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(otp, challenge_id), otp_hash)


async def require_user(
    token: str | None = Cookie(default=None, alias=get_settings().auth_cookie_name),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise ApiError(401, "NOT_AUTHENTICATED", "Please login with phone to continue.", "session")
    payload = decode_session_jwt(token)
    user = await db.get(User, UUID(payload["sub"]))
    if user is None or user.deleted_at is not None:
        raise ApiError(401, "NOT_AUTHENTICATED", "Please login with phone to continue.", "session")
    return user


async def require_dashboard_actor(
    token: str | None = Cookie(default=None, alias=get_settings().auth_cookie_name),
    db: AsyncSession = Depends(get_db),
) -> DashboardActor:
    if not token:
        raise ApiError(401, "NOT_AUTHENTICATED", "Please login to continue.", "session")
    payload = decode_session_jwt(token)
    if payload.get("typ") != "dashboard" or not payload.get("member_id"):
        raise ApiError(401, "DASHBOARD_SESSION_REQUIRED", "Please login to the dashboard.", "session")
    member = await db.get(OrganisationMember, UUID(payload["member_id"]))
    if member is None or not member.is_active:
        raise ApiError(401, "DASHBOARD_SESSION_REQUIRED", "Please login to the dashboard.", "session")
    return DashboardActor(
        user_id=UUID(payload["sub"]),
        member_id=member.id,
        organisation_id=member.organisation_id,
        role=member.role,
        display_name=member.display_name,
    )
