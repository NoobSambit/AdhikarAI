from uuid import UUID, uuid4

import pytest

from app.admin_panel.scheme_drafts import create_scheme_draft
from app.dashboard.rbac import DashboardActor
from app.db.models import SchemeDraft


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_new_scheme_draft_does_not_set_missing_scheme_fk(monkeypatch):
    class FakeSession:
        def __init__(self):
            self.rows = []

        async def get(self, model, key):
            return None

        def add(self, row):
            self.rows.append(row)

        async def flush(self):
            pass

        async def commit(self):
            pass

    async def fake_validate(db, actor, payload):
        return {"errors": [], "warnings": []}

    monkeypatch.setattr("app.admin_panel.scheme_drafts.validate_draft_payload", fake_validate)
    actor = DashboardActor(user_id=None, member_id=uuid4(), organisation_id=ORG_ID, role="super_admin")
    db = FakeSession()

    await create_scheme_draft(
        db,
        actor,
        {"scheme": {"id": "new_local_scheme"}, "eligibility_rule": {"required_documents": []}},
        "Create local test scheme",
    )

    draft = next(row for row in db.rows if isinstance(row, SchemeDraft))
    assert draft.scheme_id is None
    assert draft.draft_payload["scheme"]["id"] == "new_local_scheme"
