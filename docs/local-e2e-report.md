# AdhikarAI Local E2E Bring-Up Report

Date: 2026-05-23 10:21 IST

## Local Services

- PostgreSQL: running locally on `localhost:5432`.
  - The system PostgreSQL service initially accepted connections only after `systemctl start postgresql`, but the `postgres` role required a password and `sudo -n -u postgres ...` was denied.
  - Used the existing user-owned PostgreSQL data directory at `/home/noobsambit/.agent-playground/postgres/data` with local trust auth.
- Redis: blocked.
  - `redis-server` and `redis-cli` were not installed.
  - TCP check to `127.0.0.1:6379` returned `ECONNREFUSED`.
  - Local backend uses `REDIS_URL=memory://`.
- FastAPI: running at `http://127.0.0.1:8000`.
- Next.js: running at `http://127.0.0.1:3000`.

## Exact Setup Commands Used

```sh
pg_isready -h localhost -p 5432
psql postgresql://adhikarai:adhikarai@localhost:5432/adhikarai -c 'select current_database(), current_user;'
which uv npm node psql redis-cli
node -e "const net=require('net'); const s=net.createConnection(6379,'127.0.0.1'); s.setTimeout(1000); s.on('connect',()=>{console.log('redis_tcp=open'); s.end();}); s.on('timeout',()=>{console.log('redis_tcp=timeout'); s.destroy();}); s.on('error',(e)=>{console.log('redis_tcp=error '+e.code);});"
systemctl status postgresql --no-pager
systemctl start postgresql
systemctl stop postgresql
pg_ctl -D /home/noobsambit/.agent-playground/postgres/data -l /home/noobsambit/.agent-playground/postgres/postgres.log -o '-h localhost -p 5432 -k /home/noobsambit/.agent-playground/postgres/socket' start
psql -h localhost -p 5432 -U agent_playground -d postgres -c 'select current_database(), current_user;'
psql -h localhost -p 5432 -U agent_playground -d postgres -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'adhikarai') THEN CREATE ROLE adhikarai LOGIN PASSWORD 'adhikarai'; END IF; END \$\$;"
createdb -h localhost -p 5432 -U agent_playground -O adhikarai adhikarai
psql -h localhost -p 5432 -U agent_playground -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE adhikarai TO adhikarai;"
psql -h localhost -p 5432 -U agent_playground -d adhikarai -c "GRANT ALL ON SCHEMA public TO adhikarai; ALTER SCHEMA public OWNER TO adhikarai;"
uv run --extra test alembic upgrade head
uv run --extra test alembic current
APP_ENV=local LOCAL_E2E_HELPERS_ENABLED=true uv run --extra test python -m app.cli.local_e2e --cookie-dir /tmp/adhikarai-local-e2e
APP_ENV=local ENABLE_SCHEDULER=false AUTH_COOKIE_SECURE=false DASHBOARD_AUTH_PROVIDER=dev DASHBOARD_DEV_LOGIN_ENABLED=true DASHBOARD_DEV_LOGIN_CODE=local-e2e-login uv run --extra test uvicorn app.main:app --host 127.0.0.1 --port 8000
npm run dev -- --hostname 127.0.0.1 --port 3000
```

## Env Files

- Created `backend/.env` with local-safe values.
  - PostgreSQL: `postgresql+asyncpg://adhikarai:...@localhost:5432/adhikarai`
  - Redis: `memory://` because Redis is unavailable.
  - Auth: local dev JWT secret, insecure cookie disabled for local HTTP.
  - Dashboard auth: local-only dev provider enabled from shell env; the login code is not written to seed metadata.
  - Providers: mock/local provider settings only; no production credentials.
- Created `frontend/.env.local`.
  - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- Updated `backend/.env.example` with `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`.

## Database Migration Result

- Live Alembic upgrade against local PostgreSQL passed.
- Current revision: `0005_phase_5 (head)`.

## Seed Data Created

Seed command:

```sh
APP_ENV=local LOCAL_E2E_HELPERS_ENABLED=true uv run --extra test python -m app.cli.local_e2e --cookie-dir /tmp/adhikarai-local-e2e
```

Created or reused:

- Public organisation: `00000000-0000-0000-0000-000000000001`
- Other local NGO organisation: `00000000-0000-0000-0000-000000000002`
- Central sample schemes and eligibility rules from `backend/app/seeds/central_schemes.v1.json`
- Dashboard members:
  - operator: `operator.local@example.test`
  - second operator for denial checks: `operator2.local@example.test`
  - NGO admin: `ngo-admin.local@example.test`
  - super admin: `super-admin.local@example.test`
  - other-org operator: `other-operator.local@example.test`
- Beneficiaries:
  - assigned beneficiary for the operator
  - unassigned beneficiary assigned to the second operator
  - other-organisation beneficiary
  - operator-created beneficiary during workflow verification
