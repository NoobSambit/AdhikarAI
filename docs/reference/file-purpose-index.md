# File Purpose Index

Quick reference for the purpose of every important file in the AdhikarAI codebase.

---

## Backend — Core

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI app factory — middleware registration, router inclusion, scheduler startup |
| `app/core/config.py` | Pydantic `Settings` class — all 100+ env vars, startup validation for staging/production |
| `app/core/security.py` | JWT creation/decode, OTP hashing (PBKDF2), cookie helpers, `require_user`/`require_admin_token`/`require_dashboard_actor` auth dependencies |
| `app/core/errors.py` | `ApiError` dataclass, error JSON formatter, `X-Request-ID` injection |

---

## Backend — API Routes

| File | Purpose |
|---|---|
| `api/routes/health.py` | `GET /health` and `GET /readiness` endpoints |
| `api/routes/agent_sessions.py` | Agent session create, message send, history |
| `api/routes/ws_chat.py` | WebSocket text chat (`/ws/chat`) |
| `api/routes/profiles.py` | Profile CRUD |
| `api/routes/households.py` | Household CRUD |
| `api/routes/document_check.py` | Document checklist with substitute guidance |
| `api/routes/profile_match.py` | Eligibility matching endpoint |
| `api/routes/schemes.py` | Public scheme list/detail/search |
| `api/routes/admin_schemes.py` | Admin scheme CRUD, publish, archive |
| `api/routes/admin_ingestion.py` | Data ingestion run management |
| `api/routes/admin_index.py` | FAISS index management |
| `api/routes/dashboard.py` | Full dashboard: auth, beneficiaries, bulk, exports, notifications |
| `api/routes/admin_panel.py` | Scheme drafts, quality flags, analytics, unmatched queries |
| `api/routes/voice.py` | Voice turn, ASR upload, audio serve, WebSocket voice |
| `api/routes/translate.py` | Translation endpoint |
| `api/routes/tts.py` | TTS synthesis and audio serve |
| `api/routes/phase4.py` | All Phase 4 routes: auth, me, saved schemes, checklists, etc. |

---

## Backend — Agent

| File | Purpose |
|---|---|
| `agent/graph.py` | LangGraph conversation graph (10 nodes) |
| `agent/state.py` | Agent state dataclass |
| `agent/extraction.py` | LLM-based profile fact extraction with Aadhaar guard |
| `agent/completeness.py` | Profile completeness scorer (0–100%) |
| `agent/question_selection.py` | Next-question selector (max 8) |

---

## Backend — Voice / Translation / TTS

| File | Purpose |
|---|---|
| `voice/pipeline.py` | Voice pipeline orchestrator: ASR → translate → agent → translate back → TTS |
| `voice/audio_utils.py` | Audio validation and ffmpeg resampling |
| `voice/localized_messages.py` | Fallback messages for low-confidence ASR in 12+ languages |
| `voice/providers/whisper_cpp.py` | Local Whisper.cpp ASR provider |
| `voice/providers/groq_whisper.py` | Groq Whisper hosted ASR |
| `translation/client.py` | Translation caching wrapper (Redis, 7-day TTL) |
| `translation/language.py` | Language detection and code mapping |
| `translation/providers/*.py` | IndicTrans2, AI4Bharat, Google Translate providers |
| `tts/client.py` | TTS caching wrapper (Redis, 24-hour TTL) |
| `tts/providers/*.py` | IndicTTS, Google Cloud TTS providers |

---

## Backend — Services

| File | Purpose |
|---|---|
| `services/eligibility/matcher.py` | Eligibility rule matching engine |
| `services/eligibility/criteria.py` | Individual criterion evaluator, cross-scheme exclusion |
| `services/eligibility/near_miss.py` | Near-miss detection |
| `services/eligibility/validation.py` | JSONB rule schema validation |
| `services/sessions/redis_store.py` | Redis session state store (`memory://` fallback) |
| `services/sessions/session_service.py` | Chat turn handler — orchestrates agent graph |
| `services/schemes.py` | Scheme CRUD, publish/archive, status events |
| `services/profiles.py` | Profile CRUD with Aadhaar guard |
| `services/households.py` | Household CRUD |
| `services/phase4.py` | Phase 4 logic: OTP, saved schemes, checklists, action plans, DigiLocker/Aadhaar stubs |
| `services/search/faiss_index.py` | FAISS index build and query |
| `services/search/embeddings.py` | Embedding generation (multilingual-e5-small) |
| `services/documents/service.py` | Document matcher, synonym lookup, substitute guidance |
| `services/jobs/scheduler.py` | APScheduler builder |
| `services/jobs/expiry_checker.py` | Scheme expiry status transitions |
| `services/seeds.py` | Seed data loader |

