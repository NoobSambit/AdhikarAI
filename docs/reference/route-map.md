# Route Map

All frontend and backend routes in AdhikarAI.

---

## Frontend Routes

| Route | Page File | Auth | Purpose |
|---|---|---|---|
| `/` | `app/page.tsx` | Optional (guest or user JWT) | Main beneficiary PWA — voice/text chat, scheme results |
| `/dev-chat` | `app/dev-chat/page.tsx` | None (local-only) | Developer text chat test |
| `/dev-voice` | `app/dev-voice/page.tsx` | None (local-only) | Developer voice test |
| `/dashboard` | `app/dashboard/page.tsx` | Dashboard JWT | Operator home |
| `/dashboard/login` | `app/dashboard/login/page.tsx` | None | Dashboard login form |
| `/dashboard/beneficiaries` | `app/dashboard/beneficiaries/page.tsx` | Dashboard JWT | Beneficiary list |
| `/dashboard/beneficiaries/[id]` | `app/dashboard/beneficiaries/[id]/` | Dashboard JWT | Beneficiary detail |
| `/dashboard/bulk-eligibility` | `app/dashboard/bulk-eligibility/page.tsx` | Dashboard JWT | CSV bulk upload |
| `/dashboard/status-board` | `app/dashboard/status-board/page.tsx` | Dashboard JWT | Status summary |
| `/dashboard/scheme-guide` | `app/dashboard/scheme-guide/page.tsx` | Dashboard JWT | Scheme reference |
| `/dashboard/exports` | `app/dashboard/exports/page.tsx` | Dashboard JWT | CSV export |
| `/dashboard/help` | `app/dashboard/help/page.tsx` | Dashboard JWT | Help page |
| `/admin/schemes` | `app/admin/schemes/page.tsx` | Dashboard JWT (super_admin) | Scheme management |
| `/admin/quality` | `app/admin/quality/page.tsx` | Dashboard JWT (super_admin) | Quality flags |
| `/admin/unmatched-queries` | `app/admin/unmatched-queries/page.tsx` | Dashboard JWT (super_admin) | Unmatched queries |
| `/admin/analytics` | `app/admin/analytics/page.tsx` | Dashboard JWT (super_admin) | Analytics |

---

## Backend Routes — Public

| Method | Path | Auth | Router File |
|---|---|---|---|
| `GET` | `/health` | 🔓 | `health.py` |
| `GET` | `/readiness` | 🔓 | `health.py` |
| `POST` | `/auth/send-otp` | 🔓 | `phase4.py` |
| `POST` | `/auth/verify-otp` | 🔓 | `phase4.py` |
| `POST` | `/agent/sessions` | 🔓 | `agent_sessions.py` |
| `POST` | `/agent/message` | 🔓 | `agent_sessions.py` |
| `GET` | `/agent/sessions/{id}` | 🔓 | `agent_sessions.py` |
| `GET` | `/agent/sessions/{id}/messages` | 🔓 | `agent_sessions.py` |
| `WS` | `/ws/chat` | 🔓 | `ws_chat.py` |
| `POST` | `/voice/turn` | 🔓 | `voice.py` |
| `POST` | `/voice/asr` | 🔓 | `voice.py` |
| `GET` | `/voice/audio/{filename}` | 🔓 | `voice.py` |
| `WS` | `/ws/voice` | 🔓 | `voice.py` |
| `POST` | `/profiles` | 🔓 | `profiles.py` |
| `GET` | `/profiles/{id}` | 🔓 | `profiles.py` |
| `PATCH` | `/profiles/{id}` | 🔓 | `profiles.py` |
| `POST` | `/households` | 🔓 | `households.py` |
| `GET` | `/households/{id}` | 🔓 | `households.py` |
| `PATCH` | `/households/{id}` | 🔓 | `households.py` |
| `POST` | `/profile/match` | 🔓 | `profile_match.py` |
| `GET` | `/document-check` | 🔓 | `document_check.py` |
| `GET` | `/schemes` | 🔓 | `schemes.py` |
| `GET` | `/schemes/{id}` | 🔓 | `schemes.py` |
| `GET` | `/schemes/search` | 🔓 | `schemes.py` |
| `POST` | `/digilocker/start` | 🔐 | `phase4.py` |
| `POST` | `/digilocker/callback` | 🔓 | `phase4.py` |

---

## Backend Routes — Beneficiary Auth

| Method | Path | Auth | Router File |
|---|---|---|---|
| `POST` | `/auth/logout` | 🔐 User JWT | `phase4.py` |
| `GET` | `/me` | 🔐 User JWT | `phase4.py` |
| `PATCH` | `/me` | 🔐 User JWT | `phase4.py` |
| `DELETE` | `/me` | 🔐 User JWT | `phase4.py` |
| `GET` | `/saved-schemes` | 🔐 User JWT | `phase4.py` |
| `POST` | `/saved-schemes` | 🔐 User JWT | `phase4.py` |
| `DELETE` | `/saved-schemes/{id}` | 🔐 User JWT | `phase4.py` |
| `GET` | `/checklists` | 🔐 User JWT | `phase4.py` |
| `PATCH` | `/checklists` | 🔐 User JWT | `phase4.py` |
| `GET` | `/application-status` | 🔐 User JWT | `phase4.py` |
| `PATCH` | `/application-status` | 🔐 User JWT | `phase4.py` |
| `POST` | `/action-plans` | 🔐 User JWT | `phase4.py` |
| `GET` | `/action-plans` | 🔐 User JWT | `phase4.py` |
| `POST` | `/offline-sync` | 🔐 User JWT | `phase4.py` |
| `POST` | `/notifications/subscribe` | 🔐 User JWT | `phase4.py` |
| `POST` | `/aadhaar/prefill/start` | 🔐 User JWT | `phase4.py` |

