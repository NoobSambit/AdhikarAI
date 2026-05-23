# AdhikarAI PRD Compliance Audit

Date: 2026-05-22 16:52 IST

Scope: post-PRD stabilization audit for Phases 1-5. Evidence is from code, tests, migrations, generated OpenAPI, and local verification commands. Status values: `implemented`, `partially implemented`, `missing`, `unverified`.

## Executive Summary

The repository builds and the automated backend/frontend checks pass after one stabilization fix. The implementation has a broad Phase 1-5 surface: FastAPI routes are registered, migrations exist for each phase, the Next.js PWA/dashboard routes build, and tests cover core eligibility, agent utilities, voice pipeline, PWA auth/security logic, dashboard RBAC, CSV validation, and rate limiting.

The product is not production-ready end to end. Local PostgreSQL migration execution is unverified because no PostgreSQL server is reachable. Several PRD areas are demo-only or skeletal: real MSG91 login, real dashboard login UX, real DigiLocker/UIDAI flows, live PWA scheme loading instead of sample cards, full async bulk eligibility processing, complete dashboard/admin integration tests, Playwright E2E, real voice provider smoke tests, and deployment env validation.

## Verification Results

| Check | Result | Evidence |
|---|---:|---|
| Backend test suite | passed, 53 tests | `uv run --extra test pytest` |
| Backend compile/import | passed | `uv run --extra test python -m compileall app`; `from app.main import create_app` reported 71 routes |
| FastAPI startup smoke | passed | `uvicorn app.main:app --host 127.0.0.1 --port 8009` started with `ENABLE_SCHEDULER=false` |
| Backend route smoke | passed with expected auth/database limits | `/health` returned `200` with `database:error`; `/dashboard/me` and `/me` returned expected `401`; OpenAPI contained key Phase 1-5 paths |
| Alembic SQL generation | passed | `uv run --extra test alembic upgrade head --sql` generated 966 lines through `0005_phase_5` |
| Alembic upgrade against local PostgreSQL | failed/environment blocked | `uv run --extra test alembic upgrade head` failed: connection refused on `localhost:5432` |
| Frontend typecheck | passed | `npm run typecheck` |
| Frontend build | passed | `npm run build`; 18 App Router pages generated |
| Frontend static tests | passed | `npm run test:phase4 && node tests/phase5.static.test.mjs` |
| PWA/dashboard/admin route smoke | passed | Next dev server returned `200` for `/`, `/dashboard/*`, `/admin/*`, `/dev-chat`, `/dev-voice`, `/manifest.json`, `/sw.js`, `/offline.html` |

## PRD Compliance Matrix

### Phase 1 - Foundation and Eligibility Engine

| Requirement area | Status | Evidence | Gaps / notes |
|---|---:|---|---|
| FastAPI async backend and standard request IDs/errors | implemented | [main.py](/home/noobsambit/Documents/AdhikarAI/backend/app/main.py:36), [errors.py](/home/noobsambit/Documents/AdhikarAI/backend/app/core/errors.py:18) | Validation errors map to standard shape, but not every PRD-specific code path has an integration test. |
| PostgreSQL source of truth, tenant-scoped models, Phase 1 schema | implemented | [scheme.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/scheme.py:26), [eligibility_rule.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/eligibility_rule.py:12), [0001 migration](/home/noobsambit/Documents/AdhikarAI/backend/app/db/migrations/versions/0001_phase_1_foundation.py:1) | Live PostgreSQL upgrade not verified. |
| Eligibility rule JSON, validation, custom criteria, document substitutes | implemented | [scheme.py](/home/noobsambit/Documents/AdhikarAI/backend/app/schemas/scheme.py:1), [validation.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/eligibility/validation.py:1), [test_rule_validation.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_rule_validation.py:1) | Verified by unit tests, not exhaustive against every PRD field in API tests. |
| Eligibility engine matching, exclusions, near-miss, incomplete schemes | implemented | [criteria.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/eligibility/criteria.py:1), [matcher.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/eligibility/matcher.py:1), [test_near_miss.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_near_miss.py:1) | Core behavior tested. |
| `/profile/match`, `/schemes`, `/schemes/{id}`, `/schemes/search` | implemented | [profile_match.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/profile_match.py:13), [schemes.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/schemes.py:12) | Route smoke verified through OpenAPI, not live DB-backed data. |
| Admin scheme CRUD, publish/archive, ingestion, index rebuild | partially implemented | [admin_schemes.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/admin_schemes.py:9), [admin_ingestion.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/admin_ingestion.py:12), [admin_index.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/admin_index.py:12) | Phase 1 token auth exists. MyScheme public API remains adapter/demo dependent. |
| FAISS indexing and switchable embedding provider | partially implemented | [faiss_index.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/search/faiss_index.py:1), [embeddings.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/search/embeddings.py:1), [test_faiss_search.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/integration/test_faiss_search.py:1) | Local model/provider operational smoke not run. |
| Typer admin CLI and APScheduler expiry job | implemented | [cli/main.py](/home/noobsambit/Documents/AdhikarAI/backend/app/cli/main.py:1), [scheduler.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/jobs/scheduler.py:1), [test_expiry_checker.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/integration/test_expiry_checker.py:1) | Scheduler disabled during startup smoke to avoid background dependencies. |
| Seed data for default public organisation | implemented | [central_schemes.v1.json](/home/noobsambit/Documents/AdhikarAI/backend/app/seeds/central_schemes.v1.json:1), [test_seed_data.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_seed_data.py:1) | Seed loading against real PostgreSQL not verified. |

