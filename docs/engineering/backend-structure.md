# Backend Structure

The AdhikarAI backend is a FastAPI (Python 3.11+) async application using SQLAlchemy with asyncpg for PostgreSQL, redis-py for Redis, and LangGraph for the agent conversation system.

---

## Module Layout

```
backend/
  app/
    main.py                        ← FastAPI app factory, middleware, router registration
    core/
      config.py                    ← Pydantic Settings class (all env vars)
      security.py                  ← JWT creation/decode, OTP hash, cookie helpers, auth deps
      errors.py                    ← ApiError dataclass, error response formatter
    api/routes/                    ← All FastAPI routers (18 files)
    agent/                         ← LangGraph conversation graph
    voice/                         ← Voice pipeline orchestrator, ASR providers
    translation/                   ← Translation client, providers
    tts/                           ← TTS client, cache, providers
    services/                      ← Business logic services
    dashboard/                     ← Dashboard-specific helpers, RBAC
    admin_panel/                   ← Scheme drafts, quality flags, analytics
    db/
      models/                      ← SQLAlchemy ORM models (17 files)
      migrations/                  ← Alembic migration scripts (5 phases)
      session.py                   ← Async session factory and get_db dependency
      base.py                      ← DeclarativeBase
    schemas/                       ← Pydantic request/response models (15 files)
    rate_limit/                    ← Redis-backed daily counter service
    cli/                           ← Typer CLI (admin + E2E helpers)
    seeds/                         ← JSON seed files
  tests/
    conftest.py                    ← Shared pytest fixtures
    unit/                          ← 18 unit test files
    integration/                   ← 7 integration test files
  pyproject.toml                   ← Project metadata, dependencies
  alembic.ini                      ← Alembic configuration
  .env.example                     ← All env vars with local defaults
```

---

## API Routes

18 router files registered in `app/main.py`:

| Router File | Prefix | Purpose |
|---|---|---|
| `health.py` | `/health`, `/readiness` | Health + readiness probes |
| `agent_sessions.py` | `/agent` | Session create, message send, history |
| `ws_chat.py` | `/ws/chat` | WebSocket text chat |
| `profiles.py` | `/profiles` | Profile CRUD |
| `households.py` | `/households` | Household CRUD |
| `document_check.py` | `/document-check` | Document checklist with substitutes |
| `profile_match.py` | `/profile/match` | Eligibility matching |
| `schemes.py` | `/schemes` | Public scheme list/detail/search |
| `admin_schemes.py` | `/admin/schemes` | Admin scheme CRUD + publish/archive |
| `admin_ingestion.py` | `/admin/ingestion` | Data ingestion runs |
| `admin_index.py` | `/admin/indexes` | FAISS index management |
| `dashboard.py` | `/dashboard` | Full dashboard: auth, beneficiaries, bulk, exports |
| `admin_panel.py` | `/admin` | Scheme drafts, quality flags, analytics |
| `voice.py` | `/voice`, `/ws/voice` | Voice turn, ASR upload, audio serve, WS voice |
| `translate.py` | `/translate` | Translation endpoint |
| `tts.py` | `/tts` | TTS synthesis + audio serve |
| `phase4.py` | `/auth`, `/me`, `/saved-schemes`, etc. | All Phase 4 beneficiary routes |

---

## Core Module

### `core/config.py`

`Settings(BaseSettings)` — Pydantic Settings with `.env` file support. 100+ env vars covering database, Redis, LLM, ASR, translation, TTS, auth, OTP, dashboard, rate limits, and scheduled tasks.

Key features:
- `is_deployed_env` / `is_local_like_env` properties for environment-specific logic.
- `model_validator` that enforces security constraints in staging/production:
  - Non-default secrets, secure cookies, deployed database URLs, real Redis, explicit CORS origins, disabled dev login, provider credential requirements.

### `core/security.py`

- `create_session_jwt(user)` — HMAC-SHA256 JWT for beneficiary auth
- `create_dashboard_session_jwt(member)` — JWT with `typ: "dashboard"`, member_id, org, role
- `set_auth_cookie()` / `clear_auth_cookie()` — httpOnly cookie management
- `decode_session_jwt(token)` — Validates signature and expiry
- `generate_otp()` / `hash_otp()` / `verify_otp_hash()` — PBKDF2 OTP hashing with 120k iterations
- `require_user` — FastAPI dependency: extracts and validates beneficiary JWT from cookie
- `require_admin_token` — FastAPI dependency: validates `X-Admin-Token` header
- `require_dashboard_actor` — FastAPI dependency: extracts dashboard JWT, loads `OrganisationMember`, returns `DashboardActor`

### `core/errors.py`

- `ApiError` dataclass (status_code, code, message, field, details)
- `api_error_handler` — Formats error responses with `X-Request-ID`
- Standard error JSON shape: `{ error: { code, message, field, request_id } }`

---

## Agent Module

**Directory**: `app/agent/`

LangGraph-based conversation graph for welfare scheme intake:

| File | Purpose |
|---|---|
| `graph.py` | LangGraph graph definition with 10 named nodes |
| `state.py` | Agent state dataclass (profile, questions_asked, turn_count) |
| `extraction.py` | LLM-based profile fact extraction from user messages. Sensitive field guard (rejects Aadhaar). |
| `completeness.py` | Profile completeness scoring (0–100%) |
| `question_selection.py` | Selects next most useful clarifying question. Hard stop at 8 questions. |

---

## Voice Module

**Directory**: `app/voice/`

