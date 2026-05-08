# AdhikarAI PRD - Phase 5: NGO and CSC Operator Dashboard plus Admin Panel

## Phase Summary

Phase 5 adds operator-facing and admin-facing surfaces:

- NGO/CSC dashboard at `/dashboard`
- Beneficiary management
- Notes and follow-up workflows
- Bulk eligibility CSV processing
- Application status kanban/list views
- Exports
- Operator training and scheme guide
- Scheme update notifications
- Unmatched query analytics
- Scheme admin CRUD with rule editor, validation, staging, preview, publish, and diff
- Scheme change history
- Platform analytics
- LLM response quality monitoring
- Rate limiting
- Role permissions
- Multi-tenant enforcement

Primary users:

- CSC operator or NGO field worker who assists multiple beneficiaries daily.
- NGO admin who manages operators and sees organisation-level data.
- Super admin who manages scheme knowledge base and platform-wide analytics.

Key product rule: operator tools must be dense and efficient, while beneficiary-facing flows remain low-literacy and voice-first.

## Goals and Success Criteria

1. Enable operators to manage beneficiaries.
   - Success: operator can create, update, search, and track assigned beneficiaries.
   - Success: operator can record notes and follow-up dates.

2. Enable bulk eligibility checks.
   - Success: CSV upload with up to 500 rows processes asynchronously.
   - Success: result CSV contains matched schemes, near misses, failed row errors, and processing status.

3. Provide application workflow visibility.
   - Success: operator can drag cards across kanban columns or edit status in list view.
   - Success: changes update the same `application_statuses` records used by the PWA.

4. Improve scheme knowledge base quality.
   - Success: unmatched query logs are grouped by normalized query and frequency.
   - Success: admins can export unmatched query CSV.

5. Support safe scheme administration.
   - Success: scheme changes are saved as draft, previewed, validated, diffed, and then published.
   - Success: every rule change has an audit trail with before/after diff.

6. Enforce multi-tenant access.
   - Success: NGO admins see only their organisation.
   - Success: operators see only assigned beneficiaries.
   - Success: super admins see all organisations.

7. Add rate limits.
   - Success: user requests above 100/day return `429`.
   - Success: operator requests above 1000/day return `429`.

## User Stories

1. Operator creates beneficiary
   - Operator opens `/dashboard/beneficiaries/new`.
   - Enters name, phone, state, language, and profile facts.
   - Runs eligibility and assigns schemes.
   - Error: missing state shows "State is required to run eligibility."

2. Operator follow-up
   - Operator sets "Follow up on 2026-05-12" with note "Bring income certificate."
   - On that date, beneficiary appears at top of dashboard.

3. Bulk CSV
   - NGO admin uploads 300 beneficiaries.
   - Progress bar updates.
   - Completed result CSV downloads with matched schemes per row.
   - Rows with invalid age show row-level error and do not block valid rows.

4. Kanban status
   - Operator drags beneficiary scheme card from documents to submitted.
   - Status updates and event is recorded.
   - If offline or API fails, card returns to previous column and shows exact error.

5. Scheme rule update
   - Super admin edits PM-KISAN income exclusion rule.
   - Saves draft, previews affected matches on sample profiles, sees diff, publishes.
   - Operators in relevant states receive notification.

6. Unmatched queries
   - Admin opens unmatched query table.
   - Sees repeated query "housing for single woman no ration card".
   - Exports CSV for knowledge base improvement.

7. LLM quality monitoring
   - Session where agent asked 9 questions without result is flagged.
   - Admin reviews transcript and marks as reviewed.

8. Rate limit
   - User exceeds 100 queries/day.
   - API returns `429 RATE_LIMIT_EXCEEDED`.
   - User-facing message: "You have used today's limit. Please try tomorrow or visit a CSC."

## Functional Requirements

1. Dashboard must be a Next.js route group under `/dashboard`.
2. Dashboard requires authenticated role-based access.
3. Roles: `super_admin`, `ngo_admin`, `operator`.
4. Role matrix:
   - `super_admin`: all organisations, scheme admin, analytics, unmatched logs, quality monitoring.
   - `ngo_admin`: own organisation beneficiaries, operators, exports, dashboard analytics, scheme view only.
   - `operator`: own assigned beneficiaries only, status updates, notes, eligibility checks.
