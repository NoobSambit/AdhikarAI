# Local Development Setup

This guide walks through setting up AdhikarAI on a local machine from scratch through a working typed beneficiary flow and dashboard login.

**Estimated time**: 20–40 minutes (excluding model downloads).

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | `pyenv` or system package |
| `uv` | 0.4+ | `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18+ | `nvm install --lts` or system package |
| npm | 9+ | Bundled with Node.js |
| PostgreSQL | 14+ | `apt install postgresql` or `brew install postgresql` |
| Redis | 7+ | Optional; `memory://` fallback available locally |

---

## 1. Clone the Repository

```sh
git clone <repo-url> AdhikarAI
cd AdhikarAI
```

---

## One-Command Local Stack

If PostgreSQL has already been initialized at `/home/noobsambit/.agent-playground/postgres/data` and Redis is installed, start the full local stack from the repository root:

```sh
npm run dev:local
```

This command:

- checks or starts PostgreSQL on `localhost:5432`
- checks or starts Redis on `localhost:6379`
- runs Alembic migrations
- refreshes local E2E seed data and dashboard users
- starts FastAPI at `http://127.0.0.1:8000`
- starts Next.js at `http://127.0.0.1:3000`
- prints timestamped logs with service prefixes such as `[postgres]`, `[redis]`, `[migrate]`, `[seed]`, `[backend]`, and `[frontend]`

Useful URLs:

```txt
PWA:       http://127.0.0.1:3000
Dashboard: http://127.0.0.1:3000/dashboard/login
API:       http://127.0.0.1:8000/health
```

Dashboard local users:

```txt
operator.local@example.test
ngo-admin.local@example.test
super-admin.local@example.test
```

Access code:

```txt
local-e2e-login
```

To skip reseeding on repeated runs:

```sh
npm run dev:local:no-seed
```

Supported overrides:

```sh
POSTGRES_DATA_DIR=/path/to/postgres/data \
REDIS_URL=redis://localhost:6379/0 \
FRONTEND_PORT=3000 \
BACKEND_PORT=8000 \
DASHBOARD_DEV_LOGIN_CODE=local-e2e-login \
npm run dev:local
```

Press `Ctrl+C` to stop the managed backend, frontend, and Redis process started by the command.

---

## 2. PostgreSQL Setup

If PostgreSQL is already running and you have a superuser role, create the AdhikarAI database user and database:

```sh
sudo -u postgres psql -c "CREATE ROLE adhikarai LOGIN PASSWORD 'adhikarai';"
sudo -u postgres psql -c "CREATE DATABASE adhikarai OWNER adhikarai;"
sudo -u postgres psql -d adhikarai -c "GRANT ALL ON SCHEMA public TO adhikarai;"
```

If you prefer a user-owned data directory (no sudo required):

```sh
mkdir -p ~/.agent-playground/postgres/data
initdb -D ~/.agent-playground/postgres/data
pg_ctl -D ~/.agent-playground/postgres/data \
  -l ~/.agent-playground/postgres/postgres.log \
  -o '-h localhost -p 5432 -k ~/.agent-playground/postgres/socket' start

# Connect as local user and create role + database
psql -h localhost -p 5432 -U "$(whoami)" -d postgres \
  -c "CREATE ROLE adhikarai LOGIN PASSWORD 'adhikarai';"
createdb -h localhost -p 5432 -U "$(whoami)" -O adhikarai adhikarai
psql -h localhost -p 5432 -U "$(whoami)" -d adhikarai \
  -c "GRANT ALL ON SCHEMA public TO adhikarai;"
```

Verify the connection:

```sh
psql postgresql://adhikarai:adhikarai@localhost:5432/adhikarai -c 'select current_database();'
```

---

## 3. Redis Setup (Optional)

Redis is optional locally. If Redis is not installed, set `REDIS_URL=memory://` in `.env` and rate limiting, translation cache, and TTS cache will use in-process memory.

To install and start Redis on Debian/Ubuntu:

```sh
sudo apt install redis-server
sudo systemctl start redis
redis-cli ping  # should return PONG
```

---

## 4. Backend Setup

```sh
cd backend
```

### 4a. Create the environment file

```sh
cp .env.example .env
```

Edit `.env` for local values. The minimum required changes from the example:

```env
APP_ENV=local
DATABASE_URL=postgresql+asyncpg://adhikarai:adhikarai@localhost:5432/adhikarai
DATABASE_DIRECT_URL=postgresql+asyncpg://adhikarai:adhikarai@localhost:5432/adhikarai
REDIS_URL=memory://
AUTH_COOKIE_SECURE=false
AUTH_JWT_SECRET=local-dev-secret-at-least-32-chars
ADMIN_API_TOKEN=local-admin-token
```

For dashboard dev login (optional):

```env
DASHBOARD_AUTH_PROVIDER=dev
DASHBOARD_DEV_LOGIN_ENABLED=true
DASHBOARD_DEV_LOGIN_CODE=local-e2e-login
```

