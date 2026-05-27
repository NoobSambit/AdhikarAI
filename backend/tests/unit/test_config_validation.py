import pytest

from app.core.config import Settings


VALID_DEPLOYED = {
    "app_env": "production",
    "auth_jwt_secret": "production-secret-with-more-than-32-chars",
    "auth_cookie_secure": True,
    "database_url": "postgresql+asyncpg://prod:prod@db.example.test:5432/adhikarai",
    "database_direct_url": "postgresql+asyncpg://prod:prod@db.example.test:5432/adhikarai",
    "redis_url": "rediss://redis.example.test:6379/0",
    "admin_api_token": "prod-admin-token",
    "otp_provider": "msg91",
    "msg91_auth_key": "msg91-key",
    "msg91_template_id": "template",
    "cors_origins": "https://adhikarai.example.test",
}


def test_local_settings_allow_memory_redis_and_mock_defaults():
    settings = Settings(app_env="local", redis_url="memory://", auth_cookie_secure=False)

    assert settings.is_local_like_env
    assert settings.redis_url == "memory://"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("auth_jwt_secret", "change-me-phase-4"),
        ("auth_jwt_secret", "short"),
        ("admin_api_token", "change-me"),
        ("database_url", "postgresql+asyncpg://adhikarai:adhikarai@localhost:5432/adhikarai"),
        ("database_direct_url", "postgresql+asyncpg://adhikarai:adhikarai@localhost:5432/adhikarai"),
        ("redis_url", "memory://"),
        ("auth_cookie_secure", False),
        ("cors_origins", "*"),
        ("dashboard_auth_provider", "dev"),
        ("dashboard_dev_login_enabled", True),
        ("otp_provider", "mock"),
    ],
)
def test_production_rejects_insecure_settings(field, value):
    kwargs = {**VALID_DEPLOYED, field: value}

    with pytest.raises(ValueError):
        Settings(**kwargs)


def test_production_rejects_localhost_cors():
    with pytest.raises(ValueError):
        Settings(**{**VALID_DEPLOYED, "cors_origins": "http://localhost:3000"})


def test_staging_mock_otp_requires_explicit_allow_flag():
    staging = {**VALID_DEPLOYED, "app_env": "staging", "otp_provider": "mock", "allow_mock_otp_in_staging": True}

    assert Settings(**staging).allow_mock_otp_in_staging is True

    with pytest.raises(ValueError):
        Settings(**{**staging, "allow_mock_otp_in_staging": False})