5. Every dashboard API must derive organisation scope from JWT claims, not request body alone.
6. Beneficiary record must include name, phone, state, language, profile fields, household members, assigned schemes, application statuses, notes, and follow-up flags.
7. Beneficiary phone is optional because some rural beneficiaries share phones.
8. Beneficiary search must support name, phone, village, scheme, and status.
9. Follow-up due today list must appear at top of dashboard home.
10. Notes must be free text up to 5000 characters.
11. Follow-up flag must include due date and optional reason.
12. Bulk CSV upload must accept max 500 rows and max 2 MB.
13. CSV headers must match documented profile field names.
14. Bulk processing must show progress with polling or Server-Sent Events.
15. Bulk result CSV must include original row number, beneficiary name, matched scheme IDs/names, near-miss scheme IDs/names, profile completeness, and errors.
16. Kanban columns: not started, documents, submitted, approved.
17. Kanban must map to application statuses:
    - not started -> `not_started`
    - documents -> `documents_gathering`
    - submitted -> `submitted` or `pending`
    - approved -> `approved`
18. Rejected applications appear in list filters, not kanban default columns.
19. Export must support date range, scheme, status, operator, and state filters.
20. Export must stream CSV for large datasets.
21. Operator training module must have 5 steps:
    - create beneficiary
    - run eligibility
    - explain documents
    - update application status
    - set follow-up
22. Scheme guide page must list all active schemes with plain-language summaries and filters by category/state.
23. Scheme update notifications must trigger when:
    - a scheme is added,
    - eligibility rule changes,
    - scheme expires in < 30 days.
24. Operators in relevant state receive notification; central schemes notify all operators.
25. Optional SMS notification uses MSG91 only if operator phone exists and SMS opt-in is true.
26. Unmatched queries must log original query text, normalized query text, language, timestamp, profile completeness, and session ID.
27. Unmatched query table must group by normalized query and sort by frequency descending by default.
28. Scheme admin editor must use field-by-field form, not raw JSON.
29. Rule editor must support all Phase 1 criteria fields and `custom_criteria`.
30. Rule validation must run before draft save and before publish.
31. Draft save may allow warnings but not errors.
32. Publish is blocked by any validation error.
33. Diff view must show scheme field changes and rule JSON changes.
34. Change history must include timestamp, changed by, before snapshot, after snapshot, and change summary.
35. Platform analytics must include query volume, language breakdown, top matched schemes, top near-miss schemes, average profile completeness, and voice vs text ratio.
36. LLM quality monitoring must flag:
    - agent asked more than 8 questions without result,
    - user abandoned session after at least 2 agent questions and no result,
    - ASR low-confidence rate above 3 consecutive turns,
    - translation failure in a session.
37. Admin can mark quality flags as reviewed with notes.
38. Rate limiting must use Redis counters.
39. Per-user limit: 100 eligibility/agent queries per day.
40. Per-operator limit: 1000 eligibility/agent queries per day.
41. Rate limit key must include organisation ID and actor ID.
42. API response for rate limit must be `429` with retry date.
43. All dashboard pages must be usable on desktop and tablet; mobile support is acceptable but not primary.
44. Dashboard must use dense tables/forms, not marketing-style hero layouts.
45. No UI card inside another card.
46. Audit logs must record admin and operator write actions.

## Data Models

Phase 5 uses all prior tables. New/modified tables are below.

### SQL DDL

