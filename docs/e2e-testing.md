# Playwright E2E Testing

AdhikarAI browser regression tests live in `frontend/tests/e2e` and use:

- FastAPI at `http://127.0.0.1:8000`
- Next.js at `http://127.0.0.1:3000`
- local seed/session files from `/tmp/adhikarai-local-e2e`

## Local Setup

From `backend/`, migrate and seed the local E2E data:

```sh
uv run --extra test alembic upgrade head
uv run --extra test python -m app.cli.local_e2e --cookie-dir /tmp/adhikarai-local-e2e
uv run --extra test uvicorn app.main:app --host 127.0.0.1 --port 8000
```

From `frontend/`, run the browser suite:

```sh
npm run test:e2e
```

`playwright.config.ts` starts the local Next.js dev server on `127.0.0.1:3000` and reuses it if already running. It does not start FastAPI or PostgreSQL.

For headed debugging:

```sh
npm run test:e2e:headed
```

If Playwright browsers are missing locally, install them once from `frontend/`:

```sh
npx playwright install chromium
```

## Environment Overrides

- `E2E_BASE_URL`: defaults to `http://127.0.0.1:3000`
- `E2E_API_URL`: defaults to `http://127.0.0.1:8000`
- `E2E_COOKIE_DIR`: defaults to `/tmp/adhikarai-local-e2e`

## Coverage

The suite covers the local workflows documented in `docs/local-e2e-report.md`:

- beneficiary PWA typed guest flow, scheme/checklist/status UI smoke, mobile width, and no JWT in localStorage
- operator dashboard list/create/search, beneficiary detail route, notes, follow-ups, eligibility trigger, status update, and unassigned-beneficiary detail denial
- NGO admin organisation-scoped listing, organisation-scoped beneficiary detail access, and cross-organisation detail denial
- super admin quality, unmatched queries, analytics, and scheme draft preview endpoint smoke
- keyboard focus and accessible-name smoke checks at mobile, tablet, and desktop widths, including the beneficiary detail route
