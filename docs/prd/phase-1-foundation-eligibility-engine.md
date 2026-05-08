# AdhikarAI PRD - Phase 1: Foundation and Eligibility Engine

## Phase Summary

Phase 1 builds the non-voice, non-frontend foundation for AdhikarAI: a multilingual-ready scheme knowledge base, a PostgreSQL-backed eligibility rule store, an Experta-based eligibility engine, semantic scheme search with FAISS, an admin CLI, seed data for central schemes, and FastAPI REST endpoints.

Primary phase user: an internal developer or admin service that submits a structured beneficiary profile and receives matched schemes and near-miss schemes.

The production user remains a rural Indian beneficiary who may have low literacy and a low-end Android phone, but Phase 1 exposes only backend APIs. All Phase 1 decisions must preserve later support for voice, multilingual conversation, offline PWA behavior, and NGO operator workflows.

Important correction to the original brief: every tenant-scoped table includes `organisation_id`. The root `organisations` table itself cannot include an FK to itself and is the only exception.

## Goals and Success Criteria

1. Store welfare schemes and eligibility rules without code changes.
   - Success: adding a new scheme through CLI or API requires no Python code edit.
   - Success: `eligibility_rules.criteria` stores nested JSONB for age, gender, caste, income, land, occupation, marital status, state, exclusions, required documents, and custom criteria.

2. Return deterministic eligibility matches for structured profiles.
   - Success: `POST /profile/match` evaluates all active schemes for the caller's `organisation_id` in under 500 ms for 500 active schemes on hosted Render free tier, excluding cold start.
   - Success: cross-scheme exclusions reject schemes when `user_profile.existing_scheme_ids` intersects `criteria.exclusion_scheme_ids`.

3. Return near-miss results.
   - Success: schemes failing exactly one criterion are returned in `near_miss_schemes` with `failed_criterion`, `failed_value`, `required_value`, and `how_to_qualify`.
   - Success: schemes failing 2 or more criteria are excluded from both result arrays.

4. Keep scheme status current.
   - Success: daily background job marks schemes with `valid_until < current_date` as `expired`, sets `is_active=false`, and inserts an admin notification.

5. Support semantic search from day one.
   - Success: a FAISS index over active scheme descriptions and plain-language summaries can return top 10 schemes by semantic similarity.
   - Success: index rebuild is idempotent and stored with a content hash.

6. Seed credible starter data.
   - Success: at least 25 central schemes load from `backend/app/seeds/central_schemes.v1.json`.
   - Success: each seeded scheme has documents and substitute documents encoded.
   - Success: every seed record has `source_url`, `source_last_checked_at`, and `verification_status`.

7. Prepare for future MyScheme ingestion without depending on an undocumented API.
   - Success: schema stores `external_source`, `external_id`, raw payload snapshots, and mapping errors.
   - Success: `myscheme` ingestion adapter supports configured API, static JSON export, or CSV import modes.

## User Stories

1. Structured profile match
   - As an API client, I send a structured rural beneficiary profile.
   - The API returns fully eligible schemes and near-miss schemes.
   - Edge case: if required profile fields are missing, the API still evaluates criteria that can be evaluated and reports `unknown_criteria` for schemes blocked by missing facts.

2. Existing scheme exclusion
   - As a beneficiary already receiving one scheme, I should not be told to apply for a mutually exclusive scheme.
   - Example: if profile has `existing_scheme_ids=["pmay_g"]` and a target scheme has `exclusion_scheme_ids=["pmay_g"]`, the target scheme returns ineligible with reason `already_receives_excluded_scheme`.

3. Near-miss result
   - As a beneficiary whose income is just above a threshold, I should see that the scheme is a near miss and understand what changed.
   - Example: annual income is `130000`, max income is `120000`; response says "This scheme requires annual household income at or below INR 120,000."

4. Admin adds scheme
   - As an admin, I create a scheme with JSONB eligibility rules.
   - The system validates required fields, document shape, broken exclusions, and contradictory criteria before saving.
   - Error state: if `min_age > max_age`, API returns `422 RULE_CONTRADICTION` with field `criteria.min_age`.

5. Admin archives scheme
   - As an admin, I archive an expired or obsolete scheme.
   - The scheme remains queryable by ID for audit, but is excluded from default matching and semantic search.

6. Expiry checker
   - As an admin, I receive an admin notification when a scheme expires or will expire soon.
   - Edge case: if `valid_until` is null, expiry checker does not mark it expired.

7. Semantic search
   - As a service, I search "help for pregnant woman first child" and receive PMMVY and JSY among top results.
   - Error state: if FAISS index is missing, API rebuilds once; if rebuild fails, `GET /schemes/search` falls back to PostgreSQL `ILIKE` and returns `search_mode="fallback_text"`.

8. MyScheme ingestion
   - As an admin, I run an ingestion job.
   - If official API credentials are absent, the job must fail with `424 INGESTION_SOURCE_UNAVAILABLE` and must not create partial schemes.
   - If CSV mode is configured, rows with invalid eligibility JSON go to `ingestion_errors` and valid rows can still be staged.

## Functional Requirements