```sql
CREATE TABLE organisation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    admin_user_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('super_admin', 'ngo_admin', 'operator')),
    phone_e164 TEXT,
    email TEXT,
    display_name TEXT NOT NULL,
    sms_opt_in BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (user_id IS NOT NULL OR admin_user_id IS NOT NULL)
);

CREATE TABLE beneficiaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    assigned_operator_id UUID REFERENCES organisation_members(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    phone_e164 TEXT,
    state_code TEXT NOT NULL,
    language_code TEXT NOT NULL DEFAULT 'hi',
    village TEXT,
    district TEXT,
    source TEXT NOT NULL DEFAULT 'operator' CHECK (source IN ('operator', 'self_signup', 'csv_import')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (state_code ~ '^IN-[A-Z]{2}$')
);

CREATE INDEX idx_beneficiaries_org_operator ON beneficiaries (organisation_id, assigned_operator_id);
CREATE INDEX idx_beneficiaries_search ON beneficiaries USING GIN (to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(phone_e164,'') || ' ' || coalesce(village,'')));

CREATE TABLE beneficiary_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    beneficiary_id UUID NOT NULL REFERENCES beneficiaries(id) ON DELETE CASCADE,
    author_member_id UUID NOT NULL REFERENCES organisation_members(id),
    note TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE beneficiary_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    beneficiary_id UUID NOT NULL REFERENCES beneficiaries(id) ON DELETE CASCADE,
    assigned_operator_id UUID REFERENCES organisation_members(id) ON DELETE SET NULL,
    due_date DATE NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'completed', 'cancelled')),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_followups_due ON beneficiary_followups (organisation_id, due_date, status);

CREATE TABLE beneficiary_scheme_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    beneficiary_id UUID NOT NULL REFERENCES beneficiaries(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    scheme_id TEXT NOT NULL REFERENCES schemes(id),
    assigned_by UUID REFERENCES organisation_members(id),
    assignment_source TEXT NOT NULL CHECK (assignment_source IN ('eligibility_match', 'manual', 'bulk_csv')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, beneficiary_id, scheme_id)
);

CREATE TABLE bulk_eligibility_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    created_by UUID NOT NULL REFERENCES organisation_members(id),
    original_filename TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'completed_with_errors', 'failed')),
    total_rows INTEGER NOT NULL DEFAULT 0,
    processed_rows INTEGER NOT NULL DEFAULT 0,
    failed_rows INTEGER NOT NULL DEFAULT 0,
    result_storage_url TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE bulk_eligibility_rows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    job_id UUID NOT NULL REFERENCES bulk_eligibility_jobs(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    input_payload JSONB NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'processed', 'failed')),
    matched_schemes JSONB NOT NULL DEFAULT '[]'::jsonb,
    near_miss_schemes JSONB NOT NULL DEFAULT '[]'::jsonb,
    profile_completeness INTEGER,
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, job_id, row_number)
);

CREATE TABLE operator_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    recipient_member_id UUID REFERENCES organisation_members(id) ON DELETE CASCADE,
    state_code TEXT,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    read_at TIMESTAMPTZ,
    sms_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE unmatched_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    conversation_session_id UUID REFERENCES conversation_sessions(id) ON DELETE SET NULL,
    profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    original_query_text TEXT NOT NULL,
    normalized_query_text TEXT NOT NULL,
    language_code TEXT NOT NULL,
    profile_completeness INTEGER,
    result_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_unmatched_queries_group ON unmatched_queries (organisation_id, normalized_query_text);

CREATE TABLE scheme_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    scheme_id TEXT REFERENCES schemes(id) ON DELETE SET NULL,
    draft_payload JSONB NOT NULL,
    validation_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL CHECK (status IN ('draft', 'previewed', 'published', 'discarded')),
    created_by UUID NOT NULL REFERENCES organisation_members(id),
    updated_by UUID REFERENCES organisation_members(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE scheme_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    scheme_id TEXT,
    draft_id UUID REFERENCES scheme_drafts(id) ON DELETE SET NULL,
    action TEXT NOT NULL CHECK (action IN ('create_draft', 'update_draft', 'preview', 'publish', 'archive', 'discard')),
    changed_by UUID NOT NULL REFERENCES organisation_members(id),
    before_snapshot JSONB,
    after_snapshot JSONB,
    diff JSONB NOT NULL DEFAULT '{}'::jsonb,
    change_summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE quality_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    conversation_session_id UUID REFERENCES conversation_sessions(id) ON DELETE SET NULL,
    profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    flag_type TEXT NOT NULL CHECK (flag_type IN ('too_many_questions', 'abandoned_mid_flow', 'asr_low_confidence_loop', 'translation_failure')),
    severity TEXT NOT NULL DEFAULT 'warning' CHECK (severity IN ('info', 'warning', 'critical')),
    details JSONB NOT NULL,
    reviewed_by UUID REFERENCES organisation_members(id),
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE rate_limit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    actor_type TEXT NOT NULL CHECK (actor_type IN ('guest', 'user', 'operator', 'admin')),
    actor_id TEXT NOT NULL,
    limit_key TEXT NOT NULL,
    count INTEGER NOT NULL,
    limit_value INTEGER NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    actor_member_id UUID REFERENCES organisation_members(id),
    actor_user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    before_snapshot JSONB,
    after_snapshot JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Python SQLAlchemy Models

```python
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrganisationMember(Base):
    __tablename__ = "organisation_members"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    admin_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(Text, nullable=False)
    phone_e164: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    sms_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    assigned_operator_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisation_members.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    phone_e164: Mapped[str | None] = mapped_column(Text)
    state_code: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="hi")
    village: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BeneficiaryNote(Base):
    __tablename__ = "beneficiary_notes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    beneficiary_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False)
    author_member_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisation_members.id"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BeneficiaryFollowup(Base):
    __tablename__ = "beneficiary_followups"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    beneficiary_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False)
    assigned_operator_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisation_members.id", ondelete="SET NULL"))
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="open")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BulkEligibilityJob(Base):
    __tablename__ = "bulk_eligibility_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisation_members.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_storage_url: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SchemeDraft(Base):
    __tablename__ = "scheme_drafts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    scheme_id: Mapped[str | None] = mapped_column(Text, ForeignKey("schemes.id", ondelete="SET NULL"))
    draft_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    validation_result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisation_members.id"), nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisation_members.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

