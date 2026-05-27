# Testing Strategy

AdhikarAI uses a layered testing approach: backend unit tests, backend integration tests, frontend static tests, and Playwright browser E2E tests.

---

## Test Summary

| Layer | Tool | Count | Directory |
|---|---|---|---|
| Backend unit | pytest | 18 files | `backend/tests/unit/` |
| Backend integration | pytest + httpx | 7 files | `backend/tests/integration/` |
| Frontend static | Node.js assert | 2 files | `frontend/tests/` |
| Frontend E2E | Playwright | 5 spec files + 1 helper | `frontend/tests/e2e/` |

Total: **55 backend tests pass** (as of last verified run). Frontend static + E2E tests pass locally.

---

## Backend Unit Tests

Pure logic tests that do not require a running database or HTTP server.

| File | Coverage |
|---|---|
| `test_config_validation.py` | Settings model_validator: rejects default secrets, insecure cookies, localhost DB in staging/production |
| `test_criteria_evaluator.py` | Eligibility criterion evaluation: age, income, caste, state, marital status, cross-scheme exclusion |
| `test_near_miss.py` | Near-miss detection: exactly one failed criterion, no unknown required criteria |
| `test_rule_validation.py` | JSONB eligibility rule schema validation |
| `test_phase2_agent_utilities.py` | Profile fact extraction, completeness scoring, question selection, sensitive field guard |
| `test_phase2_document_check.py` | Document checklist generation, synonym matching, substitute guidance |
| `test_phase2_session_store.py` | Redis session store (memory fallback) |
| `test_phase3_audio_validation.py` | Audio upload: size limit, content type validation |
| `test_phase3_language_and_cache.py` | Language code mapping, translation cache TTL |
| `test_phase3_voice_pipeline.py` | Voice pipeline: low-confidence block, localized fallback messages, mocked ASR/TTS providers |
| `test_phase4_logic.py` | Soft delete, DigiLocker stub, Aadhaar prefill stub, Aadhaar guard |
| `test_phase4_security.py` | OTP hash/verify, JWT creation/decode, cookie settings, mock OTP rejection in production |
| `test_phase5_csv.py` | Bulk CSV upload validation: size, headers, row limit |
| `test_phase5_rate_limit.py` | Daily rate limit counters: guest, user, operator, midnight reset, 429 response |
| `test_phase5_rbac.py` | Operator denial, NGO admin org scope, super admin override |
| `test_phase5_scheme_drafts.py` | Draft create, validation, preview, publish, already-published guard |
| `test_seed_data.py` | Seed data loading: JSON parse, scheme count, rule attachment |
| `test_dashboard_auth.py` | Dashboard JWT validation, `require_dashboard_actor`, dev login code check, inactive member denial |

### Running Backend Unit Tests

```bash
cd backend
uv run --extra test pytest tests/unit/ -v
```

---

## Backend Integration Tests

Tests that use the httpx async test client against the full FastAPI app. They test routes, middleware, and database interactions using a test database.

| File | Coverage |
|---|---|
| `test_admin_scheme_api.py` | Scheme create, update, publish, archive via admin token |
| `test_expiry_checker.py` | APScheduler scheme expiry transition |
| `test_faiss_search.py` | FAISS index build and semantic search query |
| `test_phase2_agent_routes.py` | Session create, message send, history retrieval |
| `test_phase3_voice_routes.py` | Voice turn, ASR upload validation, mocked provider responses |
| `test_phase4_routes.py` | OTP send/verify, `/me`, saved schemes, checklists, application status |
| `test_profile_match_api.py` | Profile match endpoint, matched/near-miss response |

### Running Backend Integration Tests

```bash
cd backend
uv run --extra test pytest tests/integration/ -v
```

Requires a running PostgreSQL database. Set `TEST_DATABASE_URL` if different from the default.

---

## Frontend Static Tests

Node.js scripts that validate file existence and structure without starting a browser:

| File | Coverage |
|---|---|
| `phase4.static.test.mjs` | PWA manifest, service worker, offline.html, install prompt component, IndexedDB schema, offlineDb.ts exports |
| `phase5.static.test.mjs` | DashboardShell component, admin route pages, dashboard route pages, beneficiary detail route |

### Running Frontend Static Tests

```bash
cd frontend
npm run test:phase4
```

---

## Playwright E2E Tests

Browser-based end-to-end tests against a fully running backend + frontend stack. See [E2E Testing](e2e-testing.md) for full setup.

| File | Coverage |
|---|---|
| `beneficiary-pwa.spec.ts` | Guest typed flow, scheme display, checklist/status UI, mobile width, no JWT in localStorage |
| `operator-dashboard.spec.ts` | Operator list/create, search, beneficiary detail, notes, follow-ups, eligibility trigger, status update, unassigned denial |
| `ngo-admin.spec.ts` | Org-scoped listing, org-scoped detail, cross-org denial |
| `super-admin.spec.ts` | Quality flags, unmatched queries, analytics, scheme draft preview |
| `accessibility-smoke.spec.ts` | Keyboard focus, accessible names, touch targets at mobile/tablet/desktop |

### Running Playwright E2E Tests

```bash
cd frontend
npm run test:e2e
```

For headed debugging:

```bash
npm run test:e2e:headed
```

---

## Test Philosophy

Per AGENTS.md:

- **Prefer tests that prove behavior** over snapshot churn.
- Backend logic: unit tests for evaluators, validators, services.
- API changes: integration tests for request/response and error codes.
- DB changes: migration test or explicit migration verification.
- Frontend behavior: component or E2E tests for critical user flows.
- Voice/language behavior: provider mocks and fallback tests.
- Permissions: cross-tenant and role-denial tests.

---

## What Is Not Tested

| Area | Reason |
|---|---|
| Real LLM inference | Requires Ollama/Groq running; integration tests mock the LLM |
| Real ASR providers | Whisper.cpp/Groq Whisper are mocked in tests |
| Real translation/TTS | Mocked; real providers require running services or API keys |
| Real MSG91 SMS | Mock OTP provider used in tests |
| Cloud PostgreSQL migration | Verified locally only, not against Neon |
| Real Redis | Tests use `memory://` fallback; real Redis not smoke-tested in CI |
| PWA offline sync loop | IndexedDB sync queue exists but automated retry not implemented |
| Browser voice recording | Requires real microphone; not tested in CI |