See [environment-variables.md](environment-variables.md) for the full reference.

### 4b. Install dependencies

```sh
uv sync --extra test
```

### 4c. Run migrations

```sh
uv run --extra test alembic upgrade head
uv run --extra test alembic current  # should show 0005_phase_5 (head)
```

### 4d. Seed initial data (optional but recommended)

The seed command creates the default public organisation and loads sample central government schemes:

```sh
APP_ENV=local LOCAL_E2E_HELPERS_ENABLED=true uv run --extra test \
  python -m app.cli.local_e2e --cookie-dir /tmp/adhikarai-local-e2e
```

This creates:
- Public organisation (`00000000-0000-0000-0000-000000000001`)
- Sample schemes and eligibility rules
- Dashboard members (operator, NGO admin, super admin)
- Cookie files for E2E testing at `/tmp/adhikarai-local-e2e/`

### 4e. Start the backend

```sh
APP_ENV=local \
ENABLE_SCHEDULER=false \
AUTH_COOKIE_SECURE=false \
DASHBOARD_AUTH_PROVIDER=dev \
DASHBOARD_DEV_LOGIN_ENABLED=true \
DASHBOARD_DEV_LOGIN_CODE=local-e2e-login \
uv run --extra test uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or if your `.env` already has those values:

```sh
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify:

```sh
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok","database":"ok"}
```

---

## 5. Frontend Setup

```sh
cd frontend
npm install
```

Create the frontend env file:

```sh
echo 'NEXT_PUBLIC_API_BASE_URL=http://localhost:8000' > .env.local
```

Start the development server:

```sh
npm run dev
```

Visit `http://localhost:3000` — the beneficiary PWA should load.

---

## 6. Verify the Setup

### Backend health

```sh
curl http://127.0.0.1:8000/health
```

Expected: `{"status":"ok","database":"ok"}`

### CORS preflight

```sh
curl -sS -I -X OPTIONS http://127.0.0.1:8000/agent/sessions \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
```

Expected: `access-control-allow-origin: http://localhost:3000`

### Typed beneficiary flow

```sh
# 1. Create session
curl -sS -X POST http://127.0.0.1:8000/agent/sessions \
  -H "Content-Type: application/json" \
  -d '{"organisation_id":"00000000-0000-0000-0000-000000000001"}'

# 2. Send a message (use session_id from above response)
curl -sS -X POST http://127.0.0.1:8000/agent/message \
  -H "Content-Type: application/json" \
  -d '{"organisation_id":"00000000-0000-0000-0000-000000000001","session_id":"<session_id>","message":"I am a widow aged 52 living in Odisha"}'
```

### Frontend routes

```sh
curl -sS -I http://127.0.0.1:3000/
curl -sS -I http://127.0.0.1:3000/dashboard
curl -sS -I http://127.0.0.1:3000/admin/quality
curl -sS -I http://127.0.0.1:3000/manifest.json
```

All should return `200`.

---

## 7. Run Backend Tests

```sh
cd backend
uv run --extra test pytest
```

Expected: 55 tests pass.

---

## 8. Run Frontend Tests

```sh
cd frontend
npm run typecheck    # TypeScript check
npm run test:phase4  # Phase 4 static tests
node tests/phase5.static.test.mjs  # Phase 5 static tests
```

---

## 9. Playwright E2E Tests

Playwright E2E tests require:
- Backend running at `http://127.0.0.1:8000`
- Seed data in `/tmp/adhikarai-local-e2e`

```sh
cd frontend
npx playwright install chromium  # first time only
npm run test:e2e
```

For headed debugging:

```sh
npm run test:e2e:headed
```

See [../e2e-testing.md](../e2e-testing.md) and [../engineering/e2e-testing.md](../engineering/e2e-testing.md) for full Playwright setup.

---

## 10. Developer Tools

| URL | Purpose |
|---|---|
| `http://localhost:3000/dev-chat` | Agent conversation test UI |
| `http://localhost:3000/dev-voice` | Voice pipeline test UI |
| `http://localhost:8000/docs` | FastAPI auto-generated OpenAPI docs |
| `http://localhost:8000/redoc` | FastAPI ReDoc UI |

> **Note:** `/dev-chat` and `/dev-voice` are development-only routes. They should be hidden in staging/production by not exposing `NEXT_PUBLIC_ENABLE_DEV_TOOLS`.

---

## 11. Typer Admin CLI

The admin CLI provides commands for seed loading, index rebuilding, and local E2E helpers:

```sh
# Install CLI script
cd backend
uv run adhikarai-admin --help

# Seed schemes from JSON file
uv run adhikarai-admin seed --file app/seeds/central_schemes.v1.json

# Rebuild FAISS index
uv run adhikarai-admin rebuild-index
```

---

## Common Issues

See [troubleshooting.md](troubleshooting.md) for common failures.
