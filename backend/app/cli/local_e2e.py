"""Local-only seed data and dashboard session helper for end-to-end smoke tests."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_dashboard_session_jwt, create_session_jwt
from app.db.models import (
    AdminUser,
    ApplicationStatus,
    Beneficiary,
    BeneficiaryFollowup,
    Household,
    Organisation,
    OrganisationMember,
    Profile,
    QualityFlag,
    UnmatchedQuery,
    User,
)
from app.db.session import AsyncSessionLocal
from app.services.seeds import PUBLIC_ORG_ID, seed_central_schemes

OTHER_ORG_ID = UUID("00000000-0000-0000-0000-000000000002")


def assert_local_e2e_enabled() -> None:
    settings = get_settings()
    if not settings.is_local_like_env or not settings.local_e2e_helpers_enabled:
        raise SystemExit("Local E2E helpers require APP_ENV=local/dev/test and LOCAL_E2E_HELPERS_ENABLED=true.")


async def _get_or_create_org(db: AsyncSession, org_id: UUID, slug: str, name: str) -> Organisation:
    org = await db.get(Organisation, org_id)
    if org is None:
        org = Organisation(id=org_id, slug=slug, name=name, organisation_type="ngo")
        db.add(org)
        await db.flush()
    return org


async def _get_or_create_admin(db: AsyncSession, org_id: UUID, email: str, name: str) -> AdminUser:
    admin = await db.scalar(select(AdminUser).where(AdminUser.organisation_id == org_id, AdminUser.email == email))
    if admin is None:
        admin = AdminUser(organisation_id=org_id, email=email, display_name=name, role="dashboard")
        db.add(admin)
        await db.flush()
    return admin


async def _get_or_create_member(db: AsyncSession, org_id: UUID, role: str, email: str, name: str) -> OrganisationMember:
    member = await db.scalar(select(OrganisationMember).where(OrganisationMember.organisation_id == org_id, OrganisationMember.email == email))
    if member is None:
        admin = await _get_or_create_admin(db, org_id, email, name)
        member = OrganisationMember(
            organisation_id=org_id,
            admin_user_id=admin.id,
            role=role,
            email=email,
            display_name=name,
            is_active=True,
        )
        db.add(member)
        await db.flush()
    return member


async def _get_or_create_user(db: AsyncSession, org_id: UUID, phone: str, profile_id: UUID | None = None) -> User:
    user = await db.scalar(select(User).where(User.organisation_id == org_id, User.phone_e164 == phone))
    if user is None:
        user = User(
            organisation_id=org_id,
            phone_e164=phone,
            phone_verified_at=datetime.now(timezone.utc),
            primary_profile_id=profile_id,
            language_code="hi",
        )
        db.add(user)
        await db.flush()
    elif profile_id and user.primary_profile_id is None:
        user.primary_profile_id = profile_id
    return user


async def _get_or_create_beneficiary(
    db: AsyncSession,
    org_id: UUID,
    operator_id: UUID,
    name: str,
    phone: str,
    village: str,
    district: str,
) -> tuple[Beneficiary, User]:
    beneficiary = await db.scalar(select(Beneficiary).where(Beneficiary.organisation_id == org_id, Beneficiary.phone_e164 == phone))
    if beneficiary is None:
        household = Household(
            organisation_id=org_id,
            state_code="IN-BR",
            district=district,
            village=village,
            annual_household_income=72000,
            ration_card_type="bpl",
        )
        db.add(household)
        await db.flush()
        profile = Profile(
            organisation_id=org_id,
            household_id=household.id,
            display_name=name,
            age=38,
            gender="female",
            caste_category="OBC",
            annual_income=72000,
            land_holding_acres=0.5,
            occupation_type="farmer",
            marital_status="widowed",
            state_code="IN-BR",
            district=district,
            profile_completeness=85,
        )
        db.add(profile)
        await db.flush()
        beneficiary = Beneficiary(
            organisation_id=org_id,
            profile_id=profile.id,
            assigned_operator_id=operator_id,
            name=name,
            phone_e164=phone,
            state_code="IN-BR",
            language_code="hi",
            village=village,
            district=district,
            source="operator",
        )
        db.add(beneficiary)
        await db.flush()
    user = await _get_or_create_user(db, org_id, phone, beneficiary.profile_id)
    status = await db.scalar(
        select(ApplicationStatus).where(
            ApplicationStatus.organisation_id == org_id,
            ApplicationStatus.user_id == user.id,
            ApplicationStatus.profile_id == beneficiary.profile_id,
            ApplicationStatus.scheme_id == "pm_kisan",
        )
    )
    if status is None:
        db.add(
            ApplicationStatus(
                organisation_id=org_id,
                user_id=user.id,
                profile_id=beneficiary.profile_id,
                scheme_id="pm_kisan",
                status="documents_gathering",
                source="operator",
            )
        )
    followup = await db.scalar(select(BeneficiaryFollowup).where(BeneficiaryFollowup.beneficiary_id == beneficiary.id))
    if followup is None:
        db.add(
            BeneficiaryFollowup(
                organisation_id=org_id,
                beneficiary_id=beneficiary.id,
                assigned_operator_id=operator_id,
                due_date=date.today(),
                reason="Collect bank passbook copy",
            )
        )
    else:
        followup.assigned_operator_id = operator_id
        followup.due_date = date.today()
        followup.reason = "Collect bank passbook copy"
        followup.status = "open"
    return beneficiary, user


async def _seed_admin_fixtures(db: AsyncSession, org_id: UUID, profile_id: UUID) -> None:
    unmatched = await db.scalar(select(UnmatchedQuery).where(UnmatchedQuery.organisation_id == org_id, UnmatchedQuery.normalized_query_text == "goat shed support"))
    if unmatched is None:
        db.add(
            UnmatchedQuery(
                organisation_id=org_id,
                profile_id=profile_id,
                original_query_text="Need help for goat shed support",
                normalized_query_text="goat shed support",
                language_code="en",
                profile_completeness=60,
                result_count=0,
            )
        )
    quality = await db.scalar(select(QualityFlag).where(QualityFlag.organisation_id == org_id, QualityFlag.flag_type == "low_confidence_repeat"))
    if quality is None:
        db.add(
            QualityFlag(
                organisation_id=org_id,
                profile_id=profile_id,
                flag_type="low_confidence_repeat",
                severity="warning",
                details={"reason": "Local E2E fixture"},
            )
        )


def _write_cookie(path: Path, token: str, cookie_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Netscape HTTP Cookie File",
                f"#HttpOnly_localhost\tFALSE\t/\tFALSE\t0\t{cookie_name}\t{token}",
                f"#HttpOnly_127.0.0.1\tFALSE\t/\tFALSE\t0\t{cookie_name}\t{token}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)


async def seed(cookie_dir: Path) -> dict[str, str]:
    assert_local_e2e_enabled()
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        await seed_central_schemes(db)
        await _get_or_create_org(db, PUBLIC_ORG_ID, "public", "Public")
        await _get_or_create_org(db, OTHER_ORG_ID, "other-local-ngo", "Other Local NGO")

        operator = await _get_or_create_member(db, PUBLIC_ORG_ID, "operator", "operator.local@example.test", "Local Operator")
        other_operator = await _get_or_create_member(db, PUBLIC_ORG_ID, "operator", "operator2.local@example.test", "Second Local Operator")
        ngo_admin = await _get_or_create_member(db, PUBLIC_ORG_ID, "ngo_admin", "ngo-admin.local@example.test", "Local NGO Admin")
        super_admin = await _get_or_create_member(db, PUBLIC_ORG_ID, "super_admin", "super-admin.local@example.test", "Local Super Admin")
        other_org_operator = await _get_or_create_member(db, OTHER_ORG_ID, "operator", "other-operator.local@example.test", "Other NGO Operator")

        assigned, assigned_user = await _get_or_create_beneficiary(db, PUBLIC_ORG_ID, operator.id, "Local Beneficiary Assigned", "+919000000001", "Rampur", "Patna")
        unassigned, _ = await _get_or_create_beneficiary(db, PUBLIC_ORG_ID, other_operator.id, "Local Beneficiary Unassigned", "+919000000002", "Bairiya", "Patna")
        other_org, _ = await _get_or_create_beneficiary(db, OTHER_ORG_ID, other_org_operator.id, "Other NGO Beneficiary", "+919000000003", "Madhopur", "Gaya")
        await _seed_admin_fixtures(db, PUBLIC_ORG_ID, assigned.profile_id)

        await db.commit()

        sessions = {
            "operator": (operator, cookie_dir / "operator.cookie"),
            "ngo_admin": (ngo_admin, cookie_dir / "ngo_admin.cookie"),
            "super_admin": (super_admin, cookie_dir / "super_admin.cookie"),
        }
        for _, (member, path) in sessions.items():
            _write_cookie(path, create_dashboard_session_jwt(member), settings.auth_cookie_name)
        _write_cookie(cookie_dir / "beneficiary.cookie", create_session_jwt(assigned_user), settings.auth_cookie_name)

        metadata = {
            "organisation_id": str(PUBLIC_ORG_ID),
            "other_organisation_id": str(OTHER_ORG_ID),
            "operator_member_id": str(operator.id),
            "ngo_admin_member_id": str(ngo_admin.id),
            "super_admin_member_id": str(super_admin.id),
            "operator_email": operator.email or "",
            "ngo_admin_email": ngo_admin.email or "",
            "super_admin_email": super_admin.email or "",
            "assigned_beneficiary_id": str(assigned.id),
            "unassigned_beneficiary_id": str(unassigned.id),
            "other_org_beneficiary_id": str(other_org.id),
            "cookie_dir": str(cookie_dir),
        }
        (cookie_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed local-only E2E data and dashboard cookie jars.")
    parser.add_argument("--cookie-dir", type=Path, default=Path("/tmp/adhikarai-local-e2e"), help="Directory for local cookie jars and metadata.")
    args = parser.parse_args()
    metadata = asyncio.run(seed(args.cookie_dir))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
