from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.core.errors import ApiError
from app.core.security import create_session_jwt, decode_session_jwt, hash_otp, verify_otp_hash
from app.db.models import User
from app.services.phase4 import assert_no_aadhaar_payload, mark_guest_migration


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_otp_hash_does_not_store_plaintext():
    challenge_id = str(uuid4())
    hashed = hash_otp("123456", challenge_id)

    assert hashed != "123456"
    assert verify_otp_hash("123456", challenge_id, hashed)
    assert not verify_otp_hash("654321", challenge_id, hashed)


def test_jwt_cookie_payload_round_trip():
    user = User(id=uuid4(), organisation_id=ORG_ID, phone_e164="+919876543210")

    token = create_session_jwt(user)
    payload = decode_session_jwt(token)

    assert payload["sub"] == str(user.id)
    assert payload["org"] == str(ORG_ID)


def test_aadhaar_number_rejected_anywhere_in_payload():
    with pytest.raises(ApiError) as exc:
        assert_no_aadhaar_payload({"metadata": {"aadhaar_number": "123412341234"}})

    assert exc.value.code == "AADHAAR_NOT_ALLOWED"


class FakeDb:
    def __init__(self, profile):
        self.profile = profile

    async def get(self, model, key):
        return self.profile


@pytest.mark.asyncio
async def test_guest_migration_is_idempotent():
    profile = type("Profile", (), {"custom_attributes": {}})()
    user = User(id=uuid4(), organisation_id=ORG_ID, phone_e164="+919876543210", primary_profile_id=uuid4())
    db = FakeDb(profile)

    first = await mark_guest_migration(db, user, "guest-1")
    second = await mark_guest_migration(db, user, "guest-1")

    assert first is True
    assert second is False
    assert profile.custom_attributes["migrated_guest_profile_ids"] == ["guest-1"]