1. The backend must be FastAPI with async routes.
2. PostgreSQL must be the source of truth for schemes and eligibility rules.
3. Every tenant-scoped table must include `organisation_id UUID NOT NULL REFERENCES organisations(id)`.
4. The `schemes` table must include exactly these required product fields: `id`, `name`, `description`, `ministry`, `state_code`, `benefit_type`, `benefit_amount`, `application_url`, `is_active`, `valid_until`, `created_at`, `updated_at`.
5. `state_code` must be nullable. `null` means central scheme.
6. Eligibility criteria must be stored in `eligibility_rules.criteria JSONB`.
7. Rule JSON must allow nested objects and arrays.
8. Rule JSON must support `min_age`, `max_age`, `gender`, `caste_categories`, `max_annual_income`, `max_land_holding_acres`, `occupation_types`, `marital_status`, `state_codes`, `exclusion_scheme_ids`, and `required_documents`.
9. `required_documents` objects must contain `name`, `is_mandatory`, and `accepted_substitutes`.
10. Accepted substitute objects must contain `name`, `instructions`, `estimated_cost_inr`, `estimated_time_days`, and `issuing_authority`.
11. Rule JSON must support `custom_criteria` for scheme facts not covered by the base fields.
12. No eligibility rule may require a field that the profile schema cannot represent.
13. Rule validation must reject `min_age > max_age`.
14. Rule validation must reject negative income, negative land holding, and empty mandatory document names.
15. Rule validation must reject `exclusion_scheme_ids` that do not exist in the same `organisation_id`.
16. Rule validation must reject `state_codes` not in ISO 3166-2 IN subdivision style such as `IN-BR`, `IN-UP`, `IN-TN`.
17. The engine must evaluate only latest active rule version per scheme.
18. The engine must ignore schemes where `is_active=false`, `status != 'active'`, or `valid_until < current_date`.
19. Cross-scheme exclusion must be evaluated before normal criteria.
20. If a user already receives an excluded scheme, the scheme must be ineligible and must not appear as near miss.
21. Near-miss detection must count failed criteria after excluding unknown criteria.
22. A near miss is returned only when `failed_criteria_count == 1` and `unknown_criteria_count == 0`.
23. If required profile facts are missing, return the scheme under `incomplete_schemes` only when requested with `include_incomplete=true`.
24. Default `POST /profile/match` response must include `matched_schemes` and `near_miss_schemes`.
25. `matched_schemes` must include `eligibility_score=100`.
26. `near_miss_schemes` must include `eligibility_score` between 50 and 99.
27. The engine must return machine-readable criterion IDs, not only prose.
28. The engine must return plain-language explanations in English in Phase 1; later phases translate them.
29. FAISS index must index `name`, `description`, `benefit_type`, `benefit_amount`, `ministry`, and rule-derived keywords.
30. Embedding provider must be switchable through env vars.
31. Phase 1 local default embedding model must be `intfloat/multilingual-e5-small`.
32. Phase 1 hosted default embedding model must be `intfloat/multilingual-e5-small` running inside the FastAPI service if memory allows, otherwise precomputed index loaded from disk.
33. Admin CRUD endpoints must require `X-Admin-Token` in Phase 1.
34. Admin auth is deliberately simple in Phase 1 and replaced by role auth in Phase 4 and Phase 5.
35. Admin CLI must be implemented with Typer.
36. CLI commands must include `scheme add`, `scheme update`, `scheme archive`, `scheme validate`, `scheme seed`, `index rebuild`, and `expiry-check run`.
37. Admin CLI must call the same validation code as API.
38. Background jobs must use APScheduler in Phase 1.
39. Expiry job must run daily at 02:00 Asia/Kolkata by default.
40. Expiry job must insert notifications for schemes expiring in 30 days, 7 days, and on expiry.
41. MyScheme ingestion must be built as an adapter interface even if public API access is unavailable.
42. Ingestion must preserve raw external payloads before mapping.
43. Ingestion must stage imported schemes as `draft` unless `INGESTION_AUTO_PUBLISH=true`.
44. Seed data must be loaded into the default organisation `public`.
45. All write operations must record `created_by` and `updated_by` where an admin actor exists.
46. All API errors must use the standard error body defined below.

Standard error body:

```json
{
  "error": {
    "code": "RULE_CONTRADICTION",
    "message": "Minimum age cannot be greater than maximum age.",
    "field": "criteria.min_age",
    "request_id": "req_01JABC"
  }
}
```

## Data Models

### SQL DDL

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE organisations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    organisation_type TEXT NOT NULL DEFAULT 'platform',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    email TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, email)
);

CREATE TABLE scheme_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, code)
);

CREATE TABLE schemes (
    id TEXT PRIMARY KEY,
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    category_id UUID REFERENCES scheme_categories(id),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    plain_language_summary TEXT NOT NULL DEFAULT '',
    ministry TEXT NOT NULL,
    state_code TEXT,
    benefit_type TEXT NOT NULL,
    benefit_amount TEXT NOT NULL,
    application_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('draft', 'active', 'expired', 'archived', 'upcoming')),
    valid_from DATE,
    valid_until DATE,
    source_url TEXT,
    external_source TEXT,
    external_id TEXT,
    verification_status TEXT NOT NULL DEFAULT 'needs_admin_review'
        CHECK (verification_status IN ('needs_admin_review', 'verified', 'rejected')),
    source_last_checked_at TIMESTAMPTZ,
    created_by UUID REFERENCES admin_users(id),
    updated_by UUID REFERENCES admin_users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$')
);

CREATE INDEX idx_schemes_org_status ON schemes (organisation_id, status, is_active);
CREATE INDEX idx_schemes_state_code ON schemes (state_code);
CREATE INDEX idx_schemes_valid_until ON schemes (valid_until);

CREATE TABLE eligibility_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    criteria JSONB NOT NULL,
    explanation_templates JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID REFERENCES admin_users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, scheme_id, version)
);

CREATE INDEX idx_eligibility_rules_scheme_active ON eligibility_rules (organisation_id, scheme_id, is_active);
CREATE INDEX idx_eligibility_rules_criteria_gin ON eligibility_rules USING GIN (criteria);

CREATE TABLE scheme_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    scheme_snapshot JSONB NOT NULL,
    rule_snapshot JSONB NOT NULL,
    change_summary TEXT NOT NULL,
    changed_by UUID REFERENCES admin_users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, scheme_id, version)
);

CREATE TABLE scheme_status_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_by UUID REFERENCES admin_users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE faiss_indexes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    index_name TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    vector_dimension INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    scheme_count INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    built_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, index_name, content_hash)
);

