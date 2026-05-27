# Observability & Health

Observability features currently implemented in AdhikarAI, and gaps for production monitoring.

---

## Health Endpoints

| Endpoint | Purpose | Response |
|---|---|---|
| `GET /health` | Liveness probe | `{ status: "ok", database: "ok"/"error", faiss_index: "ok", version: "phase-1" }` |
| `GET /readiness` | Readiness probe | `{ ready: true/false, checks: {...} }` |

**Source**: `backend/app/api/routes/health.py`

The `/health` endpoint pings the database with `SELECT 1` and reports its status. Use for Render health checks and UptimeRobot monitoring.

---

## Request ID Tracing

Every HTTP request is assigned an `X-Request-ID`:
- If the client sends `X-Request-ID`, it is reused
- Otherwise, a new UUID-based ID is generated (`req_<12-hex-chars>`)
- The ID is:
  - Stored in `request.state.request_id`
  - Returned in the response `X-Request-ID` header
  - Included in all error JSON responses

**Source**: `backend/app/main.py` (request_id_middleware)

This enables end-to-end tracing from frontend → backend → error responses.

---

## Scheduled Jobs

APScheduler runs two cron jobs when `ENABLE_SCHEDULER=true`:

| Job | Schedule | Purpose |
|---|---|---|
| Scheme expiry checker | `EXPIRY_CHECK_CRON` (default: `0 2 * * *`, 2 AM daily) | Transitions schemes past `valid_until` to `expired` status. Creates `SchemeStatusEvent` records. |
| Quality monitor | `QUALITY_MONITOR_CRON` (default: `0 * * * *`, hourly) | Checks for quality issues (placeholder; not fully implemented) |

**Source**: `backend/app/services/jobs/scheduler.py`, `backend/app/services/jobs/expiry_checker.py`

---

## Audit Logging

Dashboard write operations are logged to the `audit_logs` table:

| Column | Content |
|---|---|
| `actor_id` | Dashboard member who performed the action |
| `organisation_id` | Tenant scope |
| `action` | e.g., `beneficiary.create`, `beneficiary.update`, `note.create` |
| `resource_type` | e.g., `beneficiary`, `scheme_draft` |
| `resource_id` | ID of the affected resource |
| `metadata` | JSONB with action-specific details |

**Source**: `backend/app/dashboard/audit.py`

**Known limitation**: Audit logging is not on all dashboard write endpoints yet.

---

## Voice Pipeline Metrics

Voice turns are recorded in the `voice_turns` table with timing metrics:

| Metric | Column |
|---|---|
| ASR processing time | `asr_duration_ms` |
| Translation time | `translate_duration_ms` |
| TTS processing time | `tts_duration_ms` |
| Total pipeline time | `total_duration_ms` |
| ASR confidence | `asr_confidence` |
| Detected language | `detected_language` |

**No raw audio is stored.** Only timing metrics and metadata are persisted.

---

## Rate Limit Events

The `rate_limit_events` table tracks rate limit hits:

| Column | Content |
|---|---|
| `actor_type` | `guest`, `user`, `operator` |
| `actor_id` | Session ID or member ID |
| `organisation_id` | Tenant scope |

Redis counters use daily keys with midnight UTC TTL. When `REDIS_URL=memory://`, an in-memory `defaultdict` is used instead.

---

## What Is NOT Implemented Yet

| Capability | Status |
|---|---|
| Structured logging (JSON) | Not implemented — uses default Python logging |
| Centralized log aggregation | Not configured (no Datadog, CloudWatch, etc.) |
| APM / distributed tracing | Not configured |
| Error tracking (Sentry) | Not configured |
| Metrics export (Prometheus) | Not implemented |
| Dashboard analytics at scale | Basic counts only |
| Alerting | No alerting rules configured |
| UptimeRobot keep-warm | Not configured |

---

## Recommendations for Production

1. **Add structured JSON logging** — replace default Python logging with `structlog` or `python-json-logger`
2. **Configure error tracking** — Sentry or equivalent for unhandled exceptions
3. **Add Prometheus metrics** — request latency, error rates, voice pipeline timings
4. **Configure UptimeRobot** — keep-warm pings for Render free tier
5. **Enable Redis health check** — add Redis ping to `/readiness` endpoint
6. **Add request logging middleware** — log method, path, status, latency, request_id
