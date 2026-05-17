from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.core.errors import ApiError

DashboardRole = Literal["super_admin", "ngo_admin", "operator"]
Permission = Literal[
    "beneficiary:read",
    "beneficiary:write",
    "beneficiary:export",
    "scheme:read",
    "scheme:write",
    "scheme:publish",
    "analytics:read",
    "quality:review",
]

ROLE_PERMISSIONS: dict[DashboardRole, set[str]] = {
    "super_admin": {"*"},
    "ngo_admin": {"beneficiary:read", "beneficiary:write", "beneficiary:export", "scheme:read", "analytics:read"},
    "operator": {"beneficiary:read", "beneficiary:write", "scheme:read"},
}


@dataclass(frozen=True, slots=True)
class DashboardActor:
    user_id: UUID
    member_id: UUID
    organisation_id: UUID
    role: DashboardRole
    display_name: str = ""

    @property
    def permissions(self) -> set[str]:
        return ROLE_PERMISSIONS[self.role]


def require_actor_permission(actor: DashboardActor, permission: str) -> None:
    allowed = actor.permissions
    if "*" not in allowed and permission not in allowed:
        raise ApiError(403, "PERMISSION_DENIED", "You do not have access to this action.", "permission")


def assert_organisation_scope(actor: DashboardActor, organisation_id: UUID) -> None:
    if actor.role != "super_admin" and actor.organisation_id != organisation_id:
        raise ApiError(403, "ORG_SCOPE_DENIED", "You do not have access to this organisation.", "organisation_id")


def assert_beneficiary_access(
    actor: DashboardActor,
    beneficiary_organisation_id: UUID,
    assigned_operator_id: UUID | None,
) -> None:
    assert_organisation_scope(actor, beneficiary_organisation_id)
    if actor.role == "operator" and assigned_operator_id != actor.member_id:
        raise ApiError(403, "BENEFICIARY_NOT_ASSIGNED", "This beneficiary is not assigned to you.", "beneficiary_id")
