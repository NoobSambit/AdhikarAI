# Beneficiary PWA

The main user-facing interface is a Progressive Web App (PWA) built with Next.js 15. It is designed for low-end Android devices on 2G/3G, with voice-first interaction, offline support, and accessibility for low-literacy users.

---

## Purpose

Allow rural beneficiaries to:
1. Describe their situation in their native language (voice or text)
2. Receive matched government welfare schemes with eligibility explanations
3. View a document checklist with substitute-document guidance
4. Save schemes, track application status, and receive step-by-step guidance

---

## Key User Stories

- "I want to find out which government schemes I am entitled to."
- "I want to speak in Hindi/Odia/Tamil instead of typing."
- "I want to know exactly which documents I need and what I can use instead."
- "I want to save this scheme and check my application progress later."

---

## Main Route: `/`

**File**: `frontend/app/page.tsx`

The root page implements the full beneficiary PWA experience:

| Section | Description |
|---|---|
| Language selector | 12+ regional language options; persisted to localStorage |
| Mic button | Push-to-talk voice input; records WebM/Opus via Web Audio API |
| Text input | Fallback typed input for non-voice interaction |
| Chat-style message list | Shows agent questions and beneficiary responses |
| Scheme result cards | Matched eligible schemes with benefit summary, amount, eligibility badge |
| Near-miss cards | Schemes the beneficiary almost qualifies for |
| Document checklist | Per-scheme required documents with substitute guidance |
| Scheme save button | Saves scheme to authenticated user's saved list |
| Application status tracker | Shows progress (not started → submitted → approved) |
| Bottom navigation | Home, Saved, Status, Help |

---

## PWA Infrastructure

| Asset | File |
|---|---|
| Web App Manifest | `frontend/public/manifest.json` |
| Service Worker | `frontend/public/sw.js` |
| Offline page | `frontend/public/offline.html` |
| Install prompt | `frontend/components/pwa/InstallPrompt.tsx` |

The manifest declares the app as a standalone PWA. The service worker pre-caches key assets and serves the offline page when the network is unavailable.

---

## Voice Components

| Component | File | Purpose |
|---|---|---|
| `AudioRecorder` | `components/voice/AudioRecorder.tsx` | Mic capture, push-to-talk, silence detection |
| `WaveformVisualizer` | `components/voice/WaveformVisualizer.tsx` | Real-time audio amplitude waveform |
| `LanguageSelector` | `components/voice/LanguageSelector.tsx` | Language picker with regional language names |
| `VoiceDevWindow` | `components/voice/VoiceDevWindow.tsx` | Dev-only overlay showing ASR/pipeline debug info |

---

## IndexedDB Offline Storage

**File**: `frontend/lib/offlineDb.ts`

The app stores data locally in IndexedDB for offline access:

| Store | Contents |
|---|---|
| `guestProfile` | Profile data before OTP login |
| `savedSchemes` | Cached scheme cards |
| `conversationHistory` | Recent agent conversation turns |
| `checklistItems` | Document checklist state |
| `syncQueue` | Pending server sync events (created offline) |

---

## API Client

**File**: `frontend/lib/api.ts`

Typed functions for all backend calls. Uses `credentials: "include"` to send httpOnly cookies automatically. Key functions:

- `sendOtp(phone)` → `POST /auth/send-otp`
- `verifyOtp(challengeId, otp)` → `POST /auth/verify-otp`
- `getMe()` → `GET /me`
- `createAgentSession(orgId)` → `POST /agent/sessions`
- `sendAgentMessage(payload)` → `POST /agent/message`
- `saveScheme(profileId, schemeId)` → `POST /saved-schemes`
- `updateChecklist(items)` → `PATCH /checklists`
- `updateApplicationStatus(request)` → `PATCH /application-status`
- `syncOfflineEvents(events)` → `POST /offline-sync`

---

## Guest Mode and Login Migration

Before OTP login, the beneficiary uses the app as a guest:
- Profile data is stored in IndexedDB `guestProfile`.
- Conversation sessions are tied to a locally generated `session_id`.
- The `organisation_id` defaults to the public organisation UUID.

After OTP login, the guest profile is migrated to the authenticated user account by calling `PATCH /me` with `guest_profile_id`. This prevents data loss during the login flow.

---

## Accessibility

Per `AGENTS.md` and Phase 4 PRD:
- Touch targets ≥ 44px
- WCAG AA contrast
- Visible focus states
- Accessible names on interactive elements
- Text + icon navigation (never text-only)
- Cards use ≤ 8px border radius
- No cards inside cards

Static accessibility checks are covered in the Playwright E2E suite (`accessibility-smoke.spec.ts`).

---

## Loading and Error States

- All API calls show a loading spinner or skeleton.
- Network errors show a retry button with a short user-facing message.
- Low-confidence ASR shows: "Couldn't hear you clearly. Please speak again or type."
- Rate limit exceeded shows: "You've reached today's limit. Please try again tomorrow."

---

## Security and Privacy

- JWT never stored in localStorage (httpOnly cookie only).
- No Aadhaar numbers collected or stored.
- Profile data is minimal: age, gender, state, caste, income, disability, BPL status.
- Voice audio is not stored server-side (only metadata).
- Guest profiles are stored only in the user's own browser (IndexedDB).

---

## Known Limitations

- The PWA starts with sample scheme cards until the agent completes its session. A fully live beneficiary journey from voice input to real scheme result requires a running LLM, translation, and TTS provider.
- Offline sync retry loop is not fully automated; the sync queue exists but retry execution is not implemented as a background job.
- Real push notification delivery is not implemented (subscribe endpoint works, no real Web Push dispatch).
- Playwright offline mode and mobile viewport tests are written but rely on live backend.