- Application status rows, follow-ups, unmatched query fixture, quality flag fixture.
- Local cookie jars:
  - `/tmp/adhikarai-local-e2e/operator.cookie`
  - `/tmp/adhikarai-local-e2e/ngo_admin.cookie`
  - `/tmp/adhikarai-local-e2e/super_admin.cookie`
  - `/tmp/adhikarai-local-e2e/beneficiary.cookie`

The metadata file includes seeded member emails and IDs for UI login. It does not include the dashboard login code.

No Aadhaar numbers or raw documents were stored.

## Workflows Tested

| Workflow | Result | Evidence |
|---|---:|---|
| FastAPI health | pass | `GET /health` returned 200 with `database:"ok"`. |
| CORS preflight from local Next | pass | `OPTIONS /agent/sessions` with `Origin: http://localhost:3000` returned 200 and `access-control-allow-origin`. |
| Beneficiary typed PWA flow | pass | `POST /agent/sessions` then `POST /agent/message` returned a result with an eligible scheme. |
| Beneficiary save/checklist/status | pass | Authenticated `POST /saved-schemes`, `PATCH /checklists`, and `PATCH /application-status` returned 200. |
| Operator dashboard session | pass | UI login through `/dashboard/login` set an httpOnly cookie; `GET /dashboard/me` returned operator role and permissions. |
| Operator create beneficiary | pass after fix | `POST /dashboard/beneficiaries` returned 201-equivalent JSON body after audit FK fix. |
| Operator list/search/detail | pass | `GET /dashboard/beneficiaries?q=Operator%20Created` and detail route returned 200. |
| Operator add note | pass | `POST /dashboard/beneficiaries/{id}/notes` returned 200. |
| Operator add follow-up | pass | `POST /dashboard/beneficiaries/{id}/followups` returned 200. |
| Operator update application status | pass | `PATCH /dashboard/application-status/{status_id}` returned 200. |
| Operator denial for unassigned beneficiary | pass | `GET /dashboard/beneficiaries/{unassigned_id}` returned 403 `BENEFICIARY_NOT_ASSIGNED`. |
| NGO admin organisation-scoped list | pass | `GET /dashboard/beneficiaries` showed own organisation only. |
| NGO admin cross-org denial | pass | Other organisation beneficiary detail returned 403 `ORG_SCOPE_DENIED`. |
| Super admin analytics | pass | `GET /admin/analytics` returned 200. |
| Super admin unmatched queries | pass | `GET /admin/unmatched-queries` returned 200. |
| Super admin quality flags | pass | `GET /admin/quality-flags` returned 200. |
| Super admin scheme draft preview | pass after fix | `POST /admin/scheme-drafts` and `POST /admin/scheme-drafts/{id}/preview` returned 200. |
| Next route smoke | pass | `/`, `/dashboard`, `/admin/quality`, and `/manifest.json` returned 200 from Next dev server. |

## Redis-Backed Rate Limit Result

- Redis-backed verification: blocked.
- Reason: Redis is not installed and no service is listening on `127.0.0.1:6379`.
- Fallback verified: `REDIS_URL=memory://`, and `POST /dashboard/beneficiaries/{id}/eligibility` returned 200 through a rate-limited endpoint.

## Verification Run

```sh
uv run --extra test alembic upgrade head
uv run --extra test alembic current
uv run --extra test python -m compileall app
uv run --extra test pytest
npm run typecheck
npm run build
npm run test:phase4 && node tests/phase5.static.test.mjs
curl -sS -i http://127.0.0.1:8000/health
curl -sS -I http://127.0.0.1:3000/
curl -sS -I http://127.0.0.1:3000/dashboard
curl -sS -I http://127.0.0.1:3000/admin/quality
```

Results:

- Backend tests: 55 passed.
- Frontend typecheck: passed.
- Frontend build: passed, 18 routes generated.
- Frontend static tests: passed.
- FastAPI route smoke: passed.
- Next route smoke: passed.
- Live PostgreSQL migration: passed.

## Fixes Made

1. Added config-backed CORS middleware for local frontend origins.
2. Added a local-only E2E seed/session helper at `backend/app/cli/local_e2e.py`.
3. Fixed dashboard audit logs so admin-backed dashboard actors do not write `admin_user_id` into the `audit_logs.actor_user_id` foreign key.
4. Fixed new scheme-draft creation so drafts for not-yet-created schemes keep the desired scheme id in payload but do not set the nullable `scheme_drafts.scheme_id` FK until the scheme exists.
5. Added local-only dashboard dev login and production/staging config validation; deployed environments reject dev dashboard login and `memory://` Redis.

## Known Blockers

- Redis-backed rate-limit smoke is blocked until Redis is installed and running locally.
- Local voice provider smoke was not completed because Whisper.cpp, IndicTrans2, and IndicTTS local services were not verified as running. Typed beneficiary flow was verified successfully.

## Manual Commands Needed

No manual privileged command is required for the current local bring-up. Redis-backed verification requires installing and starting Redis locally, then changing `backend/.env` from `REDIS_URL=memory://` to `REDIS_URL=redis://localhost:6379/0` and restarting FastAPI.