| File | Purpose |
|---|---|
| `pipeline.py` | `VoicePipeline` orchestrator: ASR → translate → agent → translate back → TTS. Low-confidence ASR block. |
| `audio_utils.py` | Audio validation (size, content type, duration), ffmpeg resampling |
| `localized_messages.py` | Fallback messages for low-confidence ASR in 12+ Indian languages |
| `providers/whisper_cpp.py` | Local Whisper.cpp ASR provider (subprocess) |
| `providers/groq_whisper.py` | Groq Whisper hosted ASR provider (HTTP) |
| `providers/factory.py` | Provider factory based on `VOICE_PROVIDER` env var |

---

## Translation Module

**Directory**: `app/translation/`

| File | Purpose |
|---|---|
| `client.py` | `TranslationClient` — caching wrapper. Redis TTL 7 days. |
| `language.py` | Language detection, code mapping (BCP-47 to IndicTrans2 codes) |
| `providers/local_indictrans2.py` | Local IndicTrans2 HTTP service |
| `providers/ai4bharat_hosted.py` | AI4Bharat hosted API |
| `providers/google_translate.py` | Google Translate API fallback |
| `providers/factory.py` | Provider factory based on `TRANSLATION_PROVIDER` env var |

---

## TTS Module

**Directory**: `app/tts/`

| File | Purpose |
|---|---|
| `client.py` | `TtsClient` — caching wrapper. Redis TTL 24 hours. |
| `providers/local_indictts.py` | Local IndicTTS-compatible HTTP service |
| `providers/google_tts.py` | Google Cloud TTS |
| `providers/factory.py` | Provider factory based on `TTS_PROVIDER` env var |

---

## Services

| Path | Purpose |
|---|---|
| `services/eligibility/matcher.py` | Eligibility rule matching engine |
| `services/eligibility/criteria.py` | Individual criterion evaluator, cross-scheme exclusion logic |
| `services/eligibility/near_miss.py` | Near-miss detection (exactly one failed criterion) |
| `services/eligibility/validation.py` | Rule JSONB schema validation |
| `services/sessions/redis_store.py` | Redis-backed session state store (falls back to `memory://`) |
| `services/sessions/session_service.py` | Chat turn handler — orchestrates agent, stores messages, persists session |
| `services/schemes.py` | Scheme CRUD, publish/archive, status events |
| `services/profiles.py` | Profile CRUD, Aadhaar guard |
| `services/households.py` | Household CRUD |
| `services/phase4.py` | Phase 4 logic: OTP send/verify, saved schemes, checklists, application status, action plans, offline sync, DigiLocker/Aadhaar stubs |
| `services/search/faiss_index.py` | FAISS index build and query using multilingual-e5-small |
| `services/search/embeddings.py` | Embedding generation via sentence-transformers |
| `services/documents/service.py` | Document checklist matching, synonym lookup, substitute guidance |
| `services/jobs/scheduler.py` | APScheduler builder for scheme expiry and quality monitoring cron |
| `services/jobs/expiry_checker.py` | Scheme expiry status transition logic |
| `services/seeds.py` | Seed data loader (reads from `seeds/central_schemes.v1.json`) |
| `services/ingestion/` | Ingestion run manager (JSON file and MyScheme API adapters) |

---

## Dashboard Module

**Directory**: `app/dashboard/`

| File | Purpose |
|---|---|
| `rbac.py` | `DashboardActor` dataclass, role-to-permission map, `assert_beneficiary_access()`, `assert_organisation_scope()`, `require_actor_permission()` |
| `beneficiaries.py` | Beneficiary CRUD, notes, follow-ups, eligibility trigger, status updates. All queries scoped by `organisation_id` and assignment. |
| `bulk_eligibility.py` | CSV upload validation, row parsing, job creation |
| `audit.py` | Audit log writer for dashboard write operations |

---

## Admin Panel Module

**Directory**: `app/admin_panel/`

| File | Purpose |
|---|---|
| `scheme_drafts.py` | Scheme draft CRUD, validation, preview, publish |
| `queries.py` | Unmatched query listing, quality flag listing/review, analytics aggregation |

---

## Rate Limit Module

**Directory**: `app/rate_limit/`

| File | Purpose |
|---|---|
| `service.py` | Daily counter using Redis INCR with midnight TTL. Falls back to in-memory `defaultdict` when `REDIS_URL=memory://`. Limits: 50/day guest, 100/day user, 1000/day operator. |

---

## CLI Module

**Directory**: `app/cli/`

| File | Purpose |
|---|---|
| `main.py` | Typer CLI: `seed` (loads central_schemes.v1.json), `reindex` (rebuilds FAISS) |
| `local_e2e.py` | Local E2E seed script: creates test organisations, members, beneficiaries; writes cookie files for Playwright |

---

## Middleware

Registered in `app/main.py`:

| Middleware | Purpose |
|---|---|
| `CORSMiddleware` | CORS with explicit origins from `CORS_ORIGINS` env var |
| `request_id_middleware` | Injects `X-Request-ID` (from header or generated UUID) into `request.state` and response |
| `ApiError` handler | Formats all `ApiError` exceptions into standard JSON error response |
| `RequestValidationError` handler | Formats Pydantic validation errors into standard JSON error response |

---

## Startup / Shutdown Events

| Event | Behaviour |
|---|---|
| `startup` | Starts APScheduler (scheme expiry cron, quality monitor cron) if `ENABLE_SCHEDULER=true` |
| `shutdown` | Stops APScheduler |
