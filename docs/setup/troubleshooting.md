# Troubleshooting

Common issues and fixes for local AdhikarAI development.

---

## Backend Won't Start

### `AUTH_JWT_SECRET must be a non-default value`

**Cause**: Running with `APP_ENV=staging` or `APP_ENV=production` but `AUTH_JWT_SECRET` is still the default `change-me-phase-4`.

**Fix**: Set a random secret in `.env`:
```env
AUTH_JWT_SECRET=some-long-random-string-at-least-32-chars
APP_ENV=local
```

---

### `DATABASE_URL must be a deployed database URL`

**Cause**: `APP_ENV=staging` or `APP_ENV=production` with localhost database URL.

**Fix**: Set `APP_ENV=local` for local development, or provide a real cloud database URL.

---

### `REDIS_URL must be redis:// or rediss://`

**Cause**: `APP_ENV=staging` or `APP_ENV=production` with `REDIS_URL=memory://`.

**Fix**: Use a real Redis URL or set `APP_ENV=local`.

---

### `ValidationError` on startup about `DASHBOARD_AUTH_PROVIDER`

**Cause**: `DASHBOARD_AUTH_PROVIDER` is set to something other than `disabled` or `dev`.

**Fix**:
```env
DASHBOARD_AUTH_PROVIDER=disabled   # production/staging
# OR
DASHBOARD_AUTH_PROVIDER=dev        # local development only
```

---

## Database Connection Errors

### `Connection refused on localhost:5432`

**Cause**: PostgreSQL is not running.

**Fix**:
```sh
# System PostgreSQL
sudo systemctl start postgresql

# User-owned data directory
pg_ctl -D ~/.agent-playground/postgres/data start
```

---

### `role "adhikarai" does not exist`

**Cause**: The database role hasn't been created.

**Fix**:
```sh
sudo -u postgres psql -c "CREATE ROLE adhikarai LOGIN PASSWORD 'adhikarai';"
sudo -u postgres psql -c "CREATE DATABASE adhikarai OWNER adhikarai;"
```

---

### `Alembic upgrade head` fails with `connection refused`

**Cause**: PostgreSQL is not running or `DATABASE_URL` is wrong.

**Fix**: Start PostgreSQL and verify the connection string:
```sh
psql postgresql://adhikarai:adhikarai@localhost:5432/adhikarai -c 'select 1;'
```

---

### Alembic `Target database is not up to date`

**Cause**: Running the app against a database that has not been migrated.

**Fix**:
```sh
cd backend
uv run --extra test alembic upgrade head
```

---

## Frontend Issues

### `NEXT_PUBLIC_API_BASE_URL is not set`

**Cause**: Missing `frontend/.env.local`.

**Fix**:
```sh
echo 'NEXT_PUBLIC_API_BASE_URL=http://localhost:8000' > frontend/.env.local
```

---

### TypeScript errors on `npm run typecheck`

**Cause**: Type mismatch introduced in a recent change.

**Fix**: Review the error output and fix the type. Do not use `// @ts-ignore` as a workaround unless explicitly approved.

---

### `npm run build` fails with `Page component not found`

**Cause**: A Next.js route directory is missing its `page.tsx` file.

**Fix**: Add a `page.tsx` export to the directory.

---

## Test Failures

### Backend tests fail with `asyncpg` errors

**Cause**: Backend tests use `aiosqlite` (in-memory SQLite) by default, not PostgreSQL. An `asyncpg`-specific SQL feature was used.

**Fix**: Make sure the test uses a SQLite-compatible query, or mark it as requiring PostgreSQL.

---

### Backend tests fail with `import` errors

**Cause**: A new dependency was added to `pyproject.toml` but `uv sync` was not run.

**Fix**:
```sh
cd backend
uv sync --extra test
```

---

### Playwright E2E tests fail with `Target page, context or browser has been closed`

**Cause**: Backend or frontend is not running when tests start.

**Fix**: Start both servers before running E2E tests:
```sh
# Terminal 1: backend
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: frontend
cd frontend
npm run dev

# Terminal 3: tests
cd frontend
npm run test:e2e
```

---

### Playwright tests fail with `Error: ENOENT: no such file or directory, '/tmp/adhikarai-local-e2e/operator.cookie'`

**Cause**: Seed/E2E helper not run yet.

**Fix**:
```sh
cd backend
APP_ENV=local LOCAL_E2E_HELPERS_ENABLED=true \
  uv run --extra test python -m app.cli.local_e2e \
  --cookie-dir /tmp/adhikarai-local-e2e
```

---

## Rate Limit Issues

### Getting 429 errors immediately in local testing

**Cause**: In-memory rate limit counters accumulate across requests without resetting.

**Fix**: Restart the FastAPI server to reset in-memory counters, or use a unique `session_id` per test run:
```sh
# Reset by restarting
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## Voice / ASR Issues

### `VOICE_PROVIDER=local` but Whisper.cpp binary not found

**Cause**: Whisper.cpp binary is not at the configured path.

**Fix**: Either install Whisper.cpp and set `WHISPER_CPP_BINARY` to the correct path, or switch to mock:
```env
VOICE_PROVIDER=browser  # use browser-side Web Speech API
```
For Groq ASR:
```env
VOICE_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

---

### Translation/TTS errors with local providers

**Cause**: IndicTrans2 or IndicTTS local HTTP services are not running.

**Fix**: Start the local services or switch providers:
```env
TRANSLATION_PROVIDER=google
GOOGLE_TRANSLATE_API_KEY=your_key

TTS_PROVIDER=google
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## Dashboard Issues

### `POST /dashboard/auth/login` returns `DASHBOARD_AUTH_NOT_CONFIGURED`

**Cause**: `DASHBOARD_AUTH_PROVIDER=disabled` (the default).

**Fix for local only**:
```env
DASHBOARD_AUTH_PROVIDER=dev
DASHBOARD_DEV_LOGIN_ENABLED=true
DASHBOARD_DEV_LOGIN_CODE=local-e2e-login
```

> Do not enable dev login in staging or production.

---

### `GET /dashboard/me` returns `401 NOT_AUTHENTICATED`

**Cause**: No dashboard session cookie present.

**Fix**: Log in first via `POST /dashboard/auth/login` (with dev login enabled), or use the cookie file created by the local E2E seed helper.

---

## Getting Help

1. Check this troubleshooting guide.
2. Check `docs/local-e2e-report.md` for verified local setup commands.
3. Check `docs/prd-compliance-audit.md` for known gaps and limitations.
4. Check `docs/agent-change-log.md` for recent changes that may have introduced the issue.