## API Specification

All dashboard APIs require authenticated JWT with member role claims:

```ts
interface DashboardClaims {
  user_id: string;
  member_id: string;
  organisation_id: string;
  role: "super_admin" | "ngo_admin" | "operator";
}
```

### Shared TypeScript Types

```ts
export interface Beneficiary {
  id: string;
  name: string;
  phone_e164?: string;
  state_code: string;
  language_code: string;
  village?: string;
  district?: string;
  profile_id: string;
  assigned_operator_id?: string;
  application_statuses: Array<{ scheme_id: string; status: string }>;
  follow_up?: { due_date: string; reason?: string };
}

export interface CreateBeneficiaryRequest {
  name: string;
  phone_e164?: string;
  state_code: string;
  language_code: string;
  village?: string;
  district?: string;
  assigned_operator_id?: string;
  profile: Partial<UserProfileInput>;
  household_members?: HouseholdMemberProfile[];
}

export interface BulkJobStatus {
  id: string;
  status: "queued" | "processing" | "completed" | "completed_with_errors" | "failed";
  total_rows: number;
  processed_rows: number;
  failed_rows: number;
  result_storage_url?: string;
}

export interface SchemeDraftPayload {
  scheme: CreateSchemeRequest;
  change_summary: string;
}

export interface ValidationResult {
  errors: Array<{ code: string; field: string; message: string }>;
  warnings: Array<{ code: string; field: string; message: string }>;
}
```

### Shared Pydantic Models

```python
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateBeneficiaryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone_e164: str | None = None
    state_code: str
    language_code: str = "hi"
    village: str | None = None
    district: str | None = None
    assigned_operator_id: UUID | None = None
    profile: dict
    household_members: list[dict] = []


class BeneficiaryResponse(BaseModel):
    id: UUID
    name: str
    phone_e164: str | None
    state_code: str
    language_code: str
    profile_id: UUID
    assigned_operator_id: UUID | None


class BeneficiaryNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=5000)


class FollowupRequest(BaseModel):
    due_date: date
    reason: str | None = Field(default=None, max_length=500)


class BulkJobStatusResponse(BaseModel):
    id: UUID
    status: Literal["queued", "processing", "completed", "completed_with_errors", "failed"]
    total_rows: int
    processed_rows: int
    failed_rows: int
    result_storage_url: str | None = None


class SchemeDraftRequest(BaseModel):
    draft_payload: dict
    change_summary: str = Field(min_length=5, max_length=1000)


class ReviewQualityFlagRequest(BaseModel):
    review_notes: str = Field(min_length=1, max_length=2000)
```

### GET /dashboard/me

Returns member, organisation, role, permissions.

### GET /dashboard/beneficiaries

Query:

```ts
interface BeneficiaryListQuery {
  q?: string;
  state_code?: string;
  scheme_id?: string;
  status?: string;
  followup_due?: "today" | "overdue" | "all";
  assigned_operator_id?: string;
  limit?: number;
  offset?: number;
}
```

Role behavior:

- operator: force `assigned_operator_id=current_member_id`.
- ngo_admin: organisation only.
- super_admin: optional organisation filter.

### POST /dashboard/beneficiaries

Creates beneficiary and profile.

Request:

```json
{
  "name": "Sita Devi",
  "phone_e164": "+919876543210",
  "state_code": "IN-BR",
  "language_code": "hi",
  "village": "Rampur",
  "district": "Gaya",
  "profile": {
    "age": 34,
    "gender": "female",
    "occupation_type": "farmer",
    "annual_income": 85000
  }
}
```

Response `201`: `BeneficiaryResponse`.

### GET /dashboard/beneficiaries/{id}

Returns beneficiary, profile, household members, notes, follow-ups, assigned schemes, statuses.

### PATCH /dashboard/beneficiaries/{id}

Updates beneficiary and profile fields. Operators can update only assigned beneficiaries.

### DELETE /dashboard/beneficiaries/{id}

Soft delete is recommended. If implemented in Phase 5, add `deleted_at` to `beneficiaries`. Response `204`.

### POST /dashboard/beneficiaries/{id}/eligibility

Runs eligibility for beneficiary profile and optionally assigns matches.

Request:

```json
{
  "assign_matched_schemes": true
}
```

Response:

```json
{
  "matched_schemes": [],
  "near_miss_schemes": [],
  "assigned_count": 3
}
```

### POST /dashboard/beneficiaries/{id}/notes

Adds note.

### POST /dashboard/beneficiaries/{id}/followups

Adds follow-up.

### PATCH /dashboard/followups/{id}

Updates status to `completed` or `cancelled`.

### POST /dashboard/bulk-eligibility

Multipart form: `file`.

CSV headers:

```txt
name,phone_e164,state_code,district,village,language_code,age,gender,caste_category,annual_income,land_holding_acres,occupation_type,marital_status,existing_scheme_ids
```

Response:

```json
{
  "job_id": "521e20f1-f43f-43a9-9182-a32417f00001",
  "status": "queued"
}
```

Errors:

| Status | Code | Behavior |
|---|---|---|
| 413 | CSV_TOO_LARGE | "CSV must be 2 MB or smaller." |
| 422 | CSV_TOO_MANY_ROWS | "CSV can include at most 500 rows." |
| 422 | CSV_INVALID_HEADERS | Return missing/unknown headers. |

### GET /dashboard/bulk-eligibility/{job_id}

Returns `BulkJobStatusResponse`.

### GET /dashboard/bulk-eligibility/{job_id}/download

Streams result CSV.

### GET /dashboard/status-board

Query: `operator_id`, `scheme_id`, `state_code`.

Returns kanban columns.

### PATCH /dashboard/application-status/{id}

Same status values as Phase 4. Role scoped.

### GET /dashboard/export/beneficiaries.csv

Streams CSV with filters.

### GET /dashboard/scheme-guide

Returns active scheme summaries. Scheme view only for NGO admin/operator.

### GET /dashboard/operator-notifications

Returns notifications for current member.

### POST /dashboard/operator-notifications/{id}/read

Marks notification read.

### GET /admin/unmatched-queries

Super admin only.

Response:

```json
{
  "items": [
    {
      "normalized_query_text": "housing for single woman no ration card",
      "frequency": 18,
      "languages": ["en", "hi"],
      "latest_at": "2026-05-08T12:00:00+05:30"
    }
  ]
}
```

### GET /admin/unmatched-queries.csv

Streams CSV.

### POST /admin/scheme-drafts

Super admin only.

Request:

```json
{
  "draft_payload": {
    "scheme": {
      "id": "pm_kisan",
      "name": "Pradhan Mantri Kisan Samman Nidhi"
    },
    "eligibility_rule": {}
  },
  "change_summary": "Update PM-KISAN exclusion criteria based on latest scheme guidance."
}
```

Response:

```json
{
  "draft_id": "6100a86b-2de6-4325-a4e6-64403e000001",
  "status": "draft",
  "validation_result": {
    "errors": [],
    "warnings": []
  }
}
```

### POST /admin/scheme-drafts/{id}/preview

Runs validation and returns diff plus sample impact.

Response:

```json
{
  "validation_result": {"errors": [], "warnings": []},
  "diff": {
    "scheme": [],
    "eligibility_rule": [
      {"path": "custom_criteria[1]", "old": null, "new": {"field": "is_income_tax_payer"}}
    ]
  },
  "sample_impact": {
    "profiles_tested": 100,
    "newly_eligible": 4,
    "newly_ineligible": 2
  }
}
```

### POST /admin/scheme-drafts/{id}/publish

Publishes draft to Phase 1 `schemes` and `eligibility_rules`.

Errors:

| Status | Code | Behavior |
|---|---|---|
| 422 | DRAFT_VALIDATION_FAILED | Publish blocked. Return validation errors. |
| 409 | DRAFT_ALREADY_PUBLISHED | No duplicate publish. |

### GET /admin/schemes/{id}/history

Returns scheme audit logs and Phase 1 scheme versions.

### GET /admin/analytics

Query: `date_from`, `date_to`, `organisation_id`.

Response:

```json
{
  "query_volume": {"daily": [{"date": "2026-05-08", "count": 120}]},
  "language_breakdown": [{"language_code": "hi", "count": 80}],
  "top_matched_schemes": [{"scheme_id": "pm_kisan", "count": 42}],
  "top_near_miss_schemes": [{"scheme_id": "pmay_g", "count": 18}],
  "average_profile_completeness": 73.2,
  "voice_vs_text_usage_ratio": {"voice": 0.68, "text": 0.32}
}
```

### GET /admin/quality-flags

Returns quality flags.

### POST /admin/quality-flags/{id}/review

Marks reviewed.

### Rate Limit Error Body

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You have used today's limit. Please try tomorrow or visit a CSC.",
    "field": null,
    "request_id": "req_01JRATE",
    "retry_after_seconds": 3600
  }
}
```

## Architecture and Implementation Approach

### RBAC

Define permissions centrally:

```python
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

ROLE_PERMISSIONS = {
    "super_admin": {"*"},
    "ngo_admin": {"beneficiary:read", "beneficiary:write", "beneficiary:export", "scheme:read", "analytics:read"},
    "operator": {"beneficiary:read", "beneficiary:write", "scheme:read"},
}
```

Dependency:

```python
async def require_permission(permission: str) -> DashboardActor: ...
async def scoped_query(query: Select, actor: DashboardActor, resource: str) -> Select: ...
```

### Bulk Eligibility Processing

Initial implementation can use FastAPI `BackgroundTasks` plus DB progress because volume is capped at 500 rows. Keep queue interface for future worker.

```python
async def create_bulk_job(actor: DashboardActor, file: UploadFile) -> BulkJobStatusResponse: ...
async def process_bulk_job(job_id: UUID) -> None: ...
def parse_beneficiary_csv(content: bytes) -> list[CsvBeneficiaryRow]: ...
async def process_bulk_row(row: CsvBeneficiaryRow) -> BulkRowResult: ...
async def generate_result_csv(job_id: UUID) -> str: ...
```

### Scheme Admin Publishing

1. Admin saves draft.
2. Backend validates draft with Phase 1 `validate_rule`.
3. Preview endpoint computes diff and sample impact.
4. Publish endpoint runs validation again inside transaction.
5. If new scheme, insert into `schemes`; else update existing.
6. Insert new `eligibility_rules` version.
7. Insert `scheme_audit_logs`.
8. Notify relevant operators.
9. Trigger proactive matching from Phase 4.
10. Trigger FAISS index rebuild.

### Analytics Queries

Example top matched schemes:

```sql
SELECT elem->'scheme'->>'id' AS scheme_id, count(*) AS count
FROM conversation_messages,
LATERAL jsonb_array_elements(structured_payload->'matched_schemes') elem
WHERE organisation_id = :organisation_id
  AND created_at BETWEEN :date_from AND :date_to
GROUP BY scheme_id
ORDER BY count DESC
LIMIT 10;
```

Average completeness:

```sql
SELECT avg(profile_completeness)
FROM conversation_sessions
WHERE organisation_id = :organisation_id
  AND created_at BETWEEN :date_from AND :date_to;
```

### Quality Flag Job

Runs every hour.

```python
async def flag_too_many_questions() -> int: ...
async def flag_abandoned_sessions() -> int: ...
async def flag_asr_low_confidence_loops() -> int: ...
async def flag_translation_failures() -> int: ...
```

### Rate Limiting

Redis keys:

```txt
rate:{organisation_id}:user:{user_id}:{yyyy-mm-dd}
rate:{organisation_id}:operator:{member_id}:{yyyy-mm-dd}
rate:{organisation_id}:guest:{session_id}:{yyyy-mm-dd}
```

Function:

```python
async def check_rate_limit(actor_type: str, actor_id: str, organisation_id: UUID, limit: int) -> None:
    key = f"rate:{organisation_id}:{actor_type}:{actor_id}:{date.today().isoformat()}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, seconds_until_next_midnight("Asia/Kolkata"))
    if count > limit:
        raise RateLimitExceeded(retry_after_seconds=await redis.ttl(key))