### Phase 2 - Agentic Conversation Layer

| Requirement area | Status | Evidence | Gaps / notes |
|---|---:|---|---|
| LangGraph conversation graph and required state fields | implemented | [graph.py](/home/noobsambit/Documents/AdhikarAI/backend/app/agent/graph.py:2), [state.py](/home/noobsambit/Documents/AdhikarAI/backend/app/agent/state.py:1) | Graph exists; tests mostly exercise utilities/service flow, not real LLM behavior. |
| One-question-at-a-time selection, asked fields, completeness, hard stop | implemented | [question_selection.py](/home/noobsambit/Documents/AdhikarAI/backend/app/agent/question_selection.py:53), [session_service.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/sessions/session_service.py:364), [test_phase2_agent_utilities.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase2_agent_utilities.py:1) | Real conversation manual flow not run. |
| Sensitive prompt guard: no Aadhaar/OTP/bank account collection | partially implemented | [extraction.py](/home/noobsambit/Documents/AdhikarAI/backend/app/agent/extraction.py:21) | Pattern guard exists; needs adversarial conversation tests. |
| Redis session shape and PostgreSQL conversation metadata | implemented | [redis_store.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/sessions/redis_store.py:27), [conversation.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/conversation.py:12), [0002 migration](/home/noobsambit/Documents/AdhikarAI/backend/app/db/migrations/versions/0002_phase_2_agentic_conversation.py:1) | Redis live service not smoke-tested; tests use `memory://`. |
| `/agent/sessions`, `/agent/message`, `/ws/chat`, profile/household APIs | implemented | [agent_sessions.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/agent_sessions.py:14), [ws_chat.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/ws_chat.py:1), [profiles.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/profiles.py:13), [households.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/households.py:14) | WebSocket route was not live-tested in this pass. |
| Document-check endpoint, synonym/substitute guidance | implemented | [document_check.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/document_check.py:11), [document_matcher.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/documents/document_matcher.py:1), [test_phase2_document_check.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase2_document_check.py:1) | Good unit coverage. |
| Next.js developer chat UI with debug state | implemented | [dev-chat page](/home/noobsambit/Documents/AdhikarAI/frontend/app/dev-chat/page.tsx:1), [ChatWindow.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/components/dev-chat/ChatWindow.tsx:1) | Dev UI only, not production beneficiary UX. |

### Phase 3 - Voice and Multilingual Pipeline

