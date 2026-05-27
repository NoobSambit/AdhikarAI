# API Reference

Every backend route exposed by the AdhikarAI FastAPI application. Routes are registered in `app/main.py`.

**Authentication key:**
- `🔓 Public` — no auth required
- `🔐 User JWT` — requires beneficiary session cookie (`require_user`)
- `🏛 Admin Token` — requires `X-Admin-Token` header (`require_admin_token`)
- `📊 Dashboard JWT` — requires dashboard session cookie (`require_dashboard_actor`)

**Base URL (local)**: `http://localhost:8000`

---

## Health

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | 🔓 Public | Returns `{status, database}` |
| `GET` | `/readiness` | 🔓 Public | Returns `{ready, checks}` for k8s readiness probes |

---

## Auth — Beneficiary

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/send-otp` | 🔓 Public | Send OTP to phone number; returns `{challenge_id, expires_in_seconds}` |
| `POST` | `/auth/verify-otp` | 🔓 Public | Verify OTP; sets `adhikarai_session` httpOnly cookie; returns `User` |
| `POST` | `/auth/logout` | 🔐 User JWT | Clears session cookie |

---

## Me (Beneficiary Account)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/me` | 🔐 User JWT | Get current user (id, phone, preferences) |
| `PATCH` | `/me` | 🔐 User JWT | Update language, font_size, high_contrast, notification preferences |
| `DELETE` | `/me` | 🔐 User JWT | Soft-delete account |

---

## Agent — Conversation

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/agent/sessions` | 🔓 Public | Create conversation session; returns `{session_id}` |
| `POST` | `/agent/message` | 🔓 Public | Send typed message; returns `ChatOutputModel` |
| `GET` | `/agent/sessions/{session_id}` | 🔓 Public | Get session metadata |
| `GET` | `/agent/sessions/{session_id}/messages` | 🔓 Public | Get conversation history |
| `WS` | `/ws/chat` | 🔓 Public | WebSocket text chat |

---

## Voice

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/voice/turn` | 🔓 Public | Full voice pipeline (ASR → translate → agent → TTS); returns `VoiceTurnResponseModel` |
| `POST` | `/voice/asr` | 🔓 Public | ASR only (no agent); returns `{transcript, confidence, detected_language_code}` |
| `GET` | `/voice/audio/{filename}` | 🔓 Public | Serve cached TTS audio file |
| `WS` | `/ws/voice` | 🔓 Public | WebSocket voice (binary chunks → `VoiceTurnResponseModel`) |

---

## Profiles

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/profiles` | 🔓 Public | Create profile |
| `GET` | `/profiles/{profile_id}` | 🔓 Public | Get profile |
| `PATCH` | `/profiles/{profile_id}` | 🔓 Public | Update profile fields |

---

## Households

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/households` | 🔓 Public | Create household |
| `GET` | `/households/{household_id}` | 🔓 Public | Get household |
| `PATCH` | `/households/{household_id}` | 🔓 Public | Update household |

---

## Profile Match

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/profile/match` | 🔓 Public | Run eligibility matching against profile; returns `{matched_schemes, near_miss_schemes, profile_completeness}` |

---

## Document Check

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/document-check` | 🔓 Public | Returns document checklist with substitutes for a scheme (`?scheme_id=...`) |

---

## Schemes

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/schemes` | 🔓 Public | List published schemes for an organisation |
| `GET` | `/schemes/{scheme_id}` | 🔓 Public | Get scheme detail |
| `GET` | `/schemes/search` | 🔓 Public | FAISS semantic search (`?q=...&organisation_id=...`) |

---

## Admin Schemes

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/admin/schemes` | 🏛 Admin Token | List all schemes (all statuses) |
| `POST` | `/admin/schemes` | 🏛 Admin Token | Create scheme |
| `PATCH` | `/admin/schemes/{scheme_id}` | 🏛 Admin Token | Update scheme |
| `POST` | `/admin/schemes/{scheme_id}/publish` | 🏛 Admin Token | Publish (set status to `published`) |
| `POST` | `/admin/schemes/{scheme_id}/archive` | 🏛 Admin Token | Archive scheme |
| `GET` | `/admin/schemes/{scheme_id}/history` | 🏛 Admin Token | Scheme audit history (returns `[]` currently) |

---

## Admin Ingestion

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/admin/ingestion/run` | 🏛 Admin Token | Trigger ingestion run (JSON file or MyScheme API) |
| `GET` | `/admin/ingestion/runs` | 🏛 Admin Token | List ingestion runs |
| `GET` | `/admin/ingestion/runs/{run_id}` | 🏛 Admin Token | Get ingestion run detail |

---

## Saved Schemes

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/saved-schemes` | 🔐 User JWT | List saved schemes for current user |
| `POST` | `/saved-schemes` | 🔐 User JWT | Save a scheme |
| `DELETE` | `/saved-schemes/{saved_scheme_id}` | 🔐 User JWT | Unsave a scheme |

---

