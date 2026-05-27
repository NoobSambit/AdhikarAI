# Environment Variables Reference

All environment variables for the AdhikarAI backend. The canonical source is [`backend/.env.example`](../../backend/.env.example). The frontend has a small set of `NEXT_PUBLIC_` variables.

**Security requirement:** Variables marked **MUST CHANGE** must never use their default value in staging or production. The backend's `Settings.validate_environment()` validator will **reject startup** if these are still defaults.

---

## Application

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `APP_ENV` | `local` | Yes (`staging` or `production`) | Controls environment-specific validation |
| `APP_TIMEZONE` | `Asia/Kolkata` | No | Timezone for scheduler and timestamps |
| `FASTAPI_HOST` | `0.0.0.0` | No | Bind host for uvicorn |
| `FASTAPI_PORT` | `8000` | No | Bind port for uvicorn |

---

## CORS

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Yes — **MUST CHANGE** | Comma-separated list of allowed origins. Never use `*` or localhost in production. |

---

## Database

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://adhikarai:adhikarai@localhost:5432/adhikarai` | Yes — **MUST CHANGE** | Async PostgreSQL URL. Must be a deployed URL in staging/production. |
| `DATABASE_DIRECT_URL` | Same as `DATABASE_URL` | Yes — **MUST CHANGE** | Direct (non-pooled) URL used by Alembic migrations. For Neon, use the direct connection string. |
| `DB_POOL_SIZE` | `3` | No | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | `2` | No | Max overflow connections |
| `DB_POOL_TIMEOUT` | `10` | No | Pool timeout seconds |
| `DB_POOL_RECYCLE` | `300` | No | Connection recycle interval seconds |

---

## Redis

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | Yes — **MUST CHANGE** | Must be `redis://` or `rediss://` in staging/production. Set to `memory://` only for local/test (no persistence). |
| `SESSION_TTL_SECONDS` | `2592000` | No | Conversation session TTL in Redis (30 days) |

> **Important**: `memory://` is only for local development and tests. It provides no persistence and no real rate-limiting correctness across restarts or workers.

---

## Auth — JWT & Cookies

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `AUTH_JWT_SECRET` | `change-me-phase-4` | Yes — **MUST CHANGE** | Must be at least 32 characters and non-default. Used to sign all JWTs. |
| `AUTH_COOKIE_NAME` | `adhikarai_session` | No | Name of the session cookie |
| `AUTH_COOKIE_SECURE` | `true` | Yes (`true` in prod) | Must be `true` in staging/production (HTTPS). Set to `false` only for local HTTP. |
| `AUTH_COOKIE_SAMESITE` | `lax` | No | Must be `lax`, `strict`, or `none`. Use `none` for cross-site Vercel-to-Render; requires `AUTH_COOKIE_SECURE=true`. |
| `AUTH_COOKIE_DOMAIN` | _(empty)_ | No | Set only for shared subdomain auth. Leave empty for default. |
| `AUTH_JWT_TTL_SECONDS` | `2592000` | No | JWT expiry (30 days) |

---

## Auth — OTP

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `OTP_PROVIDER` | `mock` | Yes (`msg91` in production) | `mock` logs OTP; `msg91` sends real SMS. Production rejects `mock`. Staging may use `mock` with `ALLOW_MOCK_OTP_IN_STAGING=true`. |
| `OTP_EXPIRY_SECONDS` | `300` | No | OTP validity window (5 minutes) |
| `OTP_RETRY_AFTER_SECONDS` | `30` | No | Cooldown between OTP sends |
| `OTP_MAX_ATTEMPTS` | `5` | No | Max verify attempts per challenge |
| `MSG91_BASE_URL` | `https://control.msg91.com/api/v5` | No | MSG91 API base URL |
| `MSG91_AUTH_KEY` | _(empty)_ | Yes if `OTP_PROVIDER=msg91` | MSG91 authentication key. Never commit this. |
| `MSG91_TEMPLATE_ID` | _(empty)_ | Yes if `OTP_PROVIDER=msg91` | MSG91 OTP template ID |
| `ALLOW_MOCK_OTP_IN_STAGING` | `false` | No | Set to `true` to allow mock OTP in staging |

---

## Admin

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `ADMIN_API_TOKEN` | `change-me` | Yes — **MUST CHANGE** | Bearer token for admin API routes (`X-Admin-Token` header). Must be non-default. |

---