| Requirement area | Status | Evidence | Gaps / notes |
|---|---:|---|---|
| Provider env/config for ASR, translation, TTS | implemented | [.env.example](/home/noobsambit/Documents/AdhikarAI/backend/.env.example:37), [config.py](/home/noobsambit/Documents/AdhikarAI/backend/app/core/config.py:37) | Deployment validation for missing provider credentials is not comprehensive. |
| Browser mic UI, push-to-talk/continuous recording, waveform, language selector | implemented | [AudioRecorder.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/components/voice/AudioRecorder.tsx:19), [WaveformVisualizer.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/components/voice/WaveformVisualizer.tsx:3), [LanguageSelector.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/components/voice/LanguageSelector.tsx:6) | Browser/device manual test not run. |
| ASR upload validation and normalized response shape | implemented | [voice.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/voice.py:26), [schemas/voice.py](/home/noobsambit/Documents/AdhikarAI/backend/app/schemas/voice.py:1), [test_phase3_audio_validation.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase3_audio_validation.py:1) | Actual Whisper.cpp/Groq provider smoke not run. |
| Low-confidence ASR blocks agent with localized fallback | implemented | [pipeline.py](/home/noobsambit/Documents/AdhikarAI/backend/app/voice/pipeline.py:43), [localized_messages.py](/home/noobsambit/Documents/AdhikarAI/backend/app/voice/localized_messages.py:17), [test_phase3_voice_pipeline.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase3_voice_pipeline.py:1) | Good mocked coverage. |
| Translation and TTS APIs/caching | implemented | [translate.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/translate.py:11), [tts.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/tts.py:13), [translation/client.py](/home/noobsambit/Documents/AdhikarAI/backend/app/translation/client.py:31), [tts/client.py](/home/noobsambit/Documents/AdhikarAI/backend/app/tts/client.py:33) | Redis live cache not smoke-tested; provider credentials not configured. |
| Voice turn metrics persisted without raw audio by default | implemented | [voice_turn.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/voice_turn.py:12), [pipeline.py](/home/noobsambit/Documents/AdhikarAI/backend/app/voice/pipeline.py:136), [.env.example](/home/noobsambit/Documents/AdhikarAI/backend/.env.example:64) | No raw audio storage path observed. |
| `/voice/turn`, `/voice/asr`, `/ws/voice` REST/WebSocket surfaces | implemented | [voice.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/voice.py:26), [voice.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/voice.py:40) | `/ws/voice` not browser-tested. |

### Phase 4 - User-Facing PWA

| Requirement area | Status | Evidence | Gaps / notes |
|---|---:|---|---|
| Next.js 15 App Router PWA, manifest, SW, offline page, install prompt | implemented | [package.json](/home/noobsambit/Documents/AdhikarAI/frontend/package.json:1), [layout.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/app/layout.tsx:1), [manifest.json](/home/noobsambit/Documents/AdhikarAI/frontend/public/manifest.json:1), [sw.js](/home/noobsambit/Documents/AdhikarAI/frontend/public/sw.js:1), [InstallPrompt.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/components/pwa/InstallPrompt.tsx:1) | Lighthouse/Playwright offline verification not run. |
| Voice-first `/` product UI with language selector, mic, bottom icon nav | implemented | [page.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/app/page.tsx:1), [styles.css](/home/noobsambit/Documents/AdhikarAI/frontend/app/styles.css:1), [phase4.static.test.mjs](/home/noobsambit/Documents/AdhikarAI/frontend/tests/phase4.static.test.mjs:1) | Uses sample cards until agent returns result payload. |
| IndexedDB stores guest profile, cached schemes, history, checklist, sync queue | implemented | [offlineDb.ts](/home/noobsambit/Documents/AdhikarAI/frontend/lib/offlineDb.ts:1) | Sync retry worker is not fully automated; queue helpers exist. |
| Phone OTP auth, httpOnly cookie, no JWT in localStorage | partially implemented | [phase4.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/phase4.py:53), [security.py](/home/noobsambit/Documents/AdhikarAI/backend/app/core/security.py:26), [api.ts](/home/noobsambit/Documents/AdhikarAI/frontend/lib/api.ts:102), [test_phase4_security.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase4_security.py:1) | OTP provider defaults to `mock`; real MSG91 integration not verified. Static scan found no JWT localStorage writes. |
| Saved schemes, checklist, status, notifications, action plans, offline sync APIs | partially implemented | [phase4.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/phase4.py:101), [services/phase4.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/phase4.py:1), [schemas/phase4.py](/home/noobsambit/Documents/AdhikarAI/backend/app/schemas/phase4.py:1), [test_phase4_routes.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/integration/test_phase4_routes.py:1) | Action plans and notifications are local/demo implementations, not real PDF/WhatsApp or push delivery. |
| DigiLocker and Aadhaar optional sandbox flows; no Aadhaar storage | partially implemented | [phase4.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/phase4.py:51), [phase4.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/phase4.py:102), [test_phase4_logic.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase4_logic.py:34) | DigiLocker/UIDAI are sandbox/demo; `verified_documents.document_uri` exists for metadata/reference, no raw document file storage observed. |
| Accessibility/mobile/low-bandwidth UI expectations | partially implemented | [styles.css](/home/noobsambit/Documents/AdhikarAI/frontend/app/styles.css:1), [page.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/app/page.tsx:252) | No browser viewport, screen reader, or contrast automation run. |