---

## Backend — Dashboard / Admin

| File | Purpose |
|---|---|
| `dashboard/rbac.py` | `DashboardActor`, role-permission map, access assertions |
| `dashboard/beneficiaries.py` | Beneficiary CRUD, notes, follow-ups, org-scoped queries |
| `dashboard/bulk_eligibility.py` | CSV validation, row parsing, job creation |
| `dashboard/audit.py` | Audit log writer |
| `admin_panel/scheme_drafts.py` | Scheme draft CRUD, validation, publish |
| `admin_panel/queries.py` | Unmatched queries, quality flags, analytics |

---

## Backend — Database

| File | Purpose |
|---|---|
| `db/base.py` | SQLAlchemy `DeclarativeBase` |
| `db/session.py` | Async session factory and `get_db` dependency |
| `db/models/__init__.py` | Re-exports all 45 model classes |
| `db/models/scheme.py` | `Scheme`, `SchemeCategory`, `SchemeStatusEvent`, `FaissIndex`, `SchemeEmbedding` |
| `db/models/eligibility_rule.py` | `EligibilityRule`, `SchemeVersion` |
| `db/models/profile.py` | `Profile` with CHECK constraints |
| `db/models/household.py` | `Household` |
| `db/models/conversation.py` | `ConversationSession`, `ConversationMessage` |
| `db/models/voice_turn.py` | `VoiceTurn` |
| `db/models/phase4.py` | `User`, `OtpChallenge`, `SavedScheme`, `DocumentChecklistItem`, etc. |
| `db/models/phase5.py` | `OrganisationMember`, `Beneficiary`, `BeneficiaryNote`, `SchemeDraft`, etc. |
| `db/migrations/versions/` | 5 Alembic migration files (one per phase) |

---

## Frontend — App

| File | Purpose |
|---|---|
| `app/layout.tsx` | Root layout — meta, fonts, global CSS |
| `app/page.tsx` | Main beneficiary PWA (19 KB — full conversation + scheme UI) |
| `app/styles.css` | Global design system (15 KB) |
| `app/dashboard/page.tsx` | Operator dashboard home |
| `app/dashboard/beneficiaries/page.tsx` | Beneficiary list |
| `app/dashboard/beneficiaries/[id]/BeneficiaryDetailClient.tsx` | Beneficiary detail view |

---

## Frontend — Lib

| File | Purpose |
|---|---|
| `lib/api.ts` | Typed API client (30+ functions, `credentials: "include"`) |
| `lib/offlineDb.ts` | IndexedDB schema (idb library) |
| `lib/websocket.ts` | WebSocket URL helper |

---

## Frontend — Components

| File | Purpose |
|---|---|
| `components/dashboard/DashboardShell.tsx` | Dashboard sidebar/header shell |
| `components/voice/AudioRecorder.tsx` | Browser audio recording |
| `components/voice/WaveformVisualizer.tsx` | Audio waveform canvas |
| `components/voice/LanguageSelector.tsx` | Language picker |
| `components/pwa/InstallPrompt.tsx` | PWA install banner |

---

## Documentation & Config

| File | Purpose |
|---|---|
| `AGENTS.md` | AI agent rules, cross-layer checklist, coding guidelines |
| `README.md` | Project overview, quick start links |
| `docs/README.md` | Documentation index |
| `docs/prd/*.md` | Product requirement documents (5 phases) |
| `docs/agent-change-log.md` | Append-only implementation log |
| `backend/.env.example` | All backend env vars with defaults |
| `backend/pyproject.toml` | Python project metadata and dependencies |
| `frontend/playwright.config.ts` | Playwright E2E test configuration |