CREATE TABLE scheme_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    embedding_model TEXT NOT NULL,
    embedding VECTOR,
    embedding_text TEXT NOT NULL,
    embedding_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, scheme_id, embedding_model)
);

CREATE TABLE ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    source TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('api', 'json_file', 'csv')),
    status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'completed_with_errors', 'failed')),
    source_uri TEXT,
    records_seen INTEGER NOT NULL DEFAULT 0,
    records_staged INTEGER NOT NULL DEFAULT 0,
    records_failed INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_by UUID REFERENCES admin_users(id)
);

CREATE TABLE ingestion_payloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    ingestion_run_id UUID NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
    external_id TEXT,
    raw_payload JSONB NOT NULL,
    mapped_scheme_id TEXT,
    mapping_status TEXT NOT NULL CHECK (mapping_status IN ('mapped', 'failed', 'skipped')),
    mapping_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE admin_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    related_scheme_id TEXT REFERENCES schemes(id),
    severity TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Note: `VECTOR` requires `pgvector`. Phase 1 does not depend on pgvector for runtime because FAISS is primary. If hosted Neon plan does not support pgvector, migration must skip only `scheme_embeddings.embedding` and keep `embedding_hash` and `embedding_text`.

### Eligibility Rule JSON Schema

```json
{
  "min_age": 18,
  "max_age": 60,
  "gender": ["female", "male", "other"],
  "caste_categories": ["SC", "ST", "OBC", "GENERAL"],
  "max_annual_income": 120000,
  "max_land_holding_acres": 5,
  "occupation_types": ["farmer", "street_vendor", "unorganised_worker"],
  "marital_status": ["single", "married", "widowed", "divorced"],
  "state_codes": ["IN-BR", "IN-UP"],
  "exclusion_scheme_ids": ["pmay_g"],
  "required_documents": [
    {
      "name": "Aadhaar",
      "is_mandatory": true,
      "accepted_substitutes": [
        {
          "name": "Aadhaar enrolment slip",
          "instructions": "Visit the nearest Aadhaar Seva Kendra to complete Aadhaar enrolment or retrieve the enrolment slip.",
          "estimated_cost_inr": 0,
          "estimated_time_days": 7,
          "issuing_authority": "UIDAI"
        }
      ]
    }
  ],
  "custom_criteria": [
    {
      "field": "has_bank_account",
      "operator": "equals",
      "value": true,
      "how_to_qualify": "Open a basic savings account at a bank, post office, or banking correspondent."
    }
  ]
}
```

### Python SQLAlchemy Models

```python
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    organisation_type: Mapped[str] = mapped_column(Text, nullable=False, default="platform")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = (UniqueConstraint("organisation_id", "email"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="admin")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SchemeCategory(Base):
    __tablename__ = "scheme_categories"
    __table_args__ = (UniqueConstraint("organisation_id", "code"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Scheme(Base):
    __tablename__ = "schemes"
    __table_args__ = (
        CheckConstraint("state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$'", name="ck_scheme_state_code"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("scheme_categories.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    plain_language_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ministry: Mapped[str] = mapped_column(Text, nullable=False)
    state_code: Mapped[str | None] = mapped_column(Text)
    benefit_type: Mapped[str] = mapped_column(Text, nullable=False)
    benefit_amount: Mapped[str] = mapped_column(Text, nullable=False)
    application_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)
    external_source: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, default="needs_admin_review")
    source_last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    rules: Mapped[list["EligibilityRule"]] = relationship(back_populates="scheme")


class EligibilityRule(Base):
    __tablename__ = "eligibility_rules"
    __table_args__ = (UniqueConstraint("organisation_id", "scheme_id", "version"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    criteria: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    explanation_templates: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    scheme: Mapped[Scheme] = relationship(back_populates="rules")


class SchemeVersion(Base):
    __tablename__ = "scheme_versions"
    __table_args__ = (UniqueConstraint("organisation_id", "scheme_id", "version"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    scheme_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    rule_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FaissIndex(Base):
    __tablename__ = "faiss_indexes"
    __table_args__ = (UniqueConstraint("organisation_id", "index_name", "content_hash"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    index_name: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    vector_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    scheme_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

## API Specification

Base URL local: `http://localhost:8000`

Base URL hosted: `https://adhikarai-api.onrender.com`

All responses include `X-Request-ID`.

### Shared TypeScript Types

```ts
export type Gender = "female" | "male" | "other" | "unknown";
export type CasteCategory = "SC" | "ST" | "OBC" | "GENERAL" | "UNKNOWN";
export type MaritalStatus = "single" | "married" | "widowed" | "divorced" | "separated" | "unknown";

export interface DocumentSubstitute {
  name: string;
  instructions: string;
  estimated_cost_inr: number;
  estimated_time_days: number;
  issuing_authority: string;
}

export interface RequiredDocument {
  name: string;
  is_mandatory: boolean;
  accepted_substitutes: DocumentSubstitute[];
}

export interface EligibilityCriteria {
  min_age?: number;
  max_age?: number;
  gender?: Gender[];
  caste_categories?: CasteCategory[];
  max_annual_income?: number;
  max_land_holding_acres?: number;
  occupation_types?: string[];
  marital_status?: MaritalStatus[];
  state_codes?: string[];
  exclusion_scheme_ids?: string[];
  required_documents: RequiredDocument[];
  custom_criteria?: Array<{ field: string; operator: "equals" | "not_equals" | "in" | "lte" | "gte"; value: unknown; how_to_qualify: string }>;
}

export interface UserProfileInput {
  age?: number;
  gender?: Gender;
  caste_category?: CasteCategory;
  annual_income?: number;
  land_holding_acres?: number;
  occupation_type?: string;
  marital_status?: MaritalStatus;
  state_code?: string;
  district?: string;
  existing_scheme_ids: string[];
  custom_attributes?: Record<string, unknown>;
}

export interface SchemeSummary {
  id: string;
  name: string;
  description: string;
  ministry: string;
  state_code: string | null;
  benefit_type: string;
  benefit_amount: string;
  application_url: string | null;
  is_active: boolean;
  valid_until: string | null;
  required_documents: RequiredDocument[];
}

export interface MatchedScheme {
  scheme: SchemeSummary;
  eligibility_score: number;
  matched_criteria: string[];
  explanation: string;
}

export interface NearMissScheme {
  scheme: SchemeSummary;
  eligibility_score: number;
  failed_criterion: string;
  failed_value: unknown;
  required_value: unknown;
  how_to_qualify: string;
}
```

