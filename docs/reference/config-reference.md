# Configuration Reference

All environment variables for the AdhikarAI backend, mapped to the `Settings` class in `app/core/config.py`.

---

## Application

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `APP_ENV` | `app_env` | str | `local` | Yes | `local`, `dev`, `test`, `staging`, `production` |
| `APP_TIMEZONE` | `app_timezone` | str | `Asia/Kolkata` | No | Used by scheduled jobs |
| `FASTAPI_HOST` | `fastapi_host` | str | `0.0.0.0` | No | |
| `FASTAPI_PORT` | `fastapi_port` | int | `8000` | No | |
| `CORS_ORIGINS` | `cors_origins` | str | `http://localhost:3000,...` | Yes | Comma-separated; no `*` in prod; no `localhost` in prod |

---

## Database

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `DATABASE_URL` | `database_url` | str | `postgresql+asyncpg://adhikarai:...@localhost/adhikarai` | Yes | Must not be localhost in staging/prod |
| `DATABASE_DIRECT_URL` | `database_direct_url` | str | same as above | Yes | Direct connection for Neon |
| `DB_POOL_SIZE` | `db_pool_size` | int | `3` | No | |
| `DB_MAX_OVERFLOW` | `db_max_overflow` | int | `2` | No | |
| `DB_POOL_TIMEOUT` | `db_pool_timeout` | int | `10` | No | Seconds |
| `DB_POOL_RECYCLE` | `db_pool_recycle` | int | `300` | No | Seconds |
| `TEST_DATABASE_URL` | `test_database_url` | str | None | No | For tests only |

---

## Redis

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `REDIS_URL` | `redis_url` | str | `redis://localhost:6379/0` | Yes | Must be `redis://` or `rediss://` in staging/prod; `memory://` rejected |
| `SESSION_TTL_SECONDS` | `session_ttl_seconds` | int | `2592000` | No | 30 days |

---

## Auth & Security

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `AUTH_JWT_SECRET` | `auth_jwt_secret` | str | `change-me-phase-4` | Yes | **Must be ≥ 32 chars and non-default in staging/prod** |
| `AUTH_COOKIE_SECURE` | `auth_cookie_secure` | bool | `true` | Yes | Must be `true` in staging/prod |
| `AUTH_COOKIE_NAME` | `auth_cookie_name` | str | `adhikarai_session` | No | |
| `AUTH_COOKIE_SAMESITE` | `auth_cookie_samesite` | str | `lax` | Yes | `lax`, `strict`, or `none` |
| `AUTH_COOKIE_DOMAIN` | `auth_cookie_domain` | str | None | No | Set for shared parent domain |
| `AUTH_JWT_TTL_SECONDS` | `auth_jwt_ttl_seconds` | int | `2592000` | No | 30 days |
| `ADMIN_API_TOKEN` | `admin_api_token` | str | `change-me` | Yes | **Must be non-default in staging/prod** |

---

## OTP

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `OTP_PROVIDER` | `otp_provider` | str | `mock` | Yes | `mock` or `msg91`; `mock` rejected in prod |
| `OTP_EXPIRY_SECONDS` | `otp_expiry_seconds` | int | `300` | No | 5 minutes |
| `OTP_RETRY_AFTER_SECONDS` | `otp_retry_after_seconds` | int | `30` | No | |
| `OTP_MAX_ATTEMPTS` | `otp_max_attempts` | int | `5` | No | |
| `MSG91_BASE_URL` | `msg91_base_url` | str | `https://control.msg91.com/api/v5` | No | |
| `MSG91_AUTH_KEY` | `msg91_auth_key` | str | None | When `msg91` | |
| `MSG91_TEMPLATE_ID` | `msg91_template_id` | str | None | When `msg91` | |
| `ALLOW_MOCK_OTP_IN_STAGING` | `allow_mock_otp_in_staging` | bool | `false` | No | Staging exception |

---

## LLM

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `LLM_PROVIDER` | `llm_provider` | str | `ollama` | No | `ollama` or `groq` |
| `OLLAMA_BASE_URL` | `ollama_base_url` | str | `http://localhost:11434` | No | |
| `OLLAMA_MODEL` | `ollama_model` | str | `llama3.1:8b` | No | |
| `OLLAMA_FALLBACK_MODEL` | `ollama_fallback_model` | str | `qwen2.5:7b` | No | |
| `GROQ_BASE_URL` | `groq_base_url` | str | `https://api.groq.com/openai/v1` | No | |
| `GROQ_API_KEY` | `groq_api_key` | str | None | When Groq | **Required when LLM or voice uses Groq** |
| `GROQ_CHAT_MODEL` | `groq_chat_model` | str | `llama-3.3-70b-versatile` | No | |
| `GROQ_FALLBACK_MODEL` | `groq_fallback_model` | str | `llama-3.1-8b-instant` | No | |
| `AGENT_TEMPERATURE` | `agent_temperature` | float | `0.1` | No | |
| `AGENT_MAX_TOKENS` | `agent_max_tokens` | int | `512` | No | |
| `AGENT_JSON_REPAIR_RETRIES` | `agent_json_repair_retries` | int | `1` | No | |
| `AGENT_MAX_QUESTIONS_BEFORE_RESULT` | `agent_max_questions_before_result` | int | `8` | No | |
| `AGENT_TIMEOUT_SECONDS` | `agent_timeout_seconds` | int | `20` | No | |

---

