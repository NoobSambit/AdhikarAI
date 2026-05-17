from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.rbac import DashboardActor
from app.db.models import AuditLog


def add_audit_log(
    db: AsyncSession,
    actor: DashboardActor,
    action: str,
    resource_type: str,
    resource_id: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            organisation_id=actor.organisation_id,
            actor_member_id=actor.member_id,
            actor_user_id=actor.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_snapshot=before,
            after_snapshot=after,
        )
    )
