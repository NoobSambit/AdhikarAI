from uuid import UUID, uuid4

import pytest

from app.core.errors import ApiError
from app.dashboard.rbac import DashboardActor, ROLE_PERMISSIONS, assert_beneficiary_access, require_actor_permission


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_phase5_roles_exactly_match_prd():
    assert set(ROLE_PERMISSIONS) == {"super_admin", "ngo_admin", "operator"}


def test_operator_requires_assigned_beneficiary():
    actor = DashboardActor(
        user_id=uuid4(),
        member_id=uuid4(),
        organisation_id=ORG_ID,
        role="operator",
    )

    assert_beneficiary_access(actor, ORG_ID, actor.member_id)

    with pytest.raises(ApiError) as exc:
        assert_beneficiary_access(actor, ORG_ID, uuid4())

    assert exc.value.code == "BENEFICIARY_NOT_ASSIGNED"


def test_ngo_admin_restricted_to_own_organisation():
    actor = DashboardActor(
        user_id=uuid4(),
        member_id=uuid4(),
        organisation_id=ORG_ID,
        role="ngo_admin",
    )

    with pytest.raises(ApiError) as exc:
        assert_beneficiary_access(actor, uuid4(), None)

    assert exc.value.code == "ORG_SCOPE_DENIED"


def test_super_admin_has_all_permissions():
    actor = DashboardActor(
        user_id=uuid4(),
        member_id=uuid4(),
        organisation_id=ORG_ID,
        role="super_admin",
    )

    require_actor_permission(actor, "scheme:publish")
    assert_beneficiary_access(actor, uuid4(), None)


def test_operator_cannot_publish_schemes():
    actor = DashboardActor(
        user_id=uuid4(),
        member_id=uuid4(),
        organisation_id=ORG_ID,
        role="operator",
    )

    with pytest.raises(ApiError) as exc:
        require_actor_permission(actor, "scheme:publish")

    assert exc.value.code == "PERMISSION_DENIED"
