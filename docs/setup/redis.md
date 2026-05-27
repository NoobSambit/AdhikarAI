# Redis

AdhikarAI uses Redis for:

1. **Agent conversation session state** — per-session JSON blob stored in Redis, keyed by `session_id`
2. **Translation cache** — translated text cached by `(provider, source_lang, target_lang, text_hash)` with 7-day TTL
3. **TTS cache** — synthesized audio URL cached with 24-hour TTL
4. **Rate limit counters** — daily per-actor counters using Redis `INCR` + expiry

---

## Local Setup

### Option A: Use memory:// (no Redis required)

Set in `backend/.env`:

```env
REDIS_URL=memory://
```

This uses an in-process `defaultdict` for all Redis operations. It is sufficient for local development and CI. Limitations:
- No persistence across restarts
- No sharing across multiple workers or processes
- Rate limit counters reset on restart

### Option B: Install Redis locally

```sh
# Debian/Ubuntu
sudo apt install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Verify
redis-cli ping  # → PONG
```

Then set in `backend/.env`:

```env
REDIS_URL=redis://localhost:6379/0
```

---

## Staging / Production

Use Upstash Redis (Redis-compatible managed service):

1. Create an Upstash Redis database at [upstash.com](https://upstash.com)
2. Copy the `rediss://` connection string
3. Set in environment:

```env
REDIS_URL=rediss://:password@host.upstash.io:6380
```

**Requirements in staging/production:**
- `REDIS_URL` must start with `redis://` or `rediss://`
- `memory://` is rejected at startup in staged/production environments
- The config validator (`Settings.validate_environment`) enforces this

---

## Redis Key Patterns

| Purpose | Key Pattern | TTL |
|---|---|---|
| Session state | `session:{organisation_id}:{session_id}` | `SESSION_TTL_SECONDS` (30 days) |
| Translation cache | `translation:{provider}:{src}:{tgt}:{sha256[:16]}` | `TRANSLATION_CACHE_TTL_SECONDS` (7 days) |
| TTS cache | `tts:{provider}:{lang}:{sha256[:16]}` | `TTS_CACHE_TTL_SECONDS` (24 hours) |
| Rate limit (guest) | `rate:{org_id}:guest:{session_id}:{date}` | Until next midnight |
| Rate limit (operator) | `rate:{org_id}:operator:{member_id}:{date}` | Until next midnight |
| Rate limit (user) | `rate:{org_id}:user:{user_id}:{date}` | Until next midnight |

---

## Rate Limiting Details

Rate limits are enforced using Redis `INCR`:

1. On each request, `INCR key` is called atomically.
2. If `count == 1`, `EXPIRE key` is set to seconds until next midnight (UTC).
3. If `count > limit`, `ApiError(429, "RATE_LIMIT_EXCEEDED")` is raised.
4. The error response includes `retry_after_seconds` and `retry_at` ISO timestamp.

Default limits (all configurable):

| Actor type | Variable | Default |
|---|---|---|
| Guest (unauthenticated) | `RATE_LIMIT_GUEST_PER_DAY` | 50 per session per day |
| Authenticated user | `RATE_LIMIT_USER_PER_DAY` | 100 per user per day |
| Operator | `RATE_LIMIT_OPERATOR_PER_DAY` | 1000 per member per day |

The rate limit key includes `organisation_id` so limits are scoped per organisation. A super admin in one org cannot exhaust the limits of another org.

---

## Translation and TTS Cache

Both the translation client (`app/translation/client.py`) and TTS client (`app/tts/client.py`) use Redis caching before calling provider APIs:

```
Request → Hash input → Check Redis
  Cache hit  → Return cached response
  Cache miss → Call provider → Store in Redis → Return
```

If `REDIS_URL=memory://`, caching still works but is per-process and not persistent.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ConnectionRefusedError` on `redis://localhost:6379` | Start Redis: `sudo systemctl start redis` or use `REDIS_URL=memory://` |
| Rate limit errors in local testing | Use `REDIS_URL=memory://` and restart server to reset counters, or use a test prefix |
| Cache not working | Check that `REDIS_URL` is reachable. Check Redis is not full (check `redis-cli info memory`) |
| `REDIS_URL=memory://` in staging | Fix: set `REDIS_URL` to a real `redis://` or `rediss://` URL |
