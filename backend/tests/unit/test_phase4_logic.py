from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.phase4 import OfflineSyncItem, UpdateApplicationStatusRequest
from app.services.phase4 import assert_no_aadhaar_payload, process_offline_sync


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_application_status_values_are_exact():
    request = UpdateApplicationStatusRequest(profile_id=uuid4(), scheme_id="pm_kisan", status="submitted")
    assert request.status == "submitted"

    with pytest.raises(ValidationError):
        UpdateApplicationStatusRequest(profile_id=uuid4(), scheme_id="pm_kisan", status="in_review")


def test_offline_sync_retry_metadata_limit():
    item = OfflineSyncItem(
        action_type="checklist.update",
        payload={"scheme_id": "pm_kisan"},
        created_at=datetime.now(timezone.utc),
        retry_count=5,
        idempotency_key="idem-12345",
    )

    assert item.retry_count == 5


def test_aadhaar_payload_guard_accepts_metadata_but_rejects_number():
    assert_no_aadhaar_payload({"document_type": "aadhaar", "masked_identifier": "xxxx"})
    with pytest.raises(Exception):
        assert_no_aadhaar_payload({"aadhaar": "123412341234"})