## Checklists

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/checklists` | 🔐 User JWT | List checklist items for a profile/scheme |
| `PATCH` | `/checklists` | 🔐 User JWT | Upsert checklist item state |

---

## Application Status

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/application-status` | 🔐 User JWT | List application statuses for a profile |
| `PATCH` | `/application-status` | 🔐 User JWT | Upsert application status for a scheme |

---

## Action Plans

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/action-plans` | 🔐 User JWT | Create action plan for a scheme |
| `GET` | `/action-plans` | 🔐 User JWT | List action plans for a profile |

---

## Offline Sync

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/offline-sync` | 🔐 User JWT | Replay queued offline events |

---

## Notifications (Push)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/notifications/subscribe` | 🔐 User JWT | Subscribe to push notifications |

---

## DigiLocker / Aadhaar (Sandbox)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/digilocker/start` | 🔐 User JWT | Start DigiLocker flow (sandbox only) |
| `POST` | `/digilocker/callback` | 🔓 Public | DigiLocker OAuth callback |
| `POST` | `/aadhaar/prefill/start` | 🔐 User JWT | Start Aadhaar prefill (sandbox only) |

---

## Dashboard — Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/dashboard/auth/login` | 🔓 Public | Dashboard login (dev mode only) |
| `POST` | `/dashboard/auth/logout` | 📊 Dashboard JWT | Clear dashboard session cookie |
| `GET` | `/dashboard/me` | 📊 Dashboard JWT | Get current dashboard actor |

---

## Dashboard — Beneficiaries

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard/beneficiaries` | 📊 Dashboard JWT | List beneficiaries (scoped by role) |
| `POST` | `/dashboard/beneficiaries` | 📊 Dashboard JWT | Create beneficiary |
| `GET` | `/dashboard/beneficiaries/{id}` | 📊 Dashboard JWT | Get beneficiary detail |
| `PATCH` | `/dashboard/beneficiaries/{id}` | 📊 Dashboard JWT | Update beneficiary |
| `POST` | `/dashboard/beneficiaries/{id}/notes` | 📊 Dashboard JWT | Add note |
| `POST` | `/dashboard/beneficiaries/{id}/followups` | 📊 Dashboard JWT | Add follow-up |
| `POST` | `/dashboard/beneficiaries/{id}/eligibility` | 📊 Dashboard JWT | Run eligibility check (partial) |

---

## Dashboard — Follow-ups

| Method | Path | Auth | Description |
|---|---|---|---|
| `PATCH` | `/dashboard/followups/{id}` | 📊 Dashboard JWT | Update follow-up |

---

## Dashboard — Operator Notifications

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard/operator-notifications` | 📊 Dashboard JWT | List unread operator notifications |
| `POST` | `/dashboard/operator-notifications/{id}/read` | 📊 Dashboard JWT | Mark notification as read |

---

## Dashboard — Bulk Eligibility

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/dashboard/bulk-eligibility` | 📊 Dashboard JWT | Upload CSV for bulk eligibility (partial) |
| `GET` | `/dashboard/bulk-eligibility/{job_id}` | 📊 Dashboard JWT | Get job status |
| `GET` | `/dashboard/bulk-eligibility/{job_id}/download` | 📊 Dashboard JWT | Download result CSV |

---

## Dashboard — Status Board

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard/status-board` | 📊 Dashboard JWT | Application status summary |

---

## Dashboard — Scheme Guide

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard/scheme-guide` | 📊 Dashboard JWT | Published scheme summaries for operators |

---

## Dashboard — Export

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard/export/beneficiaries.csv` | 📊 Dashboard JWT | Download beneficiary list as CSV |

---

## Admin Panel (Dashboard JWT — super_admin role required)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/admin/scheme-drafts` | 📊 Dashboard JWT | Create scheme draft |
| `GET` | `/admin/scheme-drafts/{id}` | 📊 Dashboard JWT | Get draft |
| `POST` | `/admin/scheme-drafts/{id}/preview` | 📊 Dashboard JWT | Validate draft |
| `POST` | `/admin/scheme-drafts/{id}/publish` | 📊 Dashboard JWT | Publish draft to scheme |
| `GET` | `/admin/unmatched-queries` | 📊 Dashboard JWT | Unmatched query list |
| `GET` | `/admin/unmatched-queries.csv` | 📊 Dashboard JWT | Download as CSV |
| `GET` | `/admin/quality-flags` | 📊 Dashboard JWT | List quality flags |
| `POST` | `/admin/quality-flags/{id}/review` | 📊 Dashboard JWT | Review a quality flag |
| `GET` | `/admin/analytics` | 📊 Dashboard JWT | Analytics summary |

---

## Local E2E Helpers (Local Dev Only)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/local-e2e/seed` | 🏛 Admin Token | Seed test data (only when `LOCAL_E2E_HELPERS_ENABLED=true`) |
| `POST` | `/local-e2e/sessions` | 🏛 Admin Token | Create pre-authed test sessions |
| `DELETE` | `/local-e2e/reset` | 🏛 Admin Token | Reset test data |

---

## Standard Error Response

All errors return:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Human-readable message for display",
    "detail": "Optional extra detail",
    "request_id": "uuid-per-request"
  }
}
```

See [error-codes.md](../reference/error-codes.md) for the full list of error codes.