### Phase 5 - NGO/CSC Dashboard and Admin Panel

| Requirement area | Status | Evidence | Gaps / notes |
|---|---:|---|---|
| Dashboard route group and dense dashboard pages | implemented | [dashboard layout](/home/noobsambit/Documents/AdhikarAI/frontend/app/dashboard/layout.tsx:1), [dashboard page](/home/noobsambit/Documents/AdhikarAI/frontend/app/dashboard/page.tsx:1), [DashboardShell.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/components/dashboard/DashboardShell.tsx:1) | Route smoke returns `200`; no authenticated UI workflow tested. |
| Dashboard role model, JWT-derived org scope, operator assignment checks | implemented | [rbac.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/rbac.py:1), [security.py](/home/noobsambit/Documents/AdhikarAI/backend/app/core/security.py:83), [beneficiaries.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/beneficiaries.py:43), [test_phase5_rbac.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase5_rbac.py:1) | No full DB integration test for cross-tenant endpoint denial yet. |
| Beneficiary CRUD, notes, follow-ups, status board, exports, scheme guide | partially implemented | [dashboard.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/dashboard.py:45), [beneficiaries.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/beneficiaries.py:93), [phase5.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/phase5.py:33) | Delete endpoint missing; filters are partial; exports are basic CSV. |
| Bulk CSV upload and result polling/download | partially implemented | [bulk_eligibility.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/bulk_eligibility.py:1), [dashboard.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/dashboard.py:130), [test_phase5_csv.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase5_csv.py:1) | Processing is synchronous/basic and does not run eligibility or produce complete result CSV fields. |
| Scheme admin drafts, preview, publish, history | partially implemented | [admin_panel.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/admin_panel.py:31), [scheme_drafts.py](/home/noobsambit/Documents/AdhikarAI/backend/app/admin_panel/scheme_drafts.py:1) | History route returns empty items; editor UI appears route-level/static, not full field-by-field workflow verified. |
| Unmatched queries, analytics, quality flags | partially implemented | [admin_panel.py](/home/noobsambit/Documents/AdhikarAI/backend/app/api/routes/admin_panel.py:16), [queries.py](/home/noobsambit/Documents/AdhikarAI/backend/app/admin_panel/queries.py:1), [phase5.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/phase5.py:160) | Quality flag generation jobs and analytics fixtures are not integration-tested. |
| Redis rate limiting with org and actor keys | implemented | [service.py](/home/noobsambit/Documents/AdhikarAI/backend/app/rate_limit/service.py:17), [test_phase5_rate_limit.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase5_rate_limit.py:1) | Fixed during stabilization: real Redis is used unless `REDIS_URL=memory://`; Redis service itself not smoke-tested. |
| Audit logs for admin/operator writes | implemented | [audit.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/audit.py:1), [beneficiaries.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/beneficiaries.py:161), [phase5.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/phase5.py:238) | Coverage is partial across all write endpoints. |

## Cross-Layer Consistency Findings

