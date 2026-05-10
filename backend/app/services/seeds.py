import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EligibilityRule, Organisation, Scheme
from app.schemas.scheme import EligibilityCriteriaModel
from app.services.eligibility.validation import validate_rule

PUBLIC_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


async def ensure_public_organisation(db: AsyncSession) -> Organisation:
    org = await db.get(Organisation, PUBLIC_ORG_ID)
    if org is None:
        org = Organisation(id=PUBLIC_ORG_ID, slug="public", name="Public", organisation_type="platform")
        db.add(org)
        await db.commit()
        await db.refresh(org)
    return org


async def seed_central_schemes(db: AsyncSession, seed_path: Path | None = None) -> int:
    org = await ensure_public_organisation(db)
    path = seed_path or Path(__file__).resolve().parents[1] / "seeds" / "central_schemes.v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    seed_ids = {item["id"] for item in data["schemes"]}
    checked_at = datetime.fromisoformat(data["source_last_checked_at"])
    count = 0
    for item in data["schemes"]:
        existing = await db.get(Scheme, item["id"])
        if existing is not None:
            continue
        criteria = EligibilityCriteriaModel.model_validate(item["eligibility_rule"])
        issues = validate_rule(criteria, seed_ids)
        if issues:
            raise ValueError(f"Seed rule for {item['id']} is invalid: {issues}")
        scheme = Scheme(
            id=item["id"],
            organisation_id=org.id,
            name=item["name"],
            description=item["description"],
            plain_language_summary=item["plain_language_summary"],
            ministry=item["ministry"],
            state_code=item["state_code"],
            benefit_type=item["benefit_type"],
            benefit_amount=item["benefit_amount"],
            application_url=item["application_url"],
            source_url=item["source_url"],
            verification_status=item["verification_status"],
            source_last_checked_at=checked_at,
            status="active",
            is_active=True,
        )
        db.add(scheme)
        db.add(EligibilityRule(organisation_id=org.id, scheme_id=item["id"], version=1, criteria=criteria.model_dump(mode="json"), is_active=True))
        count += 1
    await db.commit()
    return count
