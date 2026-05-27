# Database Schema

AdhikarAI uses PostgreSQL with SQLAlchemy async ORM. The schema is managed through 5 Alembic migration files corresponding to the 5 product phases.

---

## Migrations

| File | Phase | Tables Created |
|---|---|---|
| `0001_phase_1_foundation.py` | Phase 1 | `organisations`, `admin_users`, `scheme_categories`, `schemes`, `eligibility_rules`, `scheme_versions`, `scheme_status_events`, `faiss_indexes`, `scheme_embeddings`, `profiles`, `households`, `profile_events`, `document_check_events`, `zero_match_events`, `admin_notifications`, `ingestion_runs`, `ingestion_payloads` |
| `0002_phase_2_agentic_conversation.py` | Phase 2 | `conversation_sessions`, `conversation_messages` |
| `0003_phase_3_voice_multilingual.py` | Phase 3 | `voice_turns`, `translation_events`, `tts_events` |
| `0004_phase_4_user_pwa.py` | Phase 4 | `users`, `otp_challenges`, `saved_schemes`, `document_checklist_items`, `application_statuses`, `application_status_events`, `action_plans`, `notification_subscriptions`, `notification_jobs`, `offline_sync_events`, `digilocker_connections`, `verified_documents`, `user_language_preferences` |
| `0005_phase_5_dashboard_admin.py` | Phase 5 | `organisation_members`, `beneficiaries`, `beneficiary_notes`, `beneficiary_followups`, `beneficiary_scheme_assignments`, `bulk_eligibility_jobs`, `bulk_eligibility_rows`, `audit_logs`, `scheme_drafts`, `scheme_audit_logs`, `unmatched_queries`, `quality_flags`, `operator_notifications`, `rate_limit_events` |

All migration files are in `backend/app/db/migrations/versions/`.

---

## Core Tables

### `organisations`

The top-level tenant entity. Every data record is scoped to an organisation.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | Auto-generated |
| `name` | TEXT | Organisation display name |
| `slug` | TEXT UNIQUE | URL-safe identifier |
| `created_at` | TIMESTAMPTZ | Auto-set |

Public beneficiaries use the default organisation `00000000-0000-0000-0000-000000000001`.

---

### `schemes`

Government welfare schemes available for eligibility matching.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | Human-readable scheme ID (e.g., `PM-KISAN`) |
| `organisation_id` | UUID FK → organisations | Tenant scope |
| `category_id` | UUID FK → scheme_categories | Optional category |
| `name` | TEXT | Scheme name |
| `description` | TEXT | Full description |
| `plain_language_summary` | TEXT | Low-literacy description |
| `ministry` | TEXT | Responsible ministry |
| `state_code` | TEXT | ISO 3166-2 (e.g., `IN-OR`), null for central |
| `benefit_type` | TEXT | `cash`, `in-kind`, `service` |
| `benefit_amount` | TEXT | e.g., `₹6,000/year` |
| `status` | TEXT | `draft` / `active` / `expired` / `archived` / `upcoming` |
| `valid_from` / `valid_until` | DATE | Validity window |
| `verification_status` | TEXT | `needs_admin_review` / `verified` / `rejected` |
| `created_at` / `updated_at` | TIMESTAMPTZ | Timestamps |

CHECK constraints enforce `state_code` format and valid status/verification values.

---

### `eligibility_rules`

JSONB-based eligibility rules linked to schemes. Rules are data-driven, not hardcoded.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | Tenant scope |
| `scheme_id` | TEXT FK → schemes | Parent scheme |
| `rule_json` | JSONB | Rule definition (criteria, thresholds, operators) |
| `priority` | INTEGER | Evaluation order |
| `is_active` | BOOLEAN | Whether rule participates in matching |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

---

### `profiles`

Beneficiary profile with demographic, economic, and location data used for eligibility matching.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | Tenant scope |
| `household_id` | UUID FK → households | Optional family grouping |
| `display_name` | TEXT | |
| `age` | INTEGER | CHECK: 0–120 |
| `gender` | TEXT | CHECK: `female`, `male`, `other`, `unknown` |
| `caste_category` | TEXT | CHECK: `SC`, `ST`, `OBC`, `GENERAL`, `UNKNOWN` |
| `annual_income` | INTEGER | CHECK: ≥ 0 |
| `land_holding_acres` | NUMERIC(8,2) | |
| `occupation_type` | TEXT | |
| `marital_status` | TEXT | CHECK: `single`, `married`, `widowed`, `divorced`, `separated`, `unknown` |
| `state_code` | TEXT | ISO 3166-2 |
| `district` | TEXT | |
| `existing_scheme_ids` | JSONB | Array of scheme IDs already enrolled |
| `custom_attributes` | JSONB | Extensible key-value attributes |
| `profile_completeness` | INTEGER | 0–100 |
| `last_match_snapshot` | JSONB | Cached last eligibility result |

