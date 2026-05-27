# Feature Map

Comprehensive feature-by-feature status table for AdhikarAI Phases 1–5.

**Status labels:**
- **Implemented** — feature is built, tested, and locally verified
- **Partial** — built but not complete or not all edge cases handled
- **Demo** — wired but requires real credentials or services
- **Local-only** — works locally but not suitable for production
- **Planned** — in PRD but not yet built

---

## Phase 1 — Foundation & Eligibility Engine

| Feature | User | Frontend Route/Component | Backend Route/Service | DB Model | Status | Tests | Notes |
|---|---|---|---|---|---|---|---|
| Scheme CRUD (admin) | Super admin | `/admin/schemes` | `GET/POST/PATCH /admin/schemes` | `Scheme`, `EligibilityRule` | **Implemented** | `test_admin_scheme_api.py` | Token-auth gated |
| Scheme publish/archive | Super admin | `/admin/schemes` | `POST /admin/schemes/{id}/publish` | `SchemeStatusEvent` | **Implemented** | `test_admin_scheme_api.py` | |
| Eligibility rule JSONB | Super admin | Admin scheme form | Schema validation in `schemas/scheme.py` | `EligibilityRule` | **Implemented** | `test_rule_validation.py` | |
| Eligibility matching | Beneficiary | `/` (result cards) | `/profile/match` → `services/eligibility/matcher.py` | `Scheme`, `EligibilityRule` | **Implemented** | `test_near_miss.py`, `test_criteria_evaluator.py` | |
| Near-miss detection | Beneficiary | Result cards | `matcher.py` | — | **Implemented** | `test_near_miss.py` | Exactly one failed criterion |
| Cross-scheme exclusions | All | — | `criteria.py` | `EligibilityRule.rule_json` | **Implemented** | `test_criteria_evaluator.py` | |
| FAISS semantic search | Beneficiary | `/` search | `GET /schemes/search` → `faiss_index.py` | `FaissIndex`, `SchemeEmbedding` | **Partial** | `test_faiss_search.py` | Model not smoke-tested in CI |
| Scheme list/detail APIs | All | — | `GET /schemes`, `GET /schemes/{id}` | `Scheme` | **Implemented** | `test_profile_match_api.py` | |
| Scheme expiry scheduler | System | — | APScheduler cron | `Scheme`, `SchemeStatusEvent` | **Implemented** | `test_expiry_checker.py` | |
| Seed data (central schemes) | System | — | `app.cli.main seed` | `Scheme`, `EligibilityRule` | **Implemented** | `test_seed_data.py` | 5 sample central govt. schemes |
| Schema ingestion (JSON file) | Super admin | — | `POST /admin/ingestion/run` | `IngestionRun`, `IngestionPayload` | **Partial** | — | MyScheme API adapter demo |

---

## Phase 2 — Agentic Conversation Layer

| Feature | User | Frontend Route/Component | Backend Route/Service | DB Model | Status | Tests | Notes |
|---|---|---|---|---|---|---|---|
| Agent conversation session | Beneficiary | `/` | `POST /agent/sessions` | `ConversationSession` | **Implemented** | `test_phase2_agent_routes.py` | |
| Agent message (typed) | Beneficiary | `/` (text input) | `POST /agent/message` | `ConversationMessage` | **Implemented** | `test_phase2_agent_routes.py` | |
| WebSocket chat | Beneficiary | `/dev-chat` | `WS /ws/chat` | — | **Implemented** | — | Browser not tested |
| One-question selection | Beneficiary | — | `question_selection.py` | — | **Implemented** | `test_phase2_agent_utilities.py` | Max 8 questions |
| Profile fact extraction | Beneficiary | — | `extraction.py` + LLM | — | **Implemented** | `test_phase2_agent_utilities.py` | Sensitive field guard |
| Profile completeness | Beneficiary | Progress bar | `completeness.py` | — | **Implemented** | `test_phase2_agent_utilities.py` | |
| Redis session state | Beneficiary | — | `redis_store.py` | `ConversationSession` | **Implemented** | `test_phase2_session_store.py` | Falls back to `memory://` |
| Document check | Beneficiary | Checklist cards | `GET /document-check` | — | **Implemented** | `test_phase2_document_check.py` | Synonym + substitute guidance |
| Profile API | Beneficiary | — | `GET/POST/PATCH /profiles` | `Profile` | **Implemented** | — | |
| Household API | Beneficiary | — | `GET/POST/PATCH /households` | `Household` | **Implemented** | — | |
| Dev chat UI | Developer | `/dev-chat` | — | — | **Local-only** | — | Not production beneficiary UX |

