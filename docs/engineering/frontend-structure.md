# Frontend Structure

The AdhikarAI frontend is a Next.js 15 App Router application (TypeScript) that serves as both the beneficiary PWA and the operator/admin dashboard.

---

## App Routes

| Route | File | Purpose | Auth | Status |
|---|---|---|---|---|
| `/` | `app/page.tsx` | Main beneficiary PWA — voice/text conversation, scheme results, saved schemes, checklists | Optional (guest or authenticated) | **Implemented** |
| `/dev-chat` | `app/dev-chat/page.tsx` | Developer text chat test UI | None (local-only) | **Local-only** |
| `/dev-voice` | `app/dev-voice/page.tsx` | Developer voice pipeline test UI | None (local-only) | **Local-only** |
| `/dashboard` | `app/dashboard/page.tsx` | Operator home — beneficiary list, search, quick actions | Dashboard JWT | **Implemented** |
| `/dashboard/login` | `app/dashboard/login/page.tsx` | Dashboard login form (dev code auth) | None | **Local-only** |
| `/dashboard/beneficiaries` | `app/dashboard/beneficiaries/page.tsx` | Beneficiary list with search and create | Dashboard JWT | **Implemented** |
| `/dashboard/beneficiaries/[id]` | `app/dashboard/beneficiaries/[id]/` | Beneficiary detail, notes, follow-ups, eligibility | Dashboard JWT | **Implemented** |
| `/dashboard/bulk-eligibility` | `app/dashboard/bulk-eligibility/page.tsx` | CSV upload for bulk eligibility | Dashboard JWT | **Partial** |
| `/dashboard/status-board` | `app/dashboard/status-board/page.tsx` | Application status summary | Dashboard JWT | **Partial** |
| `/dashboard/scheme-guide` | `app/dashboard/scheme-guide/page.tsx` | Published scheme reference for operators | Dashboard JWT | **Partial** |
| `/dashboard/exports` | `app/dashboard/exports/page.tsx` | Beneficiary CSV export | Dashboard JWT | **Partial** |
| `/dashboard/help` | `app/dashboard/help/page.tsx` | Operator help page | Dashboard JWT | **Implemented** |
| `/admin/schemes` | `app/admin/schemes/page.tsx` | Scheme draft/publish management | Dashboard JWT (super_admin) | **Implemented** |
| `/admin/quality` | `app/admin/quality/page.tsx` | Quality flags review | Dashboard JWT (super_admin) | **Partial** |
| `/admin/unmatched-queries` | `app/admin/unmatched-queries/page.tsx` | Unmatched beneficiary queries | Dashboard JWT (super_admin) | **Partial** |
| `/admin/analytics` | `app/admin/analytics/page.tsx` | Platform analytics | Dashboard JWT (super_admin) | **Partial** |

---

## Layouts

| File | Purpose |
|---|---|
| `app/layout.tsx` | Root layout — PWA meta tags, global CSS, font preload |
| `app/dashboard/layout.tsx` | Dashboard layout — wraps dashboard routes |
| `app/admin/layout.tsx` | Admin layout — wraps admin panel routes |

---

## Components

### `components/dashboard/`

| File | Purpose |
|---|---|
| `DashboardShell.tsx` | Sidebar + header shell for all dashboard/admin pages. Role-aware navigation, logout, active route highlighting. |

### `components/dev-chat/`

| File | Purpose |
|---|---|
| `ChatWindow.tsx` | Chat message list and input for the `/dev-chat` developer test UI |

### `components/pwa/`

| File | Purpose |
|---|---|
| `InstallPrompt.tsx` | Shows PWA install banner when `beforeinstallprompt` event fires |
| `OfflineNotice.tsx` | Displays offline state notification |

### `components/voice/`

| File | Purpose |
|---|---|
| `AudioRecorder.tsx` | Browser MediaRecorder wrapper — push-to-talk, recording state, audio blob output |
| `WaveformVisualizer.tsx` | Real-time audio waveform canvas drawn from AnalyserNode |
| `LanguageSelector.tsx` | 12+ Indian languages with icons; stores selection in localStorage |

---

## Lib Files

| File | Purpose |
|---|---|
| `lib/api.ts` | Typed API client — all fetch calls to the FastAPI backend. Includes `createAgentSession()`, `sendAgentMessage()`, `sendVoiceTurn()`, `saveScheme()`, `dashboardLogin()`, `dashboardLogout()`, and 30+ other functions. All calls use `credentials: "include"` for httpOnly cookie auth. |
| `lib/offlineDb.ts` | IndexedDB schema using the `idb` library. Stores: `guestProfile`, `schemeCache`, `conversationHistory`, `syncQueue`. Used for PWA offline support. |
| `lib/websocket.ts` | WebSocket URL helper for chat/voice WS endpoints |
| `lib/audio/` | Audio processing utilities for voice recording |
| `lib/i18n/` | Internationalization helpers and language code mappings |

---

## PWA Files

| File | Purpose |
|---|---|
| `public/manifest.json` | PWA manifest — name, icons, theme color, start URL |
| `public/sw.js` | Service worker — precaches app shell, serves offline page |
| `public/offline.html` | Offline fallback page shown when network is unavailable |
| `public/icons/` | PWA icons at various sizes |

---

## Global Styles

| File | Purpose |
|---|---|
| `app/styles.css` | Full design system — CSS custom properties, responsive breakpoints, card/button/input styles, dark mode support, animations. 15 KB. |

---

## Configuration Files

| File | Purpose |
|---|---|
| `next.config.ts` | Next.js configuration |
| `tsconfig.json` | TypeScript configuration — strict mode, path aliases |
| `playwright.config.ts` | Playwright test configuration — base URL, web server command |
| `package.json` | Dependencies: Next.js 15.5, React 18.2, idb, lucide-react, Playwright |
| `.env.local` | Local env overrides (e.g., `NEXT_PUBLIC_API_BASE_URL`) |

---

## Tests

| File | Type | Coverage |
|---|---|---|
| `tests/phase4.static.test.mjs` | Node static test | PWA manifest, service worker, offline page, install prompt, IndexedDB schema |
| `tests/phase5.static.test.mjs` | Node static test | Dashboard shell, admin routes, component structure |
| `tests/e2e/beneficiary-pwa.spec.ts` | Playwright E2E | Guest flow, scheme display, auth cookie, no JWT in localStorage |
| `tests/e2e/operator-dashboard.spec.ts` | Playwright E2E | Operator list/create, beneficiary detail, notes, follow-ups, unassigned denial |
| `tests/e2e/ngo-admin.spec.ts` | Playwright E2E | Org-scoped access, cross-org denial |
| `tests/e2e/super-admin.spec.ts` | Playwright E2E | Quality flags, unmatched queries, analytics, scheme drafts |
| `tests/e2e/accessibility-smoke.spec.ts` | Playwright E2E | Keyboard focus, accessible names, mobile/tablet/desktop widths |
| `tests/e2e/helpers.ts` | Test helpers | Cookie injection, API helpers, seed data paths |

---

## Key Design Decisions

- **Single Next.js app** for both beneficiary PWA and dashboard — reduces deployment surface and shares auth cookie handling.
- **No client-side routing library** — uses Next.js App Router file-based routing exclusively.
- **No state management library** — uses React `useState`/`useEffect` with `fetch` calls. State is local to each page.
- **httpOnly cookies only** — JWT is never stored in `localStorage` or `sessionStorage`. Enforced by static test + E2E checks.
- **IndexedDB for offline** — uses the `idb` library for typed IndexedDB access. Offline sync queue exists but the automated retry loop is not yet implemented.
