# E2E Testing

Playwright browser regression tests for AdhikarAI. For the full testing strategy, see [Testing Strategy](testing-strategy.md).

---

## Setup

### Prerequisites

- PostgreSQL running with the `adhikarai` database
- Backend migrated and seeded (see below)
- Node.js 18+ with Playwright browsers installed

### 1. Migrate and Seed Backend

From `backend/`:

```bash
uv run --extra test alembic upgrade head

APP_ENV=local LOCAL_E2E_HELPERS_ENABLED=true \
  uv run --extra test python -m app.cli.local_e2e --cookie-dir /tmp/adhikarai-local-e2e
```

### 2. Start Backend

```bash
APP_ENV=local \
  ENABLE_SCHEDULER=false \
  AUTH_COOKIE_SECURE=false \
  DASHBOARD_AUTH_PROVIDER=dev \
  DASHBOARD_DEV_LOGIN_ENABLED=true \
  DASHBOARD_DEV_LOGIN_CODE=local-e2e-login \
  uv run --extra test uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3. Install Playwright Browsers (once)

From `frontend/`:

```bash
npx playwright install chromium
```

### 4. Run Tests

```bash
npm run test:e2e
```

For headed (visible browser):

```bash
npm run test:e2e:headed
```

`playwright.config.ts` starts the Next.js dev server on `127.0.0.1:3000` automatically. It does not start FastAPI or PostgreSQL.

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `E2E_BASE_URL` | `http://127.0.0.1:3000` | Next.js base URL |
| `E2E_API_URL` | `http://127.0.0.1:8000` | FastAPI base URL |
| `E2E_COOKIE_DIR` | `/tmp/adhikarai-local-e2e` | Directory with pre-authed cookie files |
| `E2E_DASHBOARD_LOGIN_CODE` | `local-e2e-login` | Dev login code for dashboard |
| `NEXT_PUBLIC_ENABLE_DEV_TOOLS` | `true` (local) | Enables `/dev-chat` and `/dev-voice` |

---

## Spec Files

| File | Coverage |
|---|---|
| `beneficiary-pwa.spec.ts` | Guest typed flow, scheme/checklist/status UI smoke, mobile width, no JWT in localStorage |
| `operator-dashboard.spec.ts` | Operator list/create/search, beneficiary detail, notes, follow-ups, eligibility trigger, status update, unassigned-beneficiary denial |
| `ngo-admin.spec.ts` | Org-scoped listing, org-scoped beneficiary detail, cross-org denial |
| `super-admin.spec.ts` | Quality flags, unmatched queries, analytics, scheme draft preview endpoint |
| `accessibility-smoke.spec.ts` | Keyboard focus, accessible names at mobile/tablet/desktop widths |

### Test Helpers

`helpers.ts` provides:
- Cookie injection from seed files
- API call helpers for seeding/resetting test data
- Metadata paths for seeded users

---

## Seed Data

The `local_e2e.py` script creates:
- 2 organisations (default public + test NGO)
- 3 organisation members (operator, NGO admin, super admin)
- Sample beneficiaries with operator assignments
- Pre-authenticated cookie files for each role
- Quality flags, unmatched queries, scheme drafts (fixture data)

Session cookies are written to `E2E_COOKIE_DIR` and consumed by `helpers.ts` for test authentication.

---

## Security Notes

- Dashboard E2E users are seeded members — the shared login code is supplied via environment only
- Backend local E2E helpers are disabled by default (`LOCAL_E2E_HELPERS_ENABLED=false`)
- The seed script refuses to run unless `APP_ENV` is local-like
- No real credentials, OTPs, or Aadhaar numbers are used in test data

---

## Known Limitations

- E2E tests have only been run against local PostgreSQL, not cloud databases
- Voice/audio tests are not included (requires real microphone)
- Tests assume the backend is already running and healthy
- Real LLM, ASR, translation, and TTS providers are not tested (mocked or stubbed)