---

## Phase 3 — Voice & Multilingual Pipeline

| Feature | User | Frontend Route/Component | Backend Route/Service | DB Model | Status | Tests | Notes |
|---|---|---|---|---|---|---|---|
| Browser mic / push-to-talk | Beneficiary | `AudioRecorder.tsx` | — | — | **Implemented** | Phase 4 static test | Browser device not tested |
| Waveform visualizer | Beneficiary | `WaveformVisualizer.tsx` | — | — | **Implemented** | — | |
| Language selector | Beneficiary | `LanguageSelector.tsx` | — | — | **Implemented** | — | |
| ASR upload validation | Beneficiary | — | `POST /voice/asr` | — | **Implemented** | `test_phase3_audio_validation.py` | Max 8 MB, content type check |
| ASR (Whisper.cpp local) | Beneficiary | — | `whisper_cpp.py` | `VoiceTurn` | **Demo** | `test_phase3_voice_routes.py` (mocked) | Binary path configurable |
| ASR (Groq Whisper hosted) | Beneficiary | — | `groq_whisper.py` | `VoiceTurn` | **Demo** | mocked | Requires `GROQ_API_KEY` |
| Low-confidence ASR block | Beneficiary | — | `pipeline.py` | `VoiceTurn` | **Implemented** | `test_phase3_voice_pipeline.py` | Localized fallback message |
| Translation (IndicTrans2) | Beneficiary | — | `local_indictrans2.py` | `TranslationEvent` | **Demo** | `test_phase3_language_and_cache.py` | Requires local service |
| Translation (AI4Bharat) | Beneficiary | — | `ai4bharat_hosted.py` | `TranslationEvent` | **Demo** | mocked | Requires API credentials |
| Translation (Google) | Beneficiary | — | `google_translate.py` | `TranslationEvent` | **Demo** | — | Fallback; requires API key |
| Translation cache | System | — | `translation/client.py` | `TranslationEvent` | **Implemented** | `test_phase3_language_and_cache.py` | Redis TTL 7 days |
| TTS (IndicTTS local) | Beneficiary | — | `local_indictts.py` | `TTSEvent` | **Demo** | mocked | Requires local HTTP service |
| TTS (Google Cloud) | Beneficiary | — | `google_tts.py` | `TTSEvent` | **Demo** | — | Requires credentials |
| TTS cache | System | — | `tts/client.py` | `TTSEvent` | **Implemented** | — | Redis TTL 24 hours |
| Voice turn POST endpoint | Beneficiary | — | `POST /voice/turn` | `VoiceTurn` | **Implemented** | `test_phase3_voice_routes.py` | |
| Voice WebSocket | Beneficiary | — | `WS /ws/voice` | `VoiceTurn` | **Implemented** | — | Browser not tested |
| Voice turn metrics persist | System | — | `pipeline.py` | `VoiceTurn` | **Implemented** | — | No raw audio stored |
| Dev voice UI | Developer | `/dev-voice` | — | — | **Local-only** | — | |

---

## Phase 4 — User-Facing PWA