### Shared Pydantic Models

```python
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

Gender = Literal["female", "male", "other", "unknown"]
CasteCategory = Literal["SC", "ST", "OBC", "GENERAL", "UNKNOWN"]
MaritalStatus = Literal["single", "married", "widowed", "divorced", "separated", "unknown"]


class DocumentSubstituteModel(BaseModel):
    name: str
    instructions: str
    estimated_cost_inr: int = Field(ge=0)
    estimated_time_days: int = Field(ge=0)
    issuing_authority: str


class RequiredDocumentModel(BaseModel):
    name: str
    is_mandatory: bool
    accepted_substitutes: list[DocumentSubstituteModel] = []


class CustomCriterionModel(BaseModel):
    field: str
    operator: Literal["equals", "not_equals", "in", "lte", "gte"]
    value: Any
    how_to_qualify: str


class EligibilityCriteriaModel(BaseModel):
    min_age: int | None = Field(default=None, ge=0)
    max_age: int | None = Field(default=None, ge=0)
    gender: list[Gender] | None = None
    caste_categories: list[CasteCategory] | None = None
    max_annual_income: int | None = Field(default=None, ge=0)
    max_land_holding_acres: float | None = Field(default=None, ge=0)
    occupation_types: list[str] | None = None
    marital_status: list[MaritalStatus] | None = None
    state_codes: list[str] | None = None
    exclusion_scheme_ids: list[str] = []
    required_documents: list[RequiredDocumentModel] = []
    custom_criteria: list[CustomCriterionModel] = []


class UserProfileInputModel(BaseModel):
    age: int | None = Field(default=None, ge=0, le=120)
    gender: Gender | None = None
    caste_category: CasteCategory | None = None
    annual_income: int | None = Field(default=None, ge=0)
    land_holding_acres: float | None = Field(default=None, ge=0)
    occupation_type: str | None = None
    marital_status: MaritalStatus | None = None
    state_code: str | None = None
    district: str | None = None
    existing_scheme_ids: list[str] = []
    custom_attributes: dict[str, Any] = {}


class MatchProfileRequest(BaseModel):
    organisation_id: str
    profile: UserProfileInputModel
    include_incomplete: bool = False
    limit: int = Field(default=50, ge=1, le=200)


class SchemeSummaryModel(BaseModel):
    id: str
    name: str
    description: str
    ministry: str
    state_code: str | None
    benefit_type: str
    benefit_amount: str
    application_url: str | None
    is_active: bool
    valid_until: date | None
    required_documents: list[RequiredDocumentModel]


class MatchedSchemeModel(BaseModel):
    scheme: SchemeSummaryModel
    eligibility_score: int
    matched_criteria: list[str]
    explanation: str


class NearMissSchemeModel(BaseModel):
    scheme: SchemeSummaryModel
    eligibility_score: int
    failed_criterion: str
    failed_value: Any
    required_value: Any
    how_to_qualify: str


class MatchProfileResponse(BaseModel):
    matched_schemes: list[MatchedSchemeModel]
    near_miss_schemes: list[NearMissSchemeModel]
    incomplete_schemes: list[dict[str, Any]] = []
    evaluated_scheme_count: int
    request_id: str
```

### POST /profile/match

Request:

```json
{
  "organisation_id": "00000000-0000-0000-0000-000000000001",
  "profile": {
    "age": 34,
    "gender": "female",
    "caste_category": "OBC",
    "annual_income": 85000,
    "land_holding_acres": 1.2,
    "occupation_type": "farmer",
    "marital_status": "married",
    "state_code": "IN-BR",
    "district": "Gaya",
    "existing_scheme_ids": [],
    "custom_attributes": {
      "has_bank_account": true,
      "is_pregnant": false,
      "has_lpg_connection": false
    }
  },
  "include_incomplete": false,
  "limit": 50
}
```

Response `200`:

```json
{
  "matched_schemes": [
    {
      "scheme": {
        "id": "pm_kisan",
        "name": "Pradhan Mantri Kisan Samman Nidhi",
        "description": "Income support for eligible farmer families.",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
        "state_code": null,
        "benefit_type": "cash_transfer",
        "benefit_amount": "INR 6,000 per year",
        "application_url": "https://pmkisan.gov.in/",
        "is_active": true,
        "valid_until": null,
        "required_documents": []
      },
      "eligibility_score": 100,
      "matched_criteria": ["occupation_type", "land_holding_acres", "has_bank_account"],
      "explanation": "You appear eligible because you are a farmer with land details and a bank account."
    }
  ],
  "near_miss_schemes": [],
  "incomplete_schemes": [],
  "evaluated_scheme_count": 25,
  "request_id": "req_01JABC"
}
```

Errors:

| Status | Code | Exact behavior |
|---|---|---|
| 400 | INVALID_PROFILE | Return no matches. Body field points to invalid profile field. |
| 404 | ORGANISATION_NOT_FOUND | Return no matches. |
| 422 | UNSUPPORTED_STATE_CODE | Return no matches. |
| 500 | ELIGIBILITY_ENGINE_ERROR | Log stack trace with request ID. Return generic message: "We could not check schemes right now." |

### GET /schemes

Query params:

```ts
interface ListSchemesQuery {
  organisation_id: string;
  status?: "draft" | "active" | "expired" | "archived" | "upcoming";
  state_code?: string;
  category_code?: string;
  limit?: number;
  offset?: number;
}
```

Response `200`:

```json
{
  "items": [],
  "limit": 50,
  "offset": 0,
  "total": 0
}
```

### GET /schemes/{id}

Response `200`: `SchemeSummary` plus `eligibility_rule`.

Errors:

| Status | Code | Exact behavior |
|---|---|---|
| 404 | SCHEME_NOT_FOUND | Return standard error body. |

### GET /schemes/search

Query:

```ts
interface SearchSchemesQuery {
  organisation_id: string;
  q: string;
  limit?: number;
}
```

Response:

```json
{
  "items": [
    {
      "scheme_id": "pm_mvy",
      "name": "Pradhan Mantri Matru Vandana Yojana",
      "score": 0.87,
      "search_mode": "faiss"
    }
  ]
}
```

### POST /admin/schemes

Headers: `X-Admin-Token: <ADMIN_API_TOKEN>`

TypeScript request:

```ts
export interface CreateSchemeRequest {
  organisation_id: string;
  id: string;
  category_code?: string;
  name: string;
  description: string;
  plain_language_summary: string;
  ministry: string;
  state_code: string | null;
  benefit_type: string;
  benefit_amount: string;
  application_url: string | null;
  valid_from: string | null;
  valid_until: string | null;
  source_url: string;
  eligibility_rule: EligibilityCriteria;
}
```

Pydantic:

```python
class CreateSchemeRequest(BaseModel):
    organisation_id: str
    id: str
    category_code: str | None = None
    name: str
    description: str
    plain_language_summary: str
    ministry: str
    state_code: str | None = None
    benefit_type: str
    benefit_amount: str
    application_url: str | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    source_url: str
    eligibility_rule: EligibilityCriteriaModel
```

Response `201`:

```json
{
  "id": "pm_kisan",
  "version": 1,
  "status": "draft",
  "validation_warnings": []
}
```

Errors:

| Status | Code | Exact behavior |
|---|---|---|
| 401 | ADMIN_TOKEN_INVALID | Return "Admin token is invalid." |
| 409 | SCHEME_ID_EXISTS | Do not update existing scheme. |
| 422 | RULE_CONTRADICTION | Reject save. |
| 422 | BROKEN_EXCLUSION_REFERENCE | Reject save and list missing scheme IDs. |

### PATCH /admin/schemes/{id}

Same body as create, all fields optional except `organisation_id` and `change_summary`.

Behavior:

1. Validate merged scheme and rule.
2. Insert `scheme_versions` snapshot.
3. Deactivate previous active rule.
4. Insert new rule version.
5. Set scheme `status='draft'` unless `publish=true`.

### POST /admin/schemes/{id}/publish

Body:

```json
{
  "organisation_id": "00000000-0000-0000-0000-000000000001"
}
```

Behavior: set `status='active'`, `is_active=true`, and rebuild FAISS index asynchronously.

### POST /admin/schemes/{id}/archive

Body:

```json
{
  "organisation_id": "00000000-0000-0000-0000-000000000001",
  "reason": "Scheme closed by ministry notice."
}
```

Behavior: set `status='archived'`, `is_active=false`; keep data for audit.

### POST /admin/ingestion/myscheme

TypeScript:

```ts
interface MySchemeIngestionRequest {
  organisation_id: string;
  mode: "api" | "json_file" | "csv";
  source_uri?: string;
  dry_run: boolean;
}
```

Response:

```json
{
  "ingestion_run_id": "b70fae33-0a22-49db-afdc-5b12dc1a33be",
  "status": "started"
}
```

Error `424 INGESTION_SOURCE_UNAVAILABLE`:

```json
{
  "error": {
    "code": "INGESTION_SOURCE_UNAVAILABLE",
    "message": "MyScheme API base URL or credentials are not configured. Use json_file or csv mode.",
    "field": "MYSCHEME_API_BASE_URL",
    "request_id": "req_01JDEF"
  }
}
```

### POST /admin/index/rebuild

Body:

```json
{
  "organisation_id": "00000000-0000-0000-0000-000000000001",
  "index_name": "schemes_active"
}
```

Response:

```json
{
  "index_name": "schemes_active",
  "scheme_count": 25,
  "embedding_model": "intfloat/multilingual-e5-small",
  "status": "rebuilt"
}
```

### GET /health

Response:

```json
{
  "status": "ok",
  "database": "ok",
  "faiss_index": "ok",
  "version": "phase-1"
}
```

## Architecture and Implementation Approach

### Libraries

Backend:

```txt
fastapi>=0.115
uvicorn[standard]>=0.30
sqlalchemy[asyncio]>=2.0
asyncpg>=0.29
alembic>=1.13
pydantic>=2.7
pydantic-settings>=2.3
experta>=1.9
faiss-cpu>=1.8
sentence-transformers>=3.0
apscheduler>=3.10
typer>=0.12
rich>=13.7
orjson>=3.10
pytest>=8.2
pytest-asyncio>=0.23
httpx>=0.27
```

### Core Function Signatures

```python
async def match_profile(request: MatchProfileRequest, db: AsyncSession) -> MatchProfileResponse: ...

class EligibilityEngine:
    def evaluate(self, profile: UserProfileInputModel, schemes: list[SchemeWithRule]) -> EligibilityEvaluation: ...
    def evaluate_scheme(self, profile: UserProfileInputModel, scheme: SchemeWithRule) -> SchemeEvaluation: ...
    def evaluate_criterion(self, criterion_id: str, expected: object, actual: object) -> CriterionResult: ...

def validate_rule(criteria: EligibilityCriteriaModel, known_scheme_ids: set[str]) -> list[ValidationIssue]: ...

async def rebuild_faiss_index(organisation_id: UUID, index_name: str) -> FaissBuildResult: ...

async def expire_schemes(today: date, db: AsyncSession) -> ExpiryRunResult: ...
```

