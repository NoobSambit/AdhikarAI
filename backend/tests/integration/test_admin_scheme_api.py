import pytest

from app.api.routes.admin_schemes import create
from app.core.errors import ApiError
from app.core.security import require_admin_token
from app.schemas.scheme import CreateSchemeRequest


@pytest.mark.asyncio
async def test_admin_scheme_api_requires_token():
    with pytest.raises(ApiError) as exc:
        await require_admin_token(None)
    assert exc.value.status_code == 401
    assert exc.value.code == "ADMIN_TOKEN_INVALID"


@pytest.mark.asyncio
async def test_admin_scheme_api_duplicate_id(monkeypatch):
    async def fake_create(db, request):
        raise ApiError(409, "SCHEME_ID_EXISTS", "Scheme ID already exists.", "id")

    monkeypatch.setattr("app.api.routes.admin_schemes.create_scheme", fake_create)
    request = CreateSchemeRequest(
        organisation_id="00000000-0000-0000-0000-000000000001",
        id="test_scheme",
        name="Test",
        description="Test",
        plain_language_summary="Test",
        ministry="Test",
        benefit_type="cash",
        benefit_amount="Test",
        source_url="https://example.com",
        eligibility_rule={"required_documents": []},
    )
    with pytest.raises(ApiError) as exc:
        await create(request, db=None)
    assert exc.value.status_code == 409
    assert exc.value.code == "SCHEME_ID_EXISTS"