---

### `households`

Family group for linking multiple profiles.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | Tenant scope |
| `family_income` | INTEGER | Total household income |
| `member_count` | INTEGER | |
| `ration_card_type` | TEXT | `BPL`, `AAY`, `APL`, etc. |
| `has_disabled_member` | BOOLEAN | |
| `primary_profile_id` | UUID FK → profiles | Head of household |

---

### `users` (Phase 4)

Authenticated beneficiaries via phone OTP.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | |
| `phone_e164` | TEXT UNIQUE | E.164 format phone number |
| `profile_id` | UUID FK → profiles | Linked profile |
| `preferred_language` | TEXT | BCP-47 code |
| `font_size` | TEXT | `normal`, `large`, `extra-large` |
| `high_contrast` | BOOLEAN | Accessibility preference |
| `deleted_at` | TIMESTAMPTZ | Soft delete |

**No Aadhaar numbers are stored.** This is enforced by guards in service code and tested.

---

### `otp_challenges` (Phase 4)

Phone OTP challenge tracking.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `phone_e164` | TEXT | |
| `otp_hash` | TEXT | PBKDF2 hash (120k iterations) |
| `attempts` | INTEGER | Max 5 |
| `expires_at` | TIMESTAMPTZ | Default 5 minutes |
| `verified_at` | TIMESTAMPTZ | Set on successful verification |

---

### `conversation_sessions` / `conversation_messages` (Phase 2)

Agent conversation state.

| Column | Type | Notes |
|---|---|---|
| `conversation_sessions.id` | UUID PK | |
| `conversation_sessions.organisation_id` | UUID FK | |
| `conversation_sessions.profile_id` | UUID FK → profiles | |
| `conversation_sessions.language_code` | TEXT | User's language |
| `conversation_sessions.questions_asked` | INTEGER | Counter |
| `conversation_sessions.status` | TEXT | `active`, `completed`, `expired` |
| `conversation_messages.id` | UUID PK | |
| `conversation_messages.session_id` | UUID FK | |
| `conversation_messages.role` | TEXT | `user`, `agent`, `system` |
| `conversation_messages.content` | TEXT | Message text |
| `conversation_messages.metadata` | JSONB | Profile completeness, type flags |

---

### `voice_turns` (Phase 3)

Voice pipeline execution records. **No raw audio stored.**

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | |
| `session_id` | UUID FK | |
| `detected_language` | TEXT | Language from ASR |
| `asr_confidence` | FLOAT | 0.0–1.0 |
| `asr_duration_ms` | INTEGER | ASR processing time |
| `translate_duration_ms` | INTEGER | Translation time |
| `tts_duration_ms` | INTEGER | TTS processing time |
| `total_duration_ms` | INTEGER | Full pipeline time |

---

### Phase 5 — Dashboard Tables

#### `organisation_members`

Staff users for the dashboard.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | |
| `role` | TEXT | `operator`, `ngo_admin`, `super_admin` |
| `display_name` | TEXT | |
| `email` | TEXT | Login identifier |
| `is_active` | BOOLEAN | |

#### `beneficiaries`

Dashboard-managed beneficiary records.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | Tenant scope |
| `profile_id` | UUID FK → profiles | |
| `assigned_operator_id` | UUID FK → organisation_members | For operator assignment enforcement |
| `status` | TEXT | `active`, `inactive`, etc. |

#### `beneficiary_notes` / `beneficiary_followups`

Operator notes and follow-up tasks attached to beneficiaries.

#### `scheme_drafts`

Admin scheme editing workflow.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | |
| `payload` | JSONB | Draft scheme data |
| `status` | TEXT | `draft`, `published` |
| `created_by` | UUID FK | |

#### `audit_logs`

Dashboard write audit trail.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `organisation_id` | UUID FK | |
| `actor_id` | UUID FK | |
| `action` | TEXT | e.g., `beneficiary.create` |
| `resource_type` | TEXT | |
| `resource_id` | TEXT | |
| `metadata` | JSONB | |

---

## Multi-Tenancy

Every tenant-scoped table includes `organisation_id UUID NOT NULL REFERENCES organisations(id)`. All queries filter by `organisation_id`. See [RBAC and Tenancy](rbac-and-tenancy.md) for enforcement details.

---

## Running Migrations

```bash
cd backend
uv run --extra test alembic upgrade head
```

See [Database & Migrations](../setup/database-and-migrations.md) for full setup instructions.