## Voice / ASR

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `VOICE_PROVIDER` | `voice_provider` | str | `local` | No | `local` or `groq` |
| `ASR_MIN_CONFIDENCE` | `asr_min_confidence` | float | `0.70` | No | Below this → low-confidence block |
| `VOICE_MAX_UTTERANCE_SECONDS` | `voice_max_utterance_seconds` | int | `20` | No | |
| `VOICE_MAX_UPLOAD_MB` | `voice_max_upload_mb` | int | `8` | No | |
| `BROWSER_ASR_FALLBACK_AFTER_MS` | `browser_asr_fallback_after_ms` | int | `2000` | No | |
| `GROQ_WHISPER_MODEL` | `groq_whisper_model` | str | `whisper-large-v3-turbo` | No | |
| `WHISPER_CPP_BINARY` | `whisper_cpp_binary` | str | `/opt/whisper.cpp/...` | No | Local binary path |
| `WHISPER_CPP_MODEL_PATH` | `whisper_cpp_model_path` | str | `/models/ggml-large-v3.bin` | No | |
| `ASR_TIMEOUT_SECONDS` | `asr_timeout_seconds` | int | `12` | No | |
| `STORE_AUDIO_DEBUG` | `store_audio_debug` | bool | `false` | Yes | Must be `false` in prod |

---

## Translation

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `TRANSLATION_PROVIDER` | `translation_provider` | str | `local_indictrans2` | No | `local_indictrans2`, `ai4bharat_hosted`, `google` |
| `TRANSLATION_SERVICE_URL` | `translation_service_url` | str | `http://localhost:8001` | No | For local IndicTrans2 |
| `AI4BHARAT_TRANSLATE_URL` | `ai4bharat_translate_url` | str | None | When `ai4bharat_hosted` | |
| `AI4BHARAT_API_KEY` | `ai4bharat_api_key` | str | None | When `ai4bharat_hosted` | |
| `GOOGLE_TRANSLATE_API_KEY` | `google_translate_api_key` | str | None | When `google` | |
| `TRANSLATION_CACHE_TTL_SECONDS` | `translation_cache_ttl_seconds` | int | `604800` | No | 7 days |

---

## TTS

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `TTS_PROVIDER` | `tts_provider` | str | `local_indictts` | No | `local_indictts` or `google` |
| `LOCAL_TTS_URL` | `local_tts_url` | str | `http://localhost:8002` | No | |
| `GOOGLE_TTS_URL` | `google_tts_url` | str | Google default | No | |
| `GOOGLE_APPLICATION_CREDENTIALS` | `google_application_credentials` | str | None | When `google` | Service account JSON path |
| `TTS_CACHE_TTL_SECONDS` | `tts_cache_ttl_seconds` | int | `86400` | No | 24 hours |

---

## Embeddings / Search

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `ELIGIBILITY_ENGINE` | `eligibility_engine` | str | `experta` | No | |
| `EMBEDDING_PROVIDER` | `embedding_provider` | str | `sentence_transformers` | No | |
| `EMBEDDING_MODEL` | `embedding_model` | str | `intfloat/multilingual-e5-small` | No | |
| `FAISS_INDEX_DIR` | `faiss_index_dir` | str | `./data/faiss` | No | |
| `ENABLE_SCHEDULER` | `enable_scheduler` | bool | `true` | No | |
| `EXPIRY_CHECK_CRON` | `expiry_check_cron` | str | `0 2 * * *` | No | |

---

## Dashboard

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `DASHBOARD_ENABLED` | `dashboard_enabled` | bool | `true` | No | |
| `DASHBOARD_SESSION_IDLE_TIMEOUT_SECONDS` | `dashboard_session_idle_timeout_seconds` | int | `3600` | No | 1 hour |
| `DASHBOARD_AUTH_PROVIDER` | `dashboard_auth_provider` | str | `disabled` | Yes | Must be `disabled` in prod |
| `DASHBOARD_DEV_LOGIN_ENABLED` | `dashboard_dev_login_enabled` | bool | `false` | Yes | Must be `false` in prod |
| `DASHBOARD_DEV_LOGIN_CODE` | `dashboard_dev_login_code` | str | `` | No | |
| `LOCAL_E2E_HELPERS_ENABLED` | `local_e2e_helpers_enabled` | bool | `false` | Yes | Must be `false` in prod |

---

## Rate Limiting

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `RATE_LIMIT_USER_PER_DAY` | `rate_limit_user_per_day` | int | `100` | No | |
| `RATE_LIMIT_OPERATOR_PER_DAY` | `rate_limit_operator_per_day` | int | `1000` | No | |
| `RATE_LIMIT_GUEST_PER_DAY` | `rate_limit_guest_per_day` | int | `50` | No | |

---

## Bulk / Export

| Variable | Settings Field | Type | Default | Required In Prod | Notes |
|---|---|---|---|---|---|
| `EXPORT_STORAGE_PROVIDER` | `export_storage_provider` | str | `local` | No | |
| `EXPORT_MAX_ROWS` | `export_max_rows` | int | `5000` | No | |
| `BULK_ELIGIBILITY_MAX_ROWS` | `bulk_eligibility_max_rows` | int | `500` | No | |
| `BULK_ELIGIBILITY_MAX_MB` | `bulk_eligibility_max_mb` | int | `2` | No | |

---

## Frontend Environment

| Variable | Default | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend URL |
| `NEXT_PUBLIC_ENABLE_DEV_TOOLS` | `true` (local) | Gate for `/dev-chat`, `/dev-voice` |
