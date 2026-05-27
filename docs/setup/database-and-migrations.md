# Database and Migrations

AdhikarAI uses PostgreSQL as its primary data store, managed via SQLAlchemy (async) and Alembic for schema migrations.

---

## Migration Files

| Migration | File | What It Creates |
|---|---|---|
| Phase 1 | `0001_phase_1_foundation.py` | organisations, schemes, eligibility_rules, profiles, households, faiss_index, scheme_embeddings, profile_events, zero_match_events, scheme_categories, ingestion_runs, admin_notifications, scheme_status_events, scheme_versions |
| Phase 2 | `0002_phase_2_agentic_conversation.py` | conversation_sessions, conversation_messages, document_check_events, translation_events, user_language_preferences |
| Phase 3 | `0003_phase_3_voice_multilingual.py` | voice_turns, tts_events, additional translation_events columns |
| Phase 4 | `0004_phase_4_user_pwa.py` | users, otp_challenges, saved_schemes, document_checklist_items, application_status, application_status_events, verified_documents, digilocker_connections, notification_subscriptions, notification_jobs, action_plans, offline_sync_events |
| Phase 5 | `0005_phase_5_dashboard_admin.py` | organisation_members, beneficiaries, beneficiary_notes, beneficiary_followups, beneficiary_scheme_assignments, audit_logs, rate_limit_events, scheme_drafts, scheme_audit_logs, unmatched_queries, quality_flags, operator_notifications, bulk_eligibility_jobs, bulk_eligibility_rows |

---

## Running Migrations

### Apply all migrations (local)

```sh
cd backend
uv run --extra test alembic upgrade head
```

### Check current revision

```sh
uv run --extra test alembic current
```

Expected output after full migration: `0005_phase_5 (head)`

### Generate SQL without applying

```sh
uv run --extra test alembic upgrade head --sql > schema.sql
```

This generates the full 966-line schema SQL, useful for review or staging bootstrap.

### Rollback one step

```sh
uv run --extra test alembic downgrade -1
```

### Create a new migration

```sh
uv run --extra test alembic revision --autogenerate -m "describe_change"
```

Always review auto-generated migrations before running them. Check for:
- Missing `organisation_id` columns on tenant-scoped tables
- Missing indexes on foreign keys
- Any `DROP` statements that could cause data loss

---

## Alembic Configuration

Alembic is configured in `backend/alembic.ini`. The key settings:

```ini
script_location = app/db/migrations
sqlalchemy.url = postgresql+asyncpg://...  # overridden by env
```

The migration env (`app/db/migrations/env.py`) reads `DATABASE_DIRECT_URL` (not `DATABASE_URL`) to allow Neon's direct connection for migrations that don't use connection pooling.

---

## Model Organisation

SQLAlchemy models are defined across these files:

| File | Models |
|---|---|
| `app/db/models/organisation.py` | `Organisation` |
| `app/db/models/scheme.py` | `Scheme`, `SchemeCategory`, `FaissIndex`, `SchemeEmbedding`, `SchemeStatusEvent` |
| `app/db/models/eligibility_rule.py` | `EligibilityRule`, `SchemeVersion` |
| `app/db/models/profile.py` | `Profile` |
| `app/db/models/household.py` | `Household` |
| `app/db/models/conversation.py` | `ConversationSession`, `ConversationMessage` |
| `app/db/models/voice_turn.py` | `VoiceTurn` |
| `app/db/models/translation_event.py` | `TranslationEvent` |
| `app/db/models/tts_event.py` | `TTSEvent` |
| `app/db/models/user_language_preference.py` | `UserLanguagePreference` |
| `app/db/models/ingestion.py` | `IngestionRun`, `IngestionPayload` |
| `app/db/models/admin_user.py` | `AdminUser` |
| `app/db/models/notification.py` | `AdminNotification` |
| `app/db/models/profile_event.py` | `ProfileEvent`, `DocumentCheckEvent`, `ZeroMatchEvent` |
| `app/db/models/phase4.py` | `User`, `OtpChallenge`, `SavedScheme`, `DocumentChecklistItem`, `ApplicationStatus`, `ApplicationStatusEvent`, `VerifiedDocument`, `DigiLockerConnection`, `NotificationSubscription`, `NotificationJob`, `ActionPlan`, `OfflineSyncEvent` |
| `app/db/models/phase5.py` | `OrganisationMember`, `Beneficiary`, `BeneficiaryNote`, `BeneficiaryFollowup`, `BeneficiarySchemeAssignment`, `AuditLog`, `RateLimitEvent`, `SchemeDraft`, `SchemeAuditLog`, `UnmatchedQuery`, `QualityFlag`, `OperatorNotification`, `BulkEligibilityJob`, `BulkEligibilityRow` |

All models are imported and exported from `app/db/models/__init__.py`.

---

## Multi-Tenancy

Every tenant-scoped table includes an `organisation_id UUID NOT NULL` column referencing `organisations.id`. This is enforced at both the model level and in all service queries. The `AGENTS.md` rules require that every query on tenant-scoped tables filters by `organisation_id`.

Tenant-scoped tables:
- `schemes`, `eligibility_rules`, `profiles`, `households`
- `conversation_sessions`, `conversation_messages`, `voice_turns`
- `translation_events`, `tts_events`, `user_language_preferences`
- `organisation_members`, `beneficiaries`, `audit_logs`, `rate_limit_events`
- All Phase 4 and Phase 5 tables

---

## Seed Data

The seed data loader is at `backend/app/services/seeds.py`. It reads `backend/app/seeds/central_schemes.v1.json` and creates:

1. The default public organisation (`00000000-0000-0000-0000-000000000001`)
2. Sample central government schemes with JSONB eligibility rules
3. Admin user records for testing

Run seed:

```sh
cd backend
uv run adhikarai-admin seed --file app/seeds/central_schemes.v1.json
```

The local E2E helper also creates dashboard members and beneficiary fixtures:

```sh
APP_ENV=local LOCAL_E2E_HELPERS_ENABLED=true uv run --extra test \
  python -m app.cli.local_e2e --cookie-dir /tmp/adhikarai-local-e2e
```

---

## Database Session

The async session factory is in `app/db/session.py`. It creates a `sessionmaker` bound to the `DATABASE_URL` engine. The `get_db()` FastAPI dependency yields a session per request and handles commit/rollback.

Pool settings (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`) are read from `Settings` and applied to the engine at startup.

---

## Production Notes

- Use `DATABASE_DIRECT_URL` for migrations (Alembic needs a direct non-pooled connection on Neon).
- Use `DATABASE_URL` for the application (pooled via PgBouncer or Neon pooler).
- Never run migrations with application credentials that have `DROP` or `TRUNCATE` privileges.
- In production, migrations should be run as a deployment pre-start step, not inside the application startup.