| Area | Status | Evidence / finding |
|---|---:|---|
| Backend schemas vs frontend API client | partially implemented | Frontend client has typed functions for Phase 2-5 core routes in [api.ts](/home/noobsambit/Documents/AdhikarAI/frontend/lib/api.ts:1), but several backend endpoints have no frontend client or complete UI workflow, including DigiLocker, Aadhaar prefill, notifications, action plans, bulk job polling/download, scheme draft publish, and dashboard notifications. |
| Database models vs migrations | implemented, SQL-only verified | Models exist for Phase 1-5 and Alembic SQL generation passed through `0005_phase_5`. Live PostgreSQL upgrade remains blocked by missing local DB. |
| Auth/session behavior | partially implemented | User and dashboard sessions use signed httpOnly cookies; no JWT localStorage writes found. Real beneficiary OTP and dashboard login flows are not production-ready. |
| Organisation scoping | implemented for core dashboard services | RBAC helpers enforce org and assignment checks; beneficiary queries scope by actor. Additional endpoint-level integration tests are still needed. |
| Operator assignment checks | implemented in service helpers | [rbac.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/rbac.py:31), [beneficiaries.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/beneficiaries.py:43). |
| Phase 4 PWA compatibility | partially implemented | Manifest/SW/offline page/build/routes pass. No Playwright offline or mobile viewport verification. |
| No JWT in localStorage | implemented | Static grep found only `language_code` localStorage writes in [page.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/app/page.tsx:120) and [VoiceDevWindow.tsx](/home/noobsambit/Documents/AdhikarAI/frontend/components/voice/VoiceDevWindow.tsx:39). |
| No Aadhaar storage | implemented for submitted payload guards | Aadhaar payload guards exist in [services/phase4.py](/home/noobsambit/Documents/AdhikarAI/backend/app/services/phase4.py:51), used by dashboard beneficiary writes in [beneficiaries.py](/home/noobsambit/Documents/AdhikarAI/backend/app/dashboard/beneficiaries.py:147), and tests reject Aadhaar numbers. Seed data and document names include Aadhaar as a document type, not stored numbers. |
| Document metadata only | partially implemented | `verified_documents` stores `document_type`, masked identifier, issuer, verification status, and optional `document_uri` in [phase4.py](/home/noobsambit/Documents/AdhikarAI/backend/app/db/models/phase4.py:102). No raw document file storage path found, but `document_uri` needs provider policy before production. |

## Fixed During Stabilization

1. Replaced Phase 5 in-memory-only rate limiting with Redis-backed counters for real `REDIS_URL` deployments, retaining `memory://` for tests.
2. Added coverage that verifies Redis counter keys include organisation ID, actor type, actor ID, and that expirations are set.
3. Added `retry_at` alongside `retry_after_seconds` in rate-limit error details.

Changed files:

- [service.py](/home/noobsambit/Documents/AdhikarAI/backend/app/rate_limit/service.py:1)
- [test_phase5_rate_limit.py](/home/noobsambit/Documents/AdhikarAI/backend/tests/unit/test_phase5_rate_limit.py:1)

## Critical Remaining Gaps

1. Local PostgreSQL migration execution is unverified; this blocks production readiness claims for schema correctness.
2. Real auth is incomplete for production: beneficiary OTP defaults to mock and dashboard operator/admin login UX is not a real workflow.
3. PWA starts with sample scheme cards and needs a fully verified live beneficiary journey from conversation result to saved scheme/checklist/status.
4. Phase 5 bulk eligibility is not the PRD workflow yet: no async processing, no real eligibility run per row, no complete result CSV.
5. Dashboard/admin integration tests for cross-tenant and operator-denial paths are missing.
6. Voice providers are wired but not operationally verified against Whisper.cpp, Groq, IndicTrans2/AI4Bharat, or TTS services.
7. Deployment readiness is incomplete: no env validation gate for production secrets/provider credentials, no hosted Postgres/Redis smoke, no CORS/cookie HTTPS verification.
8. Browser E2E is missing for beneficiary PWA, dashboard operator flows, admin publish flow, offline mode, and accessibility/viewport checks.

## Production-Ready vs Demo-Only

Production-ready with current evidence:

- Core eligibility rule evaluator behavior covered by tests.
- FastAPI app import/startup and route registration.
- Next.js production build for PWA/dashboard/admin route surfaces.
- httpOnly cookie session pattern and no JWT localStorage use.
- Aadhaar number payload guards in tested service paths.
- Redis-backed rate-limit implementation, pending live Redis smoke.

Demo-only or unverified:

- Real MSG91 OTP delivery.
- Real dashboard login/user management.
- Real DigiLocker/UIDAI flows.
- Real voice/translation/TTS providers.
- Live PostgreSQL migration and seed load.
- Bulk CSV eligibility job processing/storage.
- PWA offline sync execution loop and production push notifications.
- Admin analytics/quality jobs at production fidelity.

## Recommended Next Task

Run the app locally end-to-end with real PostgreSQL and Redis services, then add Playwright E2E tests for:

1. Beneficiary PWA voice/text fallback flow.
2. Phone OTP login with mock provider and httpOnly cookie.
3. Operator creates beneficiary and runs eligibility.
4. Operator cannot access an unassigned beneficiary.
5. NGO admin cannot access another organisation.
6. Super admin creates, previews, and publishes a scheme draft.
