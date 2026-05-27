# Security & Privacy

Security and privacy design for AdhikarAI, a platform handling sensitive government benefit data for vulnerable populations.

---

## Non-Negotiable Rules

These are enforced at the code level and must never be relaxed:

| Rule | Enforcement |
|---|---|
| **Never store Aadhaar numbers** | `services/phase4.py` guards reject payloads containing 12-digit Aadhaar patterns. `agent/extraction.py` has a sensitive field guard. Tested in `test_phase4_logic.py`. |
| **Never store raw documents** | Only document metadata and masked identifiers are stored. `VerifiedDocument` table stores document type, provider status, and masked ID — not raw files. |
| **JWT never in localStorage** | httpOnly cookies only. Enforced by `test_phase4_security.py` (unit) and `beneficiary-pwa.spec.ts` (E2E: scans localStorage after login). |
| **Production rejects insecure defaults** | `Settings.model_validator` raises `ValueError` at startup for: default secrets, `AUTH_COOKIE_SECURE=false`, localhost DB, `memory://` Redis, mock OTP, dev dashboard login. |
| **Multi-tenancy enforced** | Every tenant-scoped query filters by `organisation_id`. Tested in `test_phase5_rbac.py`. |

---

## Authentication

### Beneficiary Auth (Phone OTP)

1. `POST /auth/send-otp` → creates `OtpChallenge` row with **PBKDF2-hashed** OTP (120k iterations)
2. OTP sent via provider (mock in dev, MSG91 in production)
3. `POST /auth/verify-otp` → verifies hash, issues JWT in **httpOnly** cookie
4. Cookie settings: `httponly=true`, `secure` from env, `samesite` from env, `path=/`

OTP protections:
- Max 5 verification attempts per challenge
- 5-minute expiry
- 30-second retry cooldown
- Rate limiting via `RATE_LIMIT_GUEST_PER_DAY` (default 50)

### Dashboard Auth

1. `POST /dashboard/auth/login` → validates dev code against `DASHBOARD_DEV_LOGIN_CODE`
2. Issues dashboard JWT in **same httpOnly cookie** (distinguished by `typ: "dashboard"`)
3. JWT includes `member_id`, `org`, `role` — never trusted from request body
4. Dashboard session idle timeout: 1 hour (configurable)

**Current limitation:** Only dev code login exists. Production must keep `DASHBOARD_AUTH_PROVIDER=disabled` until a real staff identity provider (SSO/SAML) is added.

---

## JWT Structure

### Beneficiary JWT

```json
{
  "sub": "<user_id>",
  "org": "<organisation_id>",
  "iat": 1716800000,
  "exp": 1716803600
}
```

### Dashboard JWT

```json
{
  "sub": "<user_id>",
  "member_id": "<member_id>",
  "org": "<organisation_id>",
  "role": "operator",
  "typ": "dashboard",
  "iat": 1716800000,
  "exp": 1716803600
}
```

Both signed with HMAC-SHA256 using `AUTH_JWT_SECRET`. The `typ: "dashboard"` field distinguishes dashboard from beneficiary sessions.

---

## Cookie Security

| Setting | Local Default | Staging/Production |
|---|---|---|
| `AUTH_COOKIE_SECURE` | `false` (HTTP) | `true` (HTTPS required) |
| `AUTH_COOKIE_SAMESITE` | `lax` | `none` (for Vercel→Render cross-site) or `lax` |
| `AUTH_COOKIE_DOMAIN` | unset | set if shared custom parent domain |
| `httponly` | always `true` | always `true` |
| `path` | `/` | `/` |

Startup validation rejects `samesite=none` + `secure=false` (invalid per spec).

---

## CORS

- Explicit origins from `CORS_ORIGINS` env var (comma-separated)
- Wildcard (`*`) rejected in staging/production
- `localhost` rejected in production CORS origins
- `credentials: true` enabled for cookie transmission

---

## Rate Limiting

Redis-backed daily counters with midnight UTC reset:

| Actor Type | Daily Limit | Error Code |
|---|---|---|
| Guest (by session_id) | 50 | `RATE_LIMIT_EXCEEDED` |
| Authenticated user | 100 | `RATE_LIMIT_EXCEEDED` |
| Dashboard operator | 1,000 | `RATE_LIMIT_EXCEEDED` |

Response includes `retry_after_seconds` and `retry_at` ISO timestamp.

---

## RBAC & Access Control

See [RBAC and Tenancy](rbac-and-tenancy.md) for full details.

Key enforcement points:
- `assert_beneficiary_access()` — operators can only access assigned beneficiaries
- `assert_organisation_scope()` — NGO admins can only access their organisation
- `require_actor_permission()` — permission-based action gating
- Super admins bypass scope checks

---

## Data Privacy

### What Is NOT Stored

- Aadhaar numbers (hard guard + test coverage)
- Raw government documents (only metadata)
- Raw audio files (only voice turn metrics)
- OTP plaintext (only PBKDF2 hash)
- Access tokens for external services in user tables

### What IS Stored (with precautions)

| Data | Precaution |
|---|---|
| Phone numbers | E.164 format, used for auth only |
| Profile demographics | Used for eligibility matching only |
| Conversation transcripts | Text only, no audio |
| Document verification metadata | Masked identifiers (e.g., doc type + status) |
| OTP challenges | Hashed with PBKDF2 (120k iterations), 5-min TTL |

### DigiLocker / Aadhaar Sandbox

The DigiLocker and Aadhaar prefill endpoints are **sandbox/demo stubs only**:
- No real UIDAI or DigiLocker integration
- No real government credentials
- Sandbox responses return fixed test data
- Aadhaar number guard prevents any Aadhaar storage even in demo mode

---

## Request ID Tracking

Every HTTP request receives an `X-Request-ID` (from request header or auto-generated UUID). This ID is:
- Stored in `request.state.request_id`
- Returned in response header `X-Request-ID`
- Included in all error response JSON bodies

---

## Admin Token Security

Admin API routes (scheme CRUD, ingestion) use a shared `X-Admin-Token` header, validated against `ADMIN_API_TOKEN` env var. The default value `change-me` is rejected in staging/production.

---

## Dev-Only Features

| Feature | Gate | Blocked In Production |
|---|---|---|
| Dashboard dev login | `DASHBOARD_DEV_LOGIN_ENABLED` + `DASHBOARD_AUTH_PROVIDER=dev` | ✅ |
| Local E2E helpers | `LOCAL_E2E_HELPERS_ENABLED` | ✅ |
| Mock OTP provider | `OTP_PROVIDER=mock` | ✅ (staging requires explicit opt-in) |
| Audio debug storage | `STORE_AUDIO_DEBUG` | ✅ |
| Dev chat/voice UI | `NEXT_PUBLIC_ENABLE_DEV_TOOLS` | Frontend-gated |

---

## Secrets Management

- All secrets are loaded from environment variables, never hardcoded
- `.env.example` contains safe defaults for local development
- `.gitignore` excludes `.env` files
- Startup validator rejects default/weak secrets in staging/production
- No secrets appear in error responses, logs, or test fixtures