### Data Flow for /profile/match

1. Validate request with Pydantic.
2. Load active schemes and latest active eligibility rule:

```sql
SELECT s.*, r.criteria, r.explanation_templates
FROM schemes s
JOIN LATERAL (
  SELECT *
  FROM eligibility_rules r
  WHERE r.scheme_id = s.id
    AND r.organisation_id = s.organisation_id
    AND r.is_active = true
  ORDER BY r.version DESC
  LIMIT 1
) r ON true
WHERE s.organisation_id = :organisation_id
  AND s.is_active = true
  AND s.status = 'active'
  AND (s.valid_until IS NULL OR s.valid_until >= CURRENT_DATE);
```

3. Convert each scheme/rule into Experta facts.
4. Evaluate exclusions first.
5. Evaluate scalar criteria.
6. Evaluate custom criteria.
7. Compute matched, failed, and unknown criterion arrays.
8. Build `matched_schemes`, `near_miss_schemes`, and optional `incomplete_schemes`.
9. Sort matched schemes by benefit type priority, then score, then name.
10. Return response with request ID.

### Experta Implementation

Use Experta for rule orchestration, but keep criterion evaluation in pure Python functions so tests remain simple and deterministic.

```python
from experta import Fact, KnowledgeEngine, Rule


class ProfileFact(Fact):
    pass


class SchemeRuleFact(Fact):
    pass


class SchemeEligibilityEngine(KnowledgeEngine):
    def __init__(self, evaluator: CriterionEvaluator) -> None:
        super().__init__()
        self.evaluator = evaluator
        self.results: list[SchemeEvaluation] = []

    @Rule(ProfileFact(), SchemeRuleFact())
    def evaluate_scheme(self) -> None:
        # Pull declared facts from engine fact list and call evaluator.
        ...
```

### Rule Validation

Validation must return all issues at once.

Required issue IDs:

```txt
RULE_MISSING_REQUIRED_DOCUMENTS_ARRAY
RULE_CONTRADICTION
NEGATIVE_THRESHOLD
INVALID_STATE_CODE
BROKEN_EXCLUSION_REFERENCE
INVALID_CUSTOM_OPERATOR
EMPTY_DOCUMENT_NAME
EMPTY_SUBSTITUTE_INSTRUCTIONS
```

### Seed Data Requirements

The seed file must be JSON with this shape:

```json
{
  "version": "central_schemes.v1",
  "source_last_checked_at": "2026-05-08T00:00:00+05:30",
  "schemes": []
}
```

The file must include at least these 25 records. If an official rule is more restrictive than shown here, implementation must encode the official restriction and set `verification_status="verified"` only after source review. Until then, records are valid demo seed records but marked `needs_admin_review`.

| ID | Scheme | Required criteria to encode | Required documents and substitutes |
|---|---|---|---|
| `pm_kisan` | PM-KISAN | `occupation_type=farmer`, land record present, `has_bank_account=true`, exclusions for income tax payer and institutional landholder in `custom_criteria` | Aadhaar, bank passbook, land record; substitute: revenue record extract, bank statement |
| `pm_uy` | PM Ujjwala Yojana | adult female, poor household marker, `has_lpg_connection=false` | Aadhaar, ration card, bank passbook; substitute: family composition certificate |
| `pmay_g` | PMAY-Gramin | rural household, `has_pucca_house=false`, deprivation marker | Aadhaar, job card or SECC reference, bank passbook; substitute: panchayat housing certificate |
| `pmjay` | Ayushman Bharat PM-JAY | SECC deprivation or occupational vulnerable category | Aadhaar or ration card; substitute: family ID where accepted |
| `pmjdy` | Pradhan Mantri Jan Dhan Yojana | age >= 10, `has_bank_account=false` | Aadhaar, address proof; substitute: NREGA job card |
| `apy` | Atal Pension Yojana | age 18-40, bank account, not income tax payer | Aadhaar, bank passbook; substitute: bank account statement |
| `pmsby` | Pradhan Mantri Suraksha Bima Yojana | age 18-70, bank account | Aadhaar, bank passbook; substitute: bank statement |
| `pmjjby` | Pradhan Mantri Jeevan Jyoti Bima Yojana | age 18-50, bank account | Aadhaar, bank passbook; substitute: bank statement |
| `ssy` | Sukanya Samriddhi Yojana | beneficiary gender female, age <= 10 | birth certificate, guardian ID, address proof; substitute: hospital birth record |
| `ignoaps` | Indira Gandhi National Old Age Pension Scheme | age >= 60, BPL | age proof, BPL card, bank passbook; substitute: panchayat age certificate |
| `ignwps` | Indira Gandhi National Widow Pension Scheme | female, widowed, age 40-79, BPL | widow certificate or death certificate of spouse, BPL card; substitute: panchayat certificate |
| `igndps` | Indira Gandhi National Disability Pension Scheme | age 18-79, BPL, disability >= 80 in custom criteria | disability certificate, BPL card; substitute: UDID card |
| `nfbs` | National Family Benefit Scheme | BPL, death of primary breadwinner age 18-59 in custom criteria | death certificate, BPL card, applicant ID; substitute: panchayat death record |
| `mgnrega` | MGNREGA Job Card | rural, age >= 18, willing manual work | Aadhaar, residence proof, photos; substitute: panchayat residence certificate |
| `pmmvy` | Pradhan Mantri Matru Vandana Yojana | pregnant/lactating woman, age >= 19, first living child or allowed second girl child in custom criteria | MCP card, Aadhaar, bank passbook; substitute: health sub-centre record |
| `jsy` | Janani Suraksha Yojana | pregnant woman, poor/SC/ST marker depending location | MCP card, bank passbook, caste/BPL proof; substitute: ASHA certificate |
| `anganwadi_services` | Anganwadi Services | child under 6 or pregnant/lactating woman | birth record or pregnancy record; substitute: Anganwadi worker certification |
| `pm_vishwakarma` | PM Vishwakarma | artisan/craftsperson, age >= 18, not already covered by listed enterprise schemes | Aadhaar, mobile, bank account, occupation proof; substitute: gram panchayat artisan certificate |
| `pm_svanidhi` | PM SVANidhi | street vendor, urban/local body vendor proof | vending certificate, Aadhaar, bank passbook; substitute: letter of recommendation |
| `stand_up_india` | Stand-Up India | SC/ST or woman entrepreneur, age >= 18, greenfield enterprise | caste certificate where applicable, project report, bank account; substitute: self-declaration only where bank accepts |
| `mudra` | PM Mudra Yojana | non-farm micro enterprise need | ID proof, address proof, business proof; substitute: Udyam registration |
| `post_matric_sc` | Post-Matric Scholarship for SC Students | SC student, post-matric course, income cap in `max_annual_income` | caste certificate, income certificate, marksheet, bank passbook; substitute: fee receipt for admission proof |
| `pre_matric_sc` | Pre-Matric Scholarship for SC Students | SC student class 9-10, income cap | caste certificate, income certificate, school certificate; substitute: bonafide certificate |
| `pmfby` | Pradhan Mantri Fasal Bima Yojana | farmer, notified crop/season in custom criteria | land record, sowing certificate, bank account; substitute: tenant certificate where accepted |
| `kcc` | Kisan Credit Card | farmer/fisher/animal husbandry occupation | land or activity proof, ID, bank account; substitute: lease agreement or panchayat certificate |
| `pm_sym` | PM Shram Yogi Maandhan | unorganised worker, age 18-40, monthly income <= 15000, not EPFO/ESIC/NPS in custom criteria | Aadhaar, bank passbook; substitute: self-certification of occupation |