```

Apply to:

- `/profile/match`
- `/agent/message`
- `/ws/chat`
- `/voice/turn`
- `/dashboard/beneficiaries/{id}/eligibility`
- bulk rows count against operator limit.

## Environment-Specific Implementation Notes

| Component | Local / GPU production | Hosted demo / free tier |
|---|---|---|
| Dashboard URL | `http://localhost:3000/dashboard` | `https://adhikarai.vercel.app/dashboard` |
| Backend URL | `http://localhost:8000` | `https://adhikarai-api.onrender.com` |
| DB | local Postgres | Neon |
| Redis rate limits | local Redis | Upstash |
| CSV result storage | local `/tmp/adhikarai/exports` | Cloudinary or Supabase Storage |
| SMS | `SMS_NOTIFICATIONS_ENABLED=false` default | `SMS_NOTIFICATIONS_ENABLED=true` if MSG91 credits/config exist |
| Background jobs | APScheduler in FastAPI | APScheduler in Render service; keep warm with UptimeRobot |
| Analytics | SQL queries on Postgres | SQL queries on Neon with indexes |

Required env vars:

```txt
DASHBOARD_ENABLED=true
RATE_LIMIT_USER_PER_DAY=100
RATE_LIMIT_OPERATOR_PER_DAY=1000
RATE_LIMIT_GUEST_PER_DAY=50

EXPORT_STORAGE_PROVIDER=cloudinary|supabase|local
EXPORT_MAX_ROWS=5000
BULK_ELIGIBILITY_MAX_ROWS=500
BULK_ELIGIBILITY_MAX_MB=2

SMS_NOTIFICATIONS_ENABLED=false
MSG91_AUTH_KEY=
MSG91_SMS_TEMPLATE_ID=

QUALITY_MONITOR_CRON=0 * * * *
SCHEME_EXPIRY_WARNING_DAYS=30
```

## File and Folder Structure

```txt
adhikarai/
  frontend/
    app/
      dashboard/
        layout.tsx
        page.tsx
        beneficiaries/
          page.tsx
          new/page.tsx
          [id]/page.tsx
        bulk-eligibility/page.tsx
        status-board/page.tsx
        exports/page.tsx
        scheme-guide/page.tsx
        help/page.tsx
      admin/
        layout.tsx
        schemes/
          page.tsx
          new/page.tsx
          drafts/[id]/page.tsx
          [id]/history/page.tsx
        unmatched-queries/page.tsx
        analytics/page.tsx
        quality/page.tsx
    components/
      dashboard/
        DashboardShell.tsx
        BeneficiaryTable.tsx
        BeneficiaryForm.tsx
        FollowupList.tsx
        NotesPanel.tsx
        BulkUpload.tsx
        StatusKanban.tsx
        ExportFilters.tsx
        TrainingWalkthrough.tsx
      admin/
        SchemeRuleEditor.tsx
        RuleCriteriaForm.tsx
        DraftDiffView.tsx
        AnalyticsCharts.tsx
        QualityFlagTable.tsx
        UnmatchedQueriesTable.tsx
    lib/
      dashboard/
        permissions.ts
        columns.ts
        csv.ts
  backend/
    app/
      dashboard/
        rbac.py
        scopes.py
        exports.py
        bulk_eligibility.py
      admin_panel/
        scheme_drafts.py
        diffs.py
        analytics.py
        quality.py
        unmatched_queries.py
      rate_limit/
        middleware.py
        service.py
      api/
        routes/
          dashboard_me.py
          dashboard_beneficiaries.py
          dashboard_bulk.py
          dashboard_status_board.py
          dashboard_exports.py
          dashboard_scheme_guide.py
          dashboard_notifications.py
          admin_scheme_drafts.py
          admin_unmatched_queries.py
          admin_analytics.py
          admin_quality.py
      db/
        models/
          organisation_member.py
          beneficiary.py
          beneficiary_note.py
          beneficiary_followup.py
          bulk_eligibility.py
          operator_notification.py
          unmatched_query.py
          scheme_draft.py
          quality_flag.py
          audit_log.py
          rate_limit_event.py
    tests/
      unit/
        test_rbac.py
        test_rate_limit.py
        test_csv_parser.py
        test_scheme_diff.py
        test_quality_flags.py
      integration/
        test_beneficiary_crud_scoping.py
        test_bulk_eligibility.py
        test_scheme_draft_publish.py
        test_dashboard_exports.py
        test_admin_analytics.py
```