| Feature | User | Frontend Route/Component | Backend Route/Service | DB Model | Status | Tests | Notes |
|---|---|---|---|---|---|---|---|
| PWA manifest | Beneficiary | `/manifest.json` | — | — | **Implemented** | Phase 4 static test | |
| Service worker | Beneficiary | `/sw.js` | — | — | **Implemented** | Phase 4 static test | |
| Offline page | Beneficiary | `/offline.html` | — | — | **Implemented** | Phase 4 static test | |
| Install prompt | Beneficiary | `InstallPrompt.tsx` | — | — | **Implemented** | Phase 4 static test | |
| Phone OTP send | Beneficiary | OTP modal | `POST /auth/send-otp` | `OtpChallenge` | **Implemented** | `test_phase4_security.py` | Mock provider default |
| Phone OTP verify | Beneficiary | OTP modal | `POST /auth/verify-otp` | `User`, `OtpChallenge` | **Implemented** | `test_phase4_security.py` | Sets httpOnly cookie |
| Real SMS OTP (MSG91) | Beneficiary | — | `msg91.py` | — | **Demo** | — | Requires MSG91 credentials |
| GET /me | Beneficiary | PWA auth | `GET /me` | `User` | **Implemented** | `test_phase4_routes.py` | |
| PATCH /me (settings) | Beneficiary | Settings modal | `PATCH /me` | `User` | **Implemented** | `test_phase4_routes.py` | Language, font, contrast, notifications |
| DELETE /me | Beneficiary | — | `DELETE /me` | `User` | **Implemented** | `test_phase4_logic.py` | Soft delete |
| Saved schemes | Beneficiary | Saved tab | `POST/DELETE /saved-schemes` | `SavedScheme` | **Implemented** | `test_phase4_routes.py` | |
| Document checklist | Beneficiary | Checklist tab | `PATCH /checklists` | `DocumentChecklistItem` | **Implemented** | `test_phase4_routes.py` | |
| Application status | Beneficiary | Status tab | `PATCH /application-status` | `ApplicationStatus`, `ApplicationStatusEvent` | **Implemented** | `test_phase4_routes.py` | |
| Action plans | Beneficiary | — | `POST /action-plans` | `ActionPlan` | **Partial** | — | No real PDF/delivery |
| Push notification subscribe | Beneficiary | — | `POST /notifications/subscribe` | `NotificationSubscription` | **Partial** | — | Subscribe only; no real delivery |
| Offline sync | Beneficiary | — | `POST /offline-sync` | `OfflineSyncEvent` | **Partial** | — | Queue helpers exist; retry loop not automated |
| IndexedDB | Beneficiary | `offlineDb.ts` | — | — | **Implemented** | Phase 4 static test | Profile, schemes, history, sync queue |
| DigiLocker (sandbox) | Beneficiary | — | `POST /digilocker/start` | `DigiLockerConnection` | **Demo** | `test_phase4_logic.py` | Stub, no real government integration |
| Aadhaar prefill (sandbox) | Beneficiary | — | `POST /aadhaar/prefill/start` | — | **Demo** | `test_phase4_logic.py` | Stub; no Aadhaar numbers stored |
| Language preference | Beneficiary | Language selector | Stored via `UserLanguagePreference` | `UserLanguagePreference` | **Implemented** | — | |
| High contrast / font size | Beneficiary | Accessibility settings | `PATCH /me` | `User` | **Implemented** | — | |

---

## Phase 5 — NGO/CSC Dashboard & Admin Panel

