from uuid import UUID, uuid4

import pytest
from fastapi import Response

from app.api.routes import dashboard
from app.api.routes.admin_panel import scheme_history
from app.core.errors import ApiError
from app.core.security import clear_auth_cookie, create_dashboard_session_jwt, decode_session_jwt, set_auth_cookie
from app.db.models import OrganisationMember


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_dashboard_session_uses_idle_timeout(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", "local-test-secret-for-dashboard-auth-123")
    monkeypatch.setenv("DASHBOARD_SESSION_IDLE_TIMEOUT_SECONDS", "60")
    from app.core.config import get_settings

    get_settings.cache_clear()
    member = OrganisationMember(
        id=uuid4(),
        organisation_id=ORG_ID,
        admin_user_id=uuid4(),
        role="operator",
        email="operator.local@example.test",
        display_name="Local Operator",
        is_active=True,
    )

    payload = decode_session_jwt(create_dashboard_session_jwt(member))

    assert payload["typ"] == "dashboard"
    assert payload["member_id"] == str(member.id)
    assert 0 < payload["exp"] - payload["iat"] <= 60
    get_settings.cache_clear()


def test_dashboard_cookie_helpers_set_and_clear_matching_cookie(monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_NAME", "adhikarai_session")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "none")
    monkeypatch.setenv("AUTH_COOKIE_DOMAIN", ".example.test")
    from app.core.config import get_settings

    get_settings.cache_clear()
    response = Response()
    set_auth_cookie(response, "header.payload.signature", 3600)
    header = response.headers["set-cookie"]

    assert "adhikarai_session=header.payload.signature" in header
    assert "HttpOnly" in header
    assert "Max-Age=3600" in header
    assert "Path=/" in header
    assert "SameSite=none" in header
    assert "Secure" in header
    assert "Domain=.example.test" in header

    logout_response = Response()
    clear_auth_cookie(logout_response)
    logout_header = logout_response.headers["set-cookie"]
    assert "adhikarai_session=" in logout_header
    assert "Max-Age=0" in logout_header
    assert "Path=/" in logout_header
    assert "Domain=.example.test" in logout_header
    get_settings.cache_clear()


def test_dev_dashboard_login_guard_accepts_only_configured_local_code(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("DASHBOARD_AUTH_PROVIDER", "dev")
    monkeypatch.setenv("DASHBOARD_DEV_LOGIN_ENABLED", "true")
    monkeypatch.setenv("DASHBOARD_DEV_LOGIN_CODE", "local-e2e-login")
    from app.core.config import get_settings

    get_settings.cache_clear()
    dashboard._assert_dev_dashboard_login_enabled("local-e2e-login")

    with pytest.raises(ApiError) as exc:
        dashboard._assert_dev_dashboard_login_enabled("wrong")

    assert exc.value.code == "DASHBOARD_INVALID_CREDENTIALS"
    get_settings.cache_clear()


def test_disabled_dashboard_login_returns_not_configured(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("DASHBOARD_AUTH_PROVIDER", "disabled")
    from app.core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(ApiError) as exc:
        dashboard._assert_dev_dashboard_login_enabled("anything")

    assert exc.value.code == "DASHBOARD_AUTH_NOT_CONFIGURED"
    get_settings.cache_clear()


def test_local_e2e_helper_refuses_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LOCAL_E2E_HELPERS_ENABLED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", "production-secret-with-more-than-32-chars")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://prod:prod@db.example.test:5432/adhikarai")
    monkeypatch.setenv("DATABASE_DIRECT_URL", "postgresql+asyncpg://prod:prod@db.example.test:5432/adhikarai")
    monkeypatch.setenv("REDIS_URL", "rediss://redis.example.test:6379/0")
    monkeypatch.setenv("ADMIN_API_TOKEN", "prod-admin-token")
    monkeypatch.setenv("OTP_PROVIDER", "msg91")
    monkeypatch.setenv("MSG91_AUTH_KEY", "msg91-key")
    monkeypatch.setenv("MSG91_TEMPLATE_ID", "template")
    monkeypatch.setenv("CORS_ORIGINS", "https://adhikarai.example.test")
    from app.cli.local_e2e import assert_local_e2e_enabled
    from app.core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(SystemExit):
        assert_local_e2e_enabled()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_admin_scheme_history_requires_scheme_read_permission():
    actor = dashboard.DashboardActor(
        user_id=None,
        member_id=uuid4(),
        organisation_id=ORG_ID,
        role="operator",
        display_name="Operator",
    )

    response = await scheme_history("pm_kisan", actor)

    assert response == {"items": [], "scheme_id": "pm_kisan"}