Example seed rule for `pm_sym`:

```json
{
  "id": "pm_sym",
  "name": "Pradhan Mantri Shram Yogi Maandhan",
  "description": "Voluntary pension scheme for eligible unorganised workers.",
  "plain_language_summary": "You can get a monthly pension after old age if you join and make monthly contributions.",
  "ministry": "Ministry of Labour and Employment",
  "state_code": null,
  "benefit_type": "pension",
  "benefit_amount": "Pension benefit as notified by scheme rules",
  "application_url": "https://maandhan.in/",
  "source_url": "https://maandhan.in/",
  "verification_status": "needs_admin_review",
  "eligibility_rule": {
    "min_age": 18,
    "max_age": 40,
    "occupation_types": ["unorganised_worker"],
    "max_annual_income": 180000,
    "required_documents": [
      {
        "name": "Aadhaar",
        "is_mandatory": true,
        "accepted_substitutes": [
          {
            "name": "Aadhaar enrolment slip",
            "instructions": "Visit an Aadhaar Seva Kendra or CSC to retrieve or complete Aadhaar enrolment.",
            "estimated_cost_inr": 0,
            "estimated_time_days": 7,
            "issuing_authority": "UIDAI"
          }
        ]
      },
      {
        "name": "Bank passbook",
        "is_mandatory": true,
        "accepted_substitutes": [
          {
            "name": "Bank account statement",
            "instructions": "Ask your bank branch or banking correspondent for a recent account statement.",
            "estimated_cost_inr": 0,
            "estimated_time_days": 1,
            "issuing_authority": "Bank or post office"
          }
        ]
      }
    ],
    "custom_criteria": [
      {
        "field": "is_epfo_esic_nps_member",
        "operator": "equals",
        "value": false,
        "how_to_qualify": "This scheme is for workers not already covered by EPFO, ESIC, or NPS."
      }
    ]
  }
}
```

## Environment-Specific Implementation Notes

| Component | Local / GPU production | Hosted demo / free tier |
|---|---|---|
| API host | `FASTAPI_HOST=0.0.0.0`, `FASTAPI_PORT=8000` | Render web service, `PORT` provided by Render |
| Database | `DATABASE_URL=postgresql+asyncpg://adhikarai:adhikarai@localhost:5432/adhikarai` | `DATABASE_URL=<Neon pooled async URL>` |
| Admin token | `ADMIN_API_TOKEN=<local secret>` | `ADMIN_API_TOKEN=<Render secret>` |
| Eligibility engine | `ELIGIBILITY_ENGINE=experta` | `ELIGIBILITY_ENGINE=experta` |
| Embeddings provider | `EMBEDDING_PROVIDER=sentence_transformers` | `EMBEDDING_PROVIDER=sentence_transformers` |
| Embedding model | `EMBEDDING_MODEL=intfloat/multilingual-e5-small` | `EMBEDDING_MODEL=intfloat/multilingual-e5-small` |
| FAISS path | `FAISS_INDEX_DIR=./data/faiss` | `FAISS_INDEX_DIR=/opt/render/project/src/data/faiss` |
| Scheduler | `ENABLE_SCHEDULER=true` | `ENABLE_SCHEDULER=true` |
| Expiry schedule | `EXPIRY_CHECK_CRON=0 2 * * *`, `APP_TIMEZONE=Asia/Kolkata` | same |
| MyScheme ingestion | `MYSCHEME_INGESTION_MODE=json_file`, `MYSCHEME_API_BASE_URL=` empty by default | `MYSCHEME_INGESTION_MODE=csv`, `MYSCHEME_API_BASE_URL=` empty until official access |
| Health ping | optional | UptimeRobot pings `GET /health` every 10 minutes |

External reference endpoints locked for later compatibility:

- Groq chat endpoint for later phases: `https://api.groq.com/openai/v1/chat/completions`, model `llama-3.3-70b-versatile`.
- Groq ASR endpoint for later phases: `https://api.groq.com/openai/v1/audio/transcriptions`, model `whisper-large-v3-turbo`.
- Google TTS endpoint for later phases: `https://texttospeech.googleapis.com/v1/text:synthesize`.
- DigiLocker beta/public OAuth base for later phases: `https://betaapi.digitallocker.gov.in/public`.

## File and Folder Structure

```txt
adhikarai/
  backend/
    app/
      __init__.py
      main.py
      core/
        config.py
        errors.py
        logging.py
        security.py
      db/
        base.py
        session.py
        migrations/
        models/
          organisation.py
          admin_user.py
          scheme.py
          eligibility_rule.py
          ingestion.py
          notification.py
      schemas/
        common.py
        profile.py
        scheme.py
        match.py
        admin.py
        ingestion.py
      services/
        eligibility/
          engine.py
          experta_engine.py
          criteria.py
          explanations.py
          validation.py
        search/
          embeddings.py
          faiss_index.py
        ingestion/
          base.py
          myscheme.py
          csv_importer.py
        jobs/
          expiry_checker.py
          scheduler.py
      api/
        routes/
          health.py
          profile_match.py
          schemes.py
          admin_schemes.py
          admin_ingestion.py
          admin_index.py
      cli/
        main.py
        scheme_commands.py
        index_commands.py
        expiry_commands.py
      seeds/
        central_schemes.v1.json
    tests/
      unit/
        test_rule_validation.py
        test_criteria_evaluator.py
        test_near_miss.py
      integration/
        test_profile_match_api.py
        test_admin_scheme_api.py
        test_faiss_search.py
        test_expiry_checker.py
  docs/
    prd/
      phase-1-foundation-eligibility-engine.md
```

## Testing Requirements

### Unit Tests

1. `test_rule_validation_rejects_min_age_gt_max_age`
   - Input: `{"min_age": 60, "max_age": 18}`
   - Expected: `RULE_CONTRADICTION`, field `criteria.min_age`.

2. `test_cross_scheme_exclusion_blocks_match`
   - Profile: `existing_scheme_ids=["pmay_g"]`
   - Rule: `exclusion_scheme_ids=["pmay_g"]`
   - Expected: ineligible reason `already_receives_excluded_scheme`, not near miss.

3. `test_near_miss_exactly_one_failure`
   - Profile income `130000`
   - Rule `max_annual_income=120000`, all other criteria match.
   - Expected: near miss with failed criterion `annual_income`.

4. `test_two_failures_not_near_miss`
   - Profile income too high and age too low.
   - Expected: neither matched nor near miss.

5. `test_missing_profile_field_is_unknown_not_failed`
   - Profile missing caste.
   - Rule requires caste SC.
   - Expected: `unknown_criteria=["caste_category"]`.

6. `test_required_document_substitute_validation`
   - Substitute missing instructions.
   - Expected: `EMPTY_SUBSTITUTE_INSTRUCTIONS`.

### Integration Tests

1. `POST /profile/match` with farmer profile
   - Input: profile from API example.
   - Expected: includes `pm_kisan` in `matched_schemes`.

2. `POST /admin/schemes` duplicate ID
   - First request creates `test_scheme`.
   - Second request same ID returns `409 SCHEME_ID_EXISTS`.

3. `POST /admin/schemes/{id}/publish`
   - Expected: scheme status becomes `active`, previous draft version remains in `scheme_versions`.

4. `GET /schemes/search?q=pregnant woman`
   - Expected: top 10 includes `pmmvy` or `jsy` after seed load.

5. Expiry checker
   - Seed scheme with `valid_until=yesterday`.
   - Run `expire_schemes`.
   - Expected: `status='expired'`, `is_active=false`, admin notification inserted.

### Manual Test Cases

1. Low-income widow
   - Profile:
     ```json
     {"age":45,"gender":"female","marital_status":"widowed","annual_income":50000,"state_code":"IN-UP","existing_scheme_ids":[],"custom_attributes":{"is_bpl":true}}
     ```
   - Expected: `ignwps` matched.

2. Street vendor without vendor certificate
   - Profile:
     ```json
     {"age":32,"occupation_type":"street_vendor","annual_income":90000,"state_code":"IN-DL","existing_scheme_ids":[],"custom_attributes":{"has_vendor_certificate":false}}
     ```
   - Expected: `pm_svanidhi` near miss if only certificate criterion fails.

3. Incomplete profile
   - Profile: `{"age":30,"existing_scheme_ids":[]}`
   - Expected: no false matches; if `include_incomplete=true`, schemes needing missing gender/income appear in `incomplete_schemes`.

## Known Constraints and Edge Cases

1. MyScheme public API access is not guaranteed. The ingestion layer must not scrape web pages unless a future PRD explicitly approves scraping and legal review.
2. Seed scheme rules can become outdated. The system must store `source_last_checked_at` and `verification_status`.
3. Phase 1 does not implement beneficiary authentication.
4. Phase 1 does not store real user profiles after matching.
5. Phase 1 does not collect Aadhaar numbers.
6. State-specific implementation differences for central schemes are not fully modeled except through `state_codes` and `custom_criteria`.
7. Experta is used for orchestration, but simple criteria evaluation must remain testable outside Experta.
8. FAISS index files on Render ephemeral disk may be lost after redeploy. Rebuild on boot if metadata exists but file is missing.
9. Neon free tier connection limits require async connection pool size <= 5.
10. Rules with dates such as application windows are represented by `valid_from` and `valid_until`; per-district windows are deferred.
11. If an admin archives a scheme while a match request is running, current request may include it; next request must not.
12. Plain-language explanations are English only in Phase 1.
13. "Illiterate user" constraints affect data returned now: explanations must be short, concrete, and translation-ready; no legalistic paragraphs.

## Dependencies on Previous Phases

None. Phase 1 is the foundation.