## LLM

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `LLM_PROVIDER` | `ollama` | No | `ollama` or `groq` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | If `LLM_PROVIDER=ollama` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | No | Primary model |
| `OLLAMA_FALLBACK_MODEL` | `qwen2.5:7b` | No | Fallback model |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | No | Groq API base URL |
| `GROQ_API_KEY` | _(empty)_ | Yes if `LLM_PROVIDER=groq` | Groq API key. Never commit this. |
| `GROQ_CHAT_MODEL` | `llama-3.3-70b-versatile` | No | Primary Groq chat model |
| `GROQ_FALLBACK_MODEL` | `llama-3.1-8b-instant` | No | Groq fallback model |
| `AGENT_TEMPERATURE` | `0.1` | No | LLM sampling temperature |
| `AGENT_MAX_TOKENS` | `512` | No | Max tokens per agent response |
| `AGENT_JSON_REPAIR_RETRIES` | `1` | No | Retries for malformed JSON from LLM |
| `AGENT_MAX_QUESTIONS_BEFORE_RESULT` | `8` | No | Hard cap on agent questions |
| `AGENT_TIMEOUT_SECONDS` | `20` | No | Agent turn timeout |

---

## Voice / ASR

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `VOICE_PROVIDER` | `local` | No | `local` (Whisper.cpp) or `groq` |
| `ASR_MIN_CONFIDENCE` | `0.70` | No | Minimum ASR confidence to proceed to agent |
| `VOICE_MAX_UTTERANCE_SECONDS` | `20` | No | Maximum allowed utterance length |
| `VOICE_MAX_UPLOAD_MB` | `8` | No | Maximum audio upload size |
| `BROWSER_ASR_FALLBACK_AFTER_MS` | `2000` | No | Fallback timeout for browser ASR |
| `GROQ_WHISPER_MODEL` | `whisper-large-v3-turbo` | No | Groq Whisper model |
| `GROQ_AUDIO_TRANSCRIPTIONS_URL` | _(derived)_ | No | Override Groq ASR URL |
| `WHISPER_CPP_BINARY` | `/opt/whisper.cpp/build/bin/whisper-cli` | If `VOICE_PROVIDER=local` | Path to whisper.cpp binary |
| `WHISPER_CPP_MODEL_PATH` | `/models/ggml-large-v3.bin` | If `VOICE_PROVIDER=local` | Path to GGML model file |
| `WHISPER_CPP_ARGS` | `-l auto -otxt -ojf --print-progress false --no-timestamps` | No | Whisper.cpp CLI arguments |
| `ASR_TIMEOUT_SECONDS` | `12` | No | ASR transcription timeout |
| `STORE_AUDIO_DEBUG` | `false` | Must be `false` in prod | Store debug audio files. Never enable in production. |

---

## Translation

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `TRANSLATION_PROVIDER` | `local_indictrans2` | No | `local_indictrans2`, `ai4bharat_hosted`, or `google` |
| `TRANSLATION_SERVICE_URL` | `http://localhost:8001` | If `local_indictrans2` | URL of local IndicTrans2 HTTP service |
| `AI4BHARAT_TRANSLATE_URL` | _(empty)_ | If `ai4bharat_hosted` | AI4Bharat hosted translation endpoint |
| `AI4BHARAT_API_KEY` | _(empty)_ | If `ai4bharat_hosted` | AI4Bharat API key. Never commit. |
| `AI4BHARAT_TIMEOUT_SECONDS` | `3` | No | AI4Bharat API timeout |
| `GOOGLE_TRANSLATE_API_KEY` | _(empty)_ | If `TRANSLATION_PROVIDER=google` | Google Translate API key. Never commit. |
| `GOOGLE_TRANSLATE_URL` | `https://translation.googleapis.com/language/translate/v2` | No | |
| `TRANSLATION_CACHE_TTL_SECONDS` | `604800` | No | Translation Redis cache TTL (7 days) |

---

## TTS

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `TTS_PROVIDER` | `local_indictts` | No | `local_indictts` or `google` |
| `LOCAL_TTS_URL` | `http://localhost:8002` | If `local_indictts` | URL of local IndicTTS HTTP service |
| `LOCAL_TTS_TIMEOUT_SECONDS` | `8` | No | Local TTS request timeout |
| `GOOGLE_TTS_URL` | `https://texttospeech.googleapis.com/v1/text:synthesize` | No | |
| `GOOGLE_APPLICATION_CREDENTIALS` | _(empty)_ | If `TTS_PROVIDER=google` | Path to Google service account JSON. Never commit. |
| `TTS_CACHE_TTL_SECONDS` | `86400` | No | TTS audio Redis cache TTL (24 hours) |

---

