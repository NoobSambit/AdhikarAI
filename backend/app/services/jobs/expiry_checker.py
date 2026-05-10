from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdminNotification, Scheme, SchemeStatusEvent


@dataclass(frozen=True, slots=True)
class ExpiryRunResult:
    expired_count: int
    warning_count: int


async def expire_schemes(today: date, db: AsyncSession) -> ExpiryRunResult:
    expired_count = 0
    warning_count = 0
    expired = await db.scalars(
        select(Scheme).where(
            Scheme.valid_until.is_not(None),
            Scheme.valid_until < today,
            Scheme.status != "expired",
            Scheme.is_active.is_(True),
        )
    )
    for scheme in expired.all():
        old_status = scheme.status
        scheme.status = "expired"
        scheme.is_active = False
        expired_count += 1
        db.add(SchemeStatusEvent(organisation_id=scheme.organisation_id, scheme_id=scheme.id, old_status=old_status, new_status="expired", reason="Scheme validity date has passed."))
        db.add(
            AdminNotification(
                organisation_id=scheme.organisation_id,
                notification_type="scheme_expired",
                title=f"{scheme.name} expired",
                body=f"{scheme.name} expired on {scheme.valid_until}.",
                related_scheme_id=scheme.id,
                severity="critical",
            )
        )
    for days in (30, 7):
        target = today + timedelta(days=days)
        expiring = await db.scalars(
            select(Scheme).where(
                Scheme.valid_until == target,
                Scheme.status == "active",
                Scheme.is_active.is_(True),
            )
        )
        for scheme in expiring.all():
            warning_count += 1
            db.add(
                AdminNotification(
                    organisation_id=scheme.organisation_id,
                    notification_type=f"scheme_expiring_{days}_days",
                    title=f"{scheme.name} expires in {days} days",
                    body=f"{scheme.name} is valid until {scheme.valid_until}.",
                    related_scheme_id=scheme.id,
                    severity="warning",
                )
            )
    await db.commit()
    return ExpiryRunResult(expired_count=expired_count, warning_count=warning_count)

