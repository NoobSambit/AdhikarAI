# Auth and Sessions

AdhikarAI uses two distinct authentication systems: one for beneficiaries (phone OTP) and one for dashboard operators/admins (code-based dev login or future SSO).

---

## Beneficiary Auth — Phone OTP

### How It Works

1. Beneficiary enters their phone number in E.164 format (e.g., `+919876543210`).
2. `POST /auth/send-otp` creates an `OtpChallenge` row with a hashed OTP and returns a `challenge_id`.
3. The OTP is sent via the configured provider (mock locally, MSG91 in production).
4. Beneficiary enters the 6-digit code.
5. `POST /auth/verify-otp` verifies the hash using PBKDF2-SHA256 with the `challenge_id` as salt.
6. On success, a `User` row is created or fetched, and an httpOnly JWT cookie is set.

### OTP Security

- OTPs are 6-digit codes generated with `secrets.randbelow(1_000_000)`.
- The OTP is **never stored in plaintext**. The server stores `hash_otp(otp, challenge_id)` using PBKDF2-SHA256 with 120,000 iterations.
- Verification uses `hmac.compare_digest` to prevent timing attacks.
- Challenges expire after `OTP_EXPIRY_SECONDS` (default 5 minutes).
- Maximum `OTP_MAX_ATTEMPTS` (default 5) attempts per challenge.
- Retry cooldown: `OTP_RETRY_AFTER_SECONDS` (default 30 seconds) between sends.

### JWT Cookie

- The JWT is set as an **httpOnly cookie** named `adhikarai_session` (configurable).
- The cookie is **never accessible from JavaScript** — `document.cookie` cannot read it.
- Cookie flags:
  - `HttpOnly: true` (always)
  - `Secure: true` in staging/production (requires HTTPS)
  - `SameSite: lax` (default; use `none` for cross-site Vercel-to-Render)
  - `Path: /`
  - `Max-Age: AUTH_JWT_TTL_SECONDS` (default 30 days)
- JWT payload: `{sub: user_id, org: organisation_id, iat, exp}`
- JWT signature: HMAC-SHA256 using `AUTH_JWT_SECRET`

### Guest Mode

Before OTP login, the beneficiary can use the app in guest mode. Profile data is stored in IndexedDB. After login, `PATCH /me` with `guest_profile_id` migrates the guest profile to the authenticated user.

---

## OTP Providers

| Provider | Variable | Use case |
|---|---|---|
| `mock` | `OTP_PROVIDER=mock` | Local development — OTP is logged to server stdout, not sent |
| `msg91` | `OTP_PROVIDER=msg91` | Production — requires `MSG91_AUTH_KEY` and `MSG91_TEMPLATE_ID` |

In production, `OTP_PROVIDER=mock` is rejected at startup. In staging, it requires `ALLOW_MOCK_OTP_IN_STAGING=true`.

---

## Dashboard Auth — Operator and Admin Sessions

### Current Status: **Local/Dev Only**

Dashboard login is currently only functional with `DASHBOARD_AUTH_PROVIDER=dev`. This mode is **not suitable for production**. Staging and production must keep `DASHBOARD_AUTH_PROVIDER=disabled`.

### Dev Login Flow (Local Only)

1. The dashboard UI calls `POST /dashboard/auth/login` with `{email, login_code}`.
2. The server checks that:
   - `DASHBOARD_AUTH_PROVIDER=dev`
   - `DASHBOARD_DEV_LOGIN_ENABLED=true`
   - The provided `login_code` matches `DASHBOARD_DEV_LOGIN_CODE` (constant-time compare)
   - An active `OrganisationMember` row exists with the given email
3. On success, a dashboard JWT is set as an httpOnly cookie.
4. Dashboard JWT payload: `{sub: user_id, member_id, org, role, typ: "dashboard", iat, exp}`

### Session Expiry

Dashboard sessions expire after `DASHBOARD_SESSION_IDLE_TIMEOUT_SECONDS` (default 1 hour). The JWT `exp` field is checked on every authenticated request.

### Logout

`POST /dashboard/auth/logout` calls `clear_auth_cookie(response)`, which deletes the session cookie by sending a `Set-Cookie` header with `Max-Age=0`.

---

## require_user Dependency

`app/core/security.py:require_user` is a FastAPI dependency that:

1. Reads the cookie named `AUTH_COOKIE_NAME`.
2. Decodes and verifies the JWT signature.
3. Checks the JWT expiry.
4. Looks up the `User` row by `payload["sub"]`.
5. Checks `user.deleted_at is None`.
6. Returns the `User` ORM model.

Any route that uses `Depends(require_user)` is protected. Unauthenticated requests get `401 NOT_AUTHENTICATED`.

---

## require_dashboard_actor Dependency

`app/core/security.py:require_dashboard_actor` works similarly but:

1. Verifies `payload["typ"] == "dashboard"`.
2. Looks up the `OrganisationMember` row by `payload["member_id"]`.
3. Checks `member.is_active is True`.
4. Returns a `DashboardActor` dataclass with `user_id`, `member_id`, `organisation_id`, `role`, and `display_name`.

Dashboard routes use `Depends(require_dashboard_actor)`.

---

## No JWT in localStorage

**Enforced**: No AdhikarAI code writes JWTs or session tokens to `localStorage` or `sessionStorage`. This was verified by static grep of the frontend codebase. Only `language_code` is stored in `localStorage` (user preference, not a secret).

The frontend's `api.ts` uses `credentials: "include"` in all fetch calls, which automatically sends the httpOnly cookie with each request.

---

## Session Lifetimes

| Session type | TTL | Configurable |
|---|---|---|
| Beneficiary JWT (cookie) | 30 days | `AUTH_JWT_TTL_SECONDS` |
| Dashboard JWT (cookie) | 1 hour | `DASHBOARD_SESSION_IDLE_TIMEOUT_SECONDS` |
| Redis conversation session | 30 days | `SESSION_TTL_SECONDS` |
| OTP challenge | 5 minutes | `OTP_EXPIRY_SECONDS` |

---

## Security Constraints Summary

| Constraint | Status |
|---|---|
| OTP stored as PBKDF2-SHA256 hash | Implemented |
| JWT in httpOnly cookie only | Implemented + static scan verified |
| JWT secret validation at startup | Implemented |
| Cookie `Secure=true` in staging/production | Enforced by config validator |
| Mock OTP blocked in production | Enforced by config validator |
| Dev dashboard login blocked in staging/production | Enforced by config validator |
| OTP attempts limited | Implemented (5 max) |
| OTP retry cooldown | Implemented (30s) |
| Constant-time OTP and login code comparison | Implemented (`hmac.compare_digest`) |
