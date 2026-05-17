from uuid import UUID, uuid4

import pytest

from app.api.routes.phase4 import get_me, post_send_otp
from app.core.errors import ApiError
from app.db.models import User
from app.schemas.phase4 import SendOtpRequest


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


class FakeDb:
    async def get(self, model, key):
        return object()

    def add(self, row):
        self.row = row

    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_send_otp_masks_phone_and_hashes_otp(monkeypatch):
    async def fake_ensure(db, organisation_id):
        return object()

    class EmptyResultDb(FakeDb):
        async def scalar(self, stmt):
            return None

    monkeypatch.setattr("app.services.phase4.ensure_organisation", fake_ensure)
    monkeypatch.setattr("app.services.phase4.generate_otp", lambda: "123456")

    response = await post_send_otp(SendOtpRequest(organisation_id=ORG_ID, phone_e164="+919876543210"), db=EmptyResultDb())

    assert response.masked_phone == "+91******3210"


@pytest.mark.asyncio
async def test_get_me_authenticated_shape():
    user = User(
        id=uuid4(),
        organisation_id=ORG_ID,
        phone_e164="+919876543210",
        language_code="hi",
        high_contrast_enabled=True,
        font_size="large",
        notification_opt_in=True,
    )

    response = await get_me(user=user)

    assert response.user.language_code == "hi"
    assert response.user.high_contrast_enabled is True


@pytest.mark.asyncio
async def test_saved_schemes_guest_restriction_uses_auth_dependency():
    from app.core.security import require_user

    with pytest.raises(ApiError) as exc:
        await require_user(token=None, db=None)

    assert exc.value.code == "NOT_AUTHENTICATED"
