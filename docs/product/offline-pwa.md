# Offline PWA

AdhikarAI is designed to work offline and on low-bandwidth connections. It achieves this through a combination of a service worker, IndexedDB storage, and an offline sync queue.

---

## Service Worker

**File**: `frontend/public/sw.js`

The service worker:
- Pre-caches key app assets (HTML, CSS, JS, icons) at install time
- Serves cached assets when the network is unavailable
- Serves `offline.html` for navigation requests when the app shell is not cached
- Intercepts API requests and falls back to cached responses or queues failed writes

---

## Offline Page

**File**: `frontend/public/offline.html`

Shown when the browser is offline and the app shell is not cached. Displays a friendly message with an option to retry.

---

## IndexedDB Schema

**File**: `frontend/lib/offlineDb.ts`

All offline data is stored using the `idb` library (a lightweight IndexedDB wrapper).

| Object Store | Key | Contents | Purpose |
|---|---|---|---|
| `guestProfile` | Auto | Profile fields object | Stores profile data before OTP login |
| `savedSchemes` | `schemeId` | Scheme card JSON | Cached saved scheme cards |
| `conversationHistory` | Auto | `{role, content, timestamp}` | Recent conversation turns |
| `checklistItems` | `(schemeId, documentName)` | Checklist item state | Document checklist per scheme |
| `syncQueue` | Auto | `{eventType, payload, createdAt}` | Pending events to sync when online |

---

## Offline Interaction Flow

When a beneficiary is offline:

1. The app detects the offline state via `navigator.onLine`.
2. Voice input is disabled (requires server ASR).
3. Text input is still available; messages are queued in `syncQueue`.
4. Previously cached scheme cards and checklist data are displayed from IndexedDB.
5. When the connection is restored, the sync queue is replayed via `POST /offline-sync`.

---

## Offline Sync API

`POST /offline-sync`

```json
{
  "events": [
    {
      "event_type": "checklist_update",
      "payload": {"scheme_id": "...", "document_name": "Aadhaar", "checked": true},
      "occurred_at": "2026-05-27T10:00:00Z"
    }
  ]
}
```

Returns results per event:
```json
{
  "results": [{"event_type": "checklist_update", "status": "ok"}]
}
```

**Current status**: The endpoint exists and processes events. The sync retry loop (automatic retry when the connection is restored) is not fully implemented as a background task.

---

## PWA Installation

The app can be installed as a home screen icon on Android and iOS:

- `frontend/public/manifest.json` declares the app name, icons, colors, and `display: "standalone"`.
- `frontend/components/pwa/InstallPrompt.tsx` listens for the `beforeinstallprompt` event and shows a custom install button.
- Installed PWAs receive their own browser context and run without the browser chrome.

---

## Status

| Feature | Status |
|---|---|
| Service worker | **Implemented** |
| Offline page | **Implemented** |
| PWA manifest | **Implemented** |
| Install prompt | **Implemented** |
| IndexedDB schema | **Implemented** |
| Guest profile storage | **Implemented** |
| Scheme card cache | **Implemented** |
| Checklist local storage | **Implemented** |
| Sync queue storage | **Implemented** |
| Offline sync API | **Implemented** |
| Sync retry loop | **Partial** — queue helpers exist; auto-retry not implemented |
| Push notification delivery | **Partial** — subscribe endpoint works; no real Web Push dispatch |
| Lighthouse offline verification | **Not run** |
| Playwright offline test | **Written** — requires live backend and service worker registration |

---

## Known Limitations

- The service worker is a basic cache-first strategy. Dynamic API responses are not cached.
- The sync retry loop does not automatically retry failed events when the connection is restored. This must be triggered manually or on next app load.
- Push notification delivery requires VAPID keys (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`) and a Web Push dispatch implementation, neither of which is complete.
- Lighthouse offline/PWA audit has not been run against the production build.