## Eligibility

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `ELIGIBILITY_ENGINE` | `experta` | No | `experta` (only supported value) |
| `EMBEDDING_PROVIDER` | `sentence_transformers` | No | Embedding model provider |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-small` | No | Model name for embeddings |
| `FAISS_INDEX_DIR` | `./data/faiss` | No | Directory for FAISS index files |

---

## Scheduler

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `ENABLE_SCHEDULER` | `true` | No | Set to `false` to disable APScheduler (useful in tests) |
| `EXPIRY_CHECK_CRON` | `0 2 * * *` | No | Cron expression for scheme expiry check (2 AM daily) |
| `QUALITY_MONITOR_CRON` | `0 * * * *` | No | Cron expression for quality monitoring (hourly) |
| `SCHEME_EXPIRY_WARNING_DAYS` | `30` | No | Days before expiry to flag a warning |

---

## Dashboard

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `DASHBOARD_ENABLED` | `true` | No | Master switch for dashboard API |
| `DASHBOARD_SESSION_IDLE_TIMEOUT_SECONDS` | `3600` | No | Dashboard session idle timeout (1 hour) |
| `DASHBOARD_AUTH_PROVIDER` | `disabled` | Must be `disabled` in prod | `disabled` blocks login; `dev` enables local code-based login |
| `DASHBOARD_DEV_LOGIN_ENABLED` | `false` | Must be `false` in prod | Enable dev login. Rejected in staging/production. |
| `DASHBOARD_DEV_LOGIN_CODE` | _(empty)_ | Local only | Shared code for dev login. Never commit or log. |

---

## Rate Limiting

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `RATE_LIMIT_USER_PER_DAY` | `100` | No | Daily limit per authenticated user |
| `RATE_LIMIT_OPERATOR_PER_DAY` | `1000` | No | Daily limit per operator member |
| `RATE_LIMIT_GUEST_PER_DAY` | `50` | No | Daily limit per guest session |

---

## Notifications & Push

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `VAPID_PUBLIC_KEY` | _(empty)_ | If push notifications needed | VAPID public key for Web Push |
| `VAPID_PRIVATE_KEY` | _(empty)_ | If push notifications needed | VAPID private key. Never commit. |
| `SMS_NOTIFICATIONS_ENABLED` | `false` | No | Enable SMS notifications |
| `MSG91_SMS_TEMPLATE_ID` | _(empty)_ | If SMS enabled | MSG91 SMS template ID |

---

## Ingestion

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `MYSCHEME_API_BASE_URL` | _(empty)_ | No | MyScheme public API base URL (demo adapter) |
| `MYSCHEME_API_TOKEN` | _(empty)_ | No | MyScheme API token |
| `MYSCHEME_INGESTION_MODE` | `json_file` | No | `json_file` or `api` |
| `INGESTION_AUTO_PUBLISH` | `false` | No | Auto-publish ingested schemes |

---

## Export

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `EXPORT_STORAGE_PROVIDER` | `local` | No | Where to store bulk export files |
| `EXPORT_MAX_ROWS` | `5000` | No | Maximum rows in a beneficiary export |
| `BULK_ELIGIBILITY_MAX_ROWS` | `500` | No | Maximum rows in a bulk eligibility CSV upload |
| `BULK_ELIGIBILITY_MAX_MB` | `2` | No | Maximum bulk CSV file size |

---

## Local E2E Helpers

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `LOCAL_E2E_HELPERS_ENABLED` | `false` | Must be `false` in prod | Enables seed/session helper endpoints. Rejected in prod. |

---

## Frontend Variables

These go in `frontend/.env.local` (local) or Vercel environment settings (deployed).

| Variable | Default | Required in Prod | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | _(empty)_ | Yes | Backend base URL, e.g. `https://api.adhikarai.in` |
| `NEXT_PUBLIC_ENABLE_DEV_TOOLS` | _(empty)_ | No (omit or `false`) | Set to `true` locally to show dev UI links |
| `NEXT_PUBLIC_SILENCE_MS` | `1500` | No | Silence detection threshold in milliseconds |
| `NEXT_PUBLIC_SILENCE_THRESHOLD` | `0.018` | No | Amplitude threshold for silence detection |

---

## Security Checklist for Production

Before deploying to staging or production, verify:

- [ ] `AUTH_JWT_SECRET` is at least 32 chars and randomised
- [ ] `AUTH_COOKIE_SECURE=true`
- [ ] `DATABASE_URL` and `DATABASE_DIRECT_URL` point to cloud database
- [ ] `REDIS_URL` is `redis://` or `rediss://` (not `memory://`)
- [ ] `ADMIN_API_TOKEN` is changed from `change-me`
- [ ] `CORS_ORIGINS` lists only the Vercel deployment URL
- [ ] `OTP_PROVIDER=msg91` (or `ALLOW_MOCK_OTP_IN_STAGING=true` for staging only)
- [ ] `DASHBOARD_AUTH_PROVIDER=disabled`
- [ ] `DASHBOARD_DEV_LOGIN_ENABLED=false`
- [ ] `LOCAL_E2E_HELPERS_ENABLED=false`
- [ ] `STORE_AUDIO_DEBUG=false`
- [ ] Provider API keys are set in secret manager, not in code
