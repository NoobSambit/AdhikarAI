# Deployment Readiness

AdhikarAI staging and production startup now fail closed for insecure auth, Redis, database, and CORS settings.

## Backend Environment

Required for staging/production:

- `APP_ENV=staging` or `APP_ENV=production`
- `AUTH_JWT_SECRET`: non-default, at least 32 characters
- `AUTH_COOKIE_SECURE=true`
- `AUTH_COOKIE_SAMESITE=none` for cross-site Vercel-to-Render deployments, otherwise `lax` or `strict`
- `AUTH_COOKIE_DOMAIN`: set only when a shared custom parent domain needs it
- `DATABASE_URL` and `DATABASE_DIRECT_URL`: deployed PostgreSQL URLs, not localhost defaults
- `REDIS_URL`: `redis://` or `rediss://`; `memory://` is local/test only
- `ADMIN_API_TOKEN`: non-default
- `CORS_ORIGINS`: explicit frontend origins, never `*`
- `DASHBOARD_AUTH_PROVIDER=disabled`
- `DASHBOARD_DEV_LOGIN_ENABLED=false`
- `LOCAL_E2E_HELPERS_ENABLED=false`
- `OTP_PROVIDER=msg91` in production, with `MSG91_AUTH_KEY` and `MSG91_TEMPLATE_ID`
- `STORE_AUDIO_DEBUG=false` in production

Staging may use `OTP_PROVIDER=mock` only with `ALLOW_MOCK_OTP_IN_STAGING=true`. Production rejects mock OTP.

Provider credentials are validated when their hosted provider is selected:

- Groq chat or voice: `GROQ_API_KEY`
- Hosted AI4Bharat translation: `AI4BHARAT_TRANSLATE_URL` and `AI4BHARAT_API_KEY`
- Google Translate: `GOOGLE_TRANSLATE_API_KEY`
- Google TTS: `GOOGLE_APPLICATION_CREDENTIALS`

## Frontend Environment

- `NEXT_PUBLIC_API_BASE_URL`: FastAPI base URL for the environment
- `NEXT_PUBLIC_ENABLE_DEV_TOOLS=false` in staging/production

Browser auth uses httpOnly cookies and `credentials: "include"`. JWTs must not be stored in localStorage or sessionStorage.

## Dashboard Auth Status

Dashboard `/dashboard/auth/login` currently supports local/dev/test seeded E2E login only. Staging/production must keep dashboard auth disabled until a real staff identity provider is added. With `DASHBOARD_AUTH_PROVIDER=disabled`, login returns `DASHBOARD_AUTH_NOT_CONFIGURED`.