| Feature | User | Frontend Route | Backend Route/Service | DB Model | Status | Tests | Notes |
|---|---|---|---|---|---|---|---|
| Dashboard login (dev) | Operator/Admin | `/dashboard/login` | `POST /dashboard/auth/login` | `OrganisationMember` | **Local-only** | `test_dashboard_auth.py` | Dev code login only |
| Dashboard logout | Operator/Admin | Dashboard | `POST /dashboard/auth/logout` | — | **Implemented** | `test_dashboard_auth.py` | Clears cookie |
| Dashboard me | Operator/Admin | Dashboard | `GET /dashboard/me` | `OrganisationMember` | **Implemented** | `test_dashboard_auth.py` | Returns role + permissions |
| List beneficiaries | Operator/Admin | `/dashboard/beneficiaries` | `GET /dashboard/beneficiaries` | `Beneficiary` | **Implemented** | Local E2E | Scoped by org + assignment |
| Create beneficiary | Operator | `/dashboard/beneficiaries` | `POST /dashboard/beneficiaries` | `Beneficiary` | **Implemented** | Local E2E | |
| Get beneficiary detail | Operator | `/dashboard/beneficiaries/{id}` | `GET /dashboard/beneficiaries/{id}` | `Beneficiary` | **Implemented** | Local E2E | Assignment check enforced |
| Update beneficiary | Operator | Beneficiary form | `PATCH /dashboard/beneficiaries/{id}` | `Beneficiary` | **Implemented** | Local E2E | |
| Add note | Operator | Beneficiary detail | `POST /dashboard/beneficiaries/{id}/notes` | `BeneficiaryNote` | **Implemented** | Local E2E | |
| Add follow-up | Operator | Beneficiary detail | `POST /dashboard/beneficiaries/{id}/followups` | `BeneficiaryFollowup` | **Implemented** | Local E2E | |
| Update follow-up | Operator | Dashboard | `PATCH /dashboard/followups/{id}` | `BeneficiaryFollowup` | **Implemented** | — | |
| Run eligibility (dashboard) | Operator | Beneficiary detail | `POST /dashboard/beneficiaries/{id}/eligibility` | `BeneficiarySchemeAssignment` | **Partial** | — | Returns empty results; no real eligibility run |
| Bulk CSV upload | Operator | `/dashboard/bulk-eligibility` | `POST /dashboard/bulk-eligibility` | `BulkEligibilityJob`, `BulkEligibilityRow` | **Partial** | `test_phase5_csv.py` | Sync; no real eligibility per row |
| Status board | Admin | `/dashboard/status-board` | `GET /dashboard/status-board` | `ApplicationStatus` | **Partial** | — | Basic aggregation |
| Export CSV | Admin | `/dashboard/exports` | `GET /dashboard/export/beneficiaries.csv` | `Beneficiary` | **Partial** | — | Basic CSV; no full field export |
| Scheme guide | Admin | `/dashboard/scheme-guide` | `GET /dashboard/scheme-guide` | `Scheme` | **Partial** | — | |
| Operator notifications | Operator | Dashboard | `GET /dashboard/operator-notifications` | `OperatorNotification` | **Implemented** | — | Read-only display |
| Operator-denied access | Operator | — | RBAC in `beneficiaries.py` | — | **Implemented** | `test_phase5_rbac.py` | 403 BENEFICIARY_NOT_ASSIGNED |
| NGO admin org scope | NGO admin | Dashboard | `beneficiaries.py:assert_organisation_scope` | — | **Implemented** | `test_phase5_rbac.py` | |
| Super admin cross-org | Super admin | Admin | All routes | — | **Implemented** | `test_phase5_rbac.py` | |
| Rate limiting (guest) | Beneficiary | — | `rate_limit/service.py` | `RateLimitEvent` | **Implemented** | `test_phase5_rate_limit.py` | 50/day per session |
| Rate limiting (operator) | Operator | — | `rate_limit/service.py` | — | **Implemented** | `test_phase5_rate_limit.py` | 1000/day per member |
| Audit logs | Admin | — | `dashboard/audit.py` | `AuditLog` | **Partial** | — | Not on all write endpoints |
| Scheme drafts (admin) | Super admin | `/admin/schemes` | `POST/GET /admin/scheme-drafts` | `SchemeDraft` | **Partial** | `test_phase5_scheme_drafts.py` | History returns empty |
| Scheme draft preview | Super admin | Admin | `POST /admin/scheme-drafts/{id}/preview` | `SchemeDraft` | **Implemented** | Local E2E | |
| Scheme draft publish | Super admin | Admin | `POST /admin/scheme-drafts/{id}/publish` | `Scheme`, `SchemeAuditLog` | **Implemented** | `test_phase5_scheme_drafts.py` | |
| Unmatched queries | Super admin | `/admin/unmatched-queries` | `GET /admin/unmatched-queries` | `UnmatchedQuery` | **Partial** | Local E2E | DB populated by fixture; no auto-generation |
| Analytics | Admin | `/admin/analytics` | `GET /admin/analytics` | `AuditLog`, `Beneficiary` | **Partial** | Local E2E | Basic counts |
| Quality flags | Super admin | `/admin/quality` | `GET /admin/quality-flags` | `QualityFlag` | **Partial** | Local E2E | Manual fixture; no auto-generation |
| Quality flag review | Super admin | Admin | `POST /admin/quality-flags/{id}/review` | `QualityFlag` | **Implemented** | Local E2E | |