## Testing Requirements

### Unit Tests

1. `test_operator_scope_only_assigned_beneficiaries`
   - Actor role operator, assigned ID A.
   - Query beneficiaries.
   - Expected: only rows with assigned operator A.

2. `test_ngo_admin_scope_own_org`
   - Two organisations.
   - Expected: NGO admin sees only own org.

3. `test_super_admin_can_filter_all_orgs`
   - Expected: super admin sees all when no org filter.

4. `test_rate_limit_user_101st_request`
   - Limit 100.
   - Expected: 101st raises `RATE_LIMIT_EXCEEDED`.

5. `test_csv_rejects_unknown_headers`
   - Header `aadhaar_number`.
   - Expected: `CSV_INVALID_HEADERS`.

6. `test_scheme_diff_nested_rule_change`
   - Old and new custom criteria differ.
   - Expected: diff path includes changed criterion.

7. `test_quality_flag_too_many_questions`
   - Session has 9 assistant question messages and no result.
   - Expected: flag inserted.

### Integration Tests

1. Beneficiary CRUD
   - Create beneficiary as NGO admin.
   - Assign operator.
   - Operator fetches beneficiary.
   - Different operator gets 403.

2. Bulk eligibility
   - Upload CSV with 3 rows: 2 valid, 1 invalid age.
   - Expected: job completed_with_errors, result CSV has 2 processed and 1 error.

3. Kanban update
   - Update status from documents to submitted.
   - Expected: `application_status_events` row inserted.

4. Scheme draft publish
   - Create draft for test scheme.
   - Preview diff.
   - Publish.
   - Expected: Phase 1 scheme updated, rule version incremented, audit log inserted, notification scheduled.

5. Unmatched query grouping
   - Insert multiple queries with same normalized text.
   - Expected: grouped frequency descending.

6. Analytics
   - Seed messages and voice turns.
   - Expected: language breakdown and voice/text ratio match fixtures.

### Manual Test Cases

1. Operator daily workflow
   - Login as operator.
   - Create beneficiary.
   - Run eligibility.
   - Add note.
   - Set follow-up tomorrow.
   - Expected: beneficiary appears in follow-up list when date is adjusted to tomorrow.

2. CSV upload 500 rows
   - Upload maximum valid CSV.
   - Expected: progress reaches 100%, browser remains responsive, result downloads.

3. Scheme rule editor
   - Add contradictory age rule.
   - Expected: inline error on min/max age and publish disabled.

4. Permission checks
   - Login as operator.
   - Try `/admin/schemes`.
   - Expected: 403 page with "You do not have access to this page."

5. Rate limit
   - Lower operator limit to 3 in local env.
   - Run 4 eligibility checks.
   - Expected: fourth returns 429 with retry time.

## Known Constraints and Edge Cases

1. Bulk processing is capped at 500 rows to stay compatible with free-tier Render and Neon.
2. APScheduler inside a single Render web service is acceptable for demo but not robust for multi-instance production; future v3 should use a dedicated worker.
3. CSV uploads may contain sensitive data; files must not be publicly exposed and result URLs must expire where storage supports it.
4. Operators may share devices. Dashboard sessions must expire after inactivity; add `DASHBOARD_SESSION_IDLE_TIMEOUT_SECONDS=3600`.
5. Scheme admin mistakes can affect many users. Publish requires validation, diff preview, and audit log.
6. Rule impact preview is approximate if sample profiles are small.
7. SMS notifications depend on MSG91 credits and templates.
8. Analytics are operational, not official government reporting.
9. Multi-tenant schema exists from Phase 1, but UI whitelabelling remains out of scope.
10. Rate limiting must not block health checks or static assets.

## Dependencies on Previous Phases

1. Phase 1 scheme CRUD, rule validation, FAISS indexing, expiry checker, and scheme versions.
2. Phase 2 profiles, households, sessions, document checks, zero-match placeholders.
3. Phase 3 voice/translation/TTS telemetry for quality monitoring.
4. Phase 4 users, authentication, saved schemes, checklists, statuses, notifications, action plans.