---

## Backend Routes — Admin Token

| Method | Path | Auth | Router File |
|---|---|---|---|
| `GET` | `/admin/schemes` | 🏛 Admin Token | `admin_schemes.py` |
| `POST` | `/admin/schemes` | 🏛 Admin Token | `admin_schemes.py` |
| `PATCH` | `/admin/schemes/{id}` | 🏛 Admin Token | `admin_schemes.py` |
| `POST` | `/admin/schemes/{id}/publish` | 🏛 Admin Token | `admin_schemes.py` |
| `POST` | `/admin/schemes/{id}/archive` | 🏛 Admin Token | `admin_schemes.py` |
| `GET` | `/admin/schemes/{id}/history` | 🏛 Admin Token | `admin_schemes.py` |
| `POST` | `/admin/ingestion/run` | 🏛 Admin Token | `admin_ingestion.py` |
| `GET` | `/admin/ingestion/runs` | 🏛 Admin Token | `admin_ingestion.py` |
| `GET` | `/admin/ingestion/runs/{id}` | 🏛 Admin Token | `admin_ingestion.py` |

---

## Backend Routes — Dashboard JWT

| Method | Path | Auth | Router File |
|---|---|---|---|
| `POST` | `/dashboard/auth/login` | 🔓 | `dashboard.py` |
| `POST` | `/dashboard/auth/logout` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/me` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/beneficiaries` | 📊 | `dashboard.py` |
| `POST` | `/dashboard/beneficiaries` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/beneficiaries/{id}` | 📊 | `dashboard.py` |
| `PATCH` | `/dashboard/beneficiaries/{id}` | 📊 | `dashboard.py` |
| `POST` | `/dashboard/beneficiaries/{id}/notes` | 📊 | `dashboard.py` |
| `POST` | `/dashboard/beneficiaries/{id}/followups` | 📊 | `dashboard.py` |
| `POST` | `/dashboard/beneficiaries/{id}/eligibility` | 📊 | `dashboard.py` |
| `PATCH` | `/dashboard/followups/{id}` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/operator-notifications` | 📊 | `dashboard.py` |
| `POST` | `/dashboard/operator-notifications/{id}/read` | 📊 | `dashboard.py` |
| `POST` | `/dashboard/bulk-eligibility` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/bulk-eligibility/{id}` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/bulk-eligibility/{id}/download` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/status-board` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/scheme-guide` | 📊 | `dashboard.py` |
| `GET` | `/dashboard/export/beneficiaries.csv` | 📊 | `dashboard.py` |

---

## Backend Routes — Admin Panel (Dashboard JWT, super_admin)

| Method | Path | Auth | Router File |
|---|---|---|---|
| `POST` | `/admin/scheme-drafts` | 📊 super_admin | `admin_panel.py` |
| `GET` | `/admin/scheme-drafts/{id}` | 📊 super_admin | `admin_panel.py` |
| `POST` | `/admin/scheme-drafts/{id}/preview` | 📊 super_admin | `admin_panel.py` |
| `POST` | `/admin/scheme-drafts/{id}/publish` | 📊 super_admin | `admin_panel.py` |
| `GET` | `/admin/unmatched-queries` | 📊 super_admin | `admin_panel.py` |
| `GET` | `/admin/unmatched-queries.csv` | 📊 super_admin | `admin_panel.py` |
| `GET` | `/admin/quality-flags` | 📊 super_admin | `admin_panel.py` |
| `POST` | `/admin/quality-flags/{id}/review` | 📊 super_admin | `admin_panel.py` |
| `GET` | `/admin/analytics` | 📊 super_admin | `admin_panel.py` |

---

## Backend Routes — Local E2E Helpers

| Method | Path | Auth | Gate |
|---|---|---|---|
| `POST` | `/local-e2e/seed` | 🏛 Admin Token | `LOCAL_E2E_HELPERS_ENABLED=true` |
| `POST` | `/local-e2e/sessions` | 🏛 Admin Token | `LOCAL_E2E_HELPERS_ENABLED=true` |
| `DELETE` | `/local-e2e/reset` | 🏛 Admin Token | `LOCAL_E2E_HELPERS_ENABLED=true` |

---

## Auth Legend

| Symbol | Meaning |
|---|---|
| 🔓 | Public — no auth required |
| 🔐 | User JWT — beneficiary session cookie |
| 🏛 | Admin Token — `X-Admin-Token` header |
| 📊 | Dashboard JWT — dashboard session cookie |
