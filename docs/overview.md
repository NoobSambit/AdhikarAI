# AdhikarAI — Overview

## What is AdhikarAI?

AdhikarAI is a multilingual, voice-first agentic AI platform that helps rural Indian citizens discover and apply for government welfare schemes they are legally entitled to. The platform is designed for low-literacy, low-bandwidth users on low-end Android devices, and supports regional Indian languages.

The name *Adhikar* means "right" or "entitlement" in Hindi — the product is built on the premise that every eligible citizen should be able to claim what they are entitled to, without needing a literate intermediary.

---

## Primary User

| Attribute | Detail |
|---|---|
| Who | Rural Indian beneficiary |
| Literacy | May have low or no literacy |
| Language | May speak only a regional language (Hindi, Odia, Tamil, Telugu, Bengali, etc.) |
| Device | Low-end Android phone |
| Connectivity | 2G / 3G |
| Assistance | May be assisted by an NGO worker or CSC operator |

## Secondary Users

| User | Role |
|---|---|
| NGO worker / CSC operator | Assists beneficiaries via dashboard; runs eligibility checks; manages follow-ups |
| NGO admin | Manages operators within their organisation; views analytics |
| Super admin | Manages all organisations; drafts and publishes scheme rules; reviews quality flags |

---

## Core User Journey

```
Beneficiary speaks their situation in native language
    ↓
Agent asks one clarifying question at a time (up to 8 questions)
    ↓
Agent matches eligible government schemes
    ↓
App shows: document checklist, substitute-document guidance, application steps
    ↓
Beneficiary can save schemes, track application status, download checklist
    ↓
NGO/CSC operator can view, assist, and manage beneficiary records via dashboard
```

---

## What Is Implemented Now

The following features are **implemented** and verified (either by automated tests or local E2E workflows):

### Phase 1 — Foundation & Eligibility Engine
- FastAPI async backend with standard error codes and request IDs
- PostgreSQL schema for schemes, eligibility rules, profiles, households, organisations
- Eligibility rule engine using Experta + PostgreSQL JSONB rules
- Near-miss matching (exactly one failed criterion)
- FAISS vector index for semantic scheme search using multilingual-e5-small
- Admin token-gated scheme CRUD and ingestion APIs
- APScheduler for scheme expiry checking
- Seed data: sample central government schemes and eligibility rules

### Phase 2 — Agentic Conversation Layer
- LangGraph conversation graph with 10 named nodes
- One-question-at-a-time selection; hard stop after 8 questions
- Redis session store for conversation state
- PostgreSQL conversation metadata
- REST + WebSocket chat APIs
- Document check endpoint with synonym/substitute guidance
- Developer chat UI (`/dev-chat`) — local/development only

### Phase 3 — Voice & Multilingual Pipeline
- ASR providers: Whisper.cpp (local) and Groq Whisper (hosted) — wired, not smoke-tested against real hardware
- Browser ASR fallback option
- Translation providers: IndicTrans2 local, AI4Bharat hosted, Google fallback
- TTS providers: IndicTTS-compatible local, Google Cloud TTS hosted
- Translation and TTS caching (Redis-backed)
- Low-confidence ASR blocks the agent with localized fallback messages
- Voice turn metrics persisted (no raw audio stored)
- Voice browser UI: mic button, push-to-talk, waveform, language selector
- `/voice/turn`, `/voice/asr`, `/ws/voice` endpoints

### Phase 4 — User-Facing PWA
- Next.js 15 App Router with PWA manifest, service worker, offline page
- Voice-first `/` page with language selector, mic button, and bottom nav
- Phone OTP auth with httpOnly cookie sessions
- `GET /me`, `PATCH /me`, `DELETE /me` (account management)
- Saved schemes, checklist, application status, action plans, offline sync
- DigiLocker and Aadhaar prefill (sandbox/demo flows only)
- IndexedDB for offline profile, scheme cache, history, and sync queue
- Push notification subscription endpoint (delivery not real in demo)

### Phase 5 — NGO/CSC Dashboard & Admin Panel
- Dashboard login (dev/local only — real production auth not configured)
- Operator: list/create/update beneficiaries, add notes, add follow-ups, update application status
- Operator assignment enforcement (operators can only access assigned beneficiaries)
- NGO admin: organisation-scoped beneficiary access, analytics
- Super admin: cross-organisation access, analytics, quality flags, unmatched queries
- Bulk CSV upload for beneficiary eligibility (synchronous, basic processing)
- Scheme draft/preview/publish workflow (admin)
- Redis rate limiting (daily limits per guest/user/operator)
- Audit logs for dashboard writes

---

## What Is Demo / Local-Only

| Feature | Status | Notes |
|---|---|---|
| Real MSG91 SMS OTP | **Demo** | `OTP_PROVIDER=mock` by default; MSG91 requires credentials |
| Real dashboard login | **Local dev only** | `DASHBOARD_AUTH_PROVIDER=dev`; production must keep disabled |
| Real DigiLocker / UIDAI | **Sandbox/demo** | Stub flows; no real government integration |
| Real Whisper.cpp | **Wired** | Binary path configurable; local hardware not smoke-tested |
| Real Groq Whisper / LLM | **Wired** | Requires `GROQ_API_KEY` |
| Real IndicTrans2 / AI4Bharat | **Wired** | Requires local service or API credentials |
| Real IndicTTS / Google TTS | **Wired** | Requires credentials |
| Redis-backed caching | **Wired** | Falls back to `memory://` locally; real Redis smoke not run |
| Live PostgreSQL migration | **Verified locally** | Not verified against cloud PostgreSQL |
| Push notification delivery | **Partial** | Subscribe endpoint works; real Web Push not implemented |

---

## What Is Not Production-Ready

- Real beneficiary SMS OTP delivery
- Dashboard operator authentication (no staff identity provider)
- Full async bulk eligibility job processing
- PWA offline sync execution loop
- Admin analytics at production fidelity
- Browser E2E tests against deployed cloud environments
- CORS/cookie HTTPS validation on hosted infrastructure

See the full compliance audit at [prd-compliance-audit.md](prd-compliance-audit.md).

---

## Non-Negotiable Principles

The following constraints are enforced at the code level and must not be relaxed:

- **Never store Aadhaar numbers** — payload guards enforced in service code and tested
- **Never store raw document files** — only document metadata and masked identifiers
- **JWT never in localStorage** — only httpOnly cookies; enforced by static scan
- **Production rejects insecure defaults** — config validation at startup rejects weak secrets, localhost DB/Redis, `memory://` Redis, mock OTP, and dev dashboard login
- **Multi-tenancy enforced** — every tenant-scoped query filters by `organisation_id`; operators can only access assigned beneficiaries
