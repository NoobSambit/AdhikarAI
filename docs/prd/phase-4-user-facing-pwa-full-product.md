# AdhikarAI PRD - Phase 4: User-Facing PWA and Full Product

## Phase Summary

Phase 4 builds the production end-user PWA for rural Indian beneficiaries. It combines the Phase 1 eligibility engine, Phase 2 agent, and Phase 3 voice pipeline into an installable, offline-capable, voice-first Android-friendly product.

The PWA supports guest eligibility checks, phone OTP login, saved schemes, document checklists, substitute document guidance, DigiLocker document verification, optional Aadhaar-based profile pre-fill in sandbox/demo mode, application status tracking, proactive eligibility alerts, reminder notifications, shareable action plans, accessibility settings, profile management, and session history.

Primary user: rural Indian beneficiary who may have very low literacy, speaks a regional language, and uses a basic Android phone on 2G/3G.

Secondary user in this phase: a family member helping the primary user on the same device.

Key product rule: the first screen is the usable voice-first home, not a marketing landing page.

## Goals and Success Criteria

1. Ship an installable Android-friendly PWA.
   - Success: Lighthouse PWA checks pass for manifest, service worker, offline start URL, and installability.
   - Success: app loads core shell under 3 seconds on simulated Slow 3G after first install.

2. Make voice the primary CTA.
   - Success: home screen has one large microphone button as the main action.
   - Success: all important error states include a "Tap to speak your problem" fallback.

3. Support guest mode.
   - Success: guest user can complete eligibility flow and view results without login.
   - Success: guest profile is stored in localStorage/IndexedDB and migrates to DB after OTP login.

4. Support authenticated features.
   - Success: logged-in users can save schemes, persist checklists, track application statuses, receive notifications, and verify documents.

5. Provide actionable scheme results.
   - Success: each scheme card includes benefit explanation, amount, eligibility status, checklist, substitute guidance, application steps, and apply link.
   - Success: mandatory checklist completion activates "Ready to apply".

6. Work on low-end Android and 2G/3G.
   - Success: initial JS bundle for home route stays under 180 KB gzip excluding framework baseline where feasible.
   - Success: images are avoided unless necessary; icons use inline/lucide or local SVG sprite.
   - Success: offline cached schemes and profile remain usable with no network.

7. Respect sensitive identity flows.
   - Success: DigiLocker and Aadhaar pre-fill are user-initiated, optional, and never block eligibility matching.
   - Success: Aadhaar number is not stored.

## User Stories

1. Guest voice eligibility check
   - User opens app, selects Hindi, taps mic, explains situation.
   - Agent asks clarifying voice questions.
   - User sees matched schemes without logging in.
   - Guest limitation: save/bookmark buttons show login prompt.

2. Low-literacy result review
   - User sees a scheme card with icon, green eligible label, amount badge, and short plain-language benefit.
   - User taps play to hear the card summary.

3. Near-miss review
   - User has income above a scheme limit.
   - Near-miss card appears below matches and says exactly which criterion failed and what would be needed.

4. Document checklist
   - User taps Aadhaar checkbox and bank passbook checkbox.
   - Checklist persists offline.
   - If all mandatory docs are checked, "Ready to apply" activates.

5. Missing document substitute
   - User lacks income certificate.
   - UI shows accepted substitutes and how to obtain original from tehsil/e-district office.

6. Save scheme
   - Authenticated user taps bookmark.
   - Scheme appears in "My schemes" tab and reminder is scheduled for 7 days.
   - Guest user taps bookmark and sees "Login with phone to save this scheme."

7. DigiLocker verify
   - User taps "Verify with DigiLocker."
   - OAuth opens.
   - On return, verified docs are marked confirmed.
   - If DigiLocker fails, manual checklist remains available.

8. Application status tracker
   - User marks scheme as submitted.
   - If status remains submitted for > 14 days, push reminder asks user to update.

9. Offline action
   - User checks documents while offline.
   - Action is added to sync queue.
   - When online returns, queue syncs and UI shows "Saved online."

10. Delete account
   - User opens profile, taps delete account, confirms.
   - Personal profile, saved schemes, checklists, sessions, and notification tokens are deleted or anonymized.

## Functional Requirements

1. Frontend must use Next.js 15 App Router and TypeScript.
2. PWA must include `manifest.json`, service worker, offline fallback page, and install prompt handling.
3. Service worker must use Workbox or a small custom service worker; choice must be documented in code.
4. IndexedDB must store cached schemes, guest profile, conversation history, saved local checklist state, and sync queue.
5. Use `idb` library for IndexedDB access.
6. Home route `/` must render the actual voice-first product.
7. Home screen must show language selector pill at top, large microphone button, and bottom icon navigation.
8. Navigation must use icons plus short labels, never text-only.
9. Supported tabs: Home, My Schemes, History, Profile.
10. Scheme result cards must have max 8 px border radius.
11. Scheme result card must show benefit name, plain-language description, benefit amount badge, eligibility status, checklist, application steps accordion, and apply link.
12. Benefit descriptions must be concrete, e.g. "You get INR 6,000 per year directly in your bank account."
13. Near-miss cards must be in a separate section below matched schemes.
14. Near-miss card must show one failed criterion and one how-to-qualify explanation.
15. Bookmark icon must appear on every scheme card.
16. Saved schemes must persist to DB for authenticated users and IndexedDB for guests until login.
17. Guest users cannot save schemes permanently, track status, verify with DigiLocker, or receive notifications.
18. Guest attempts for restricted features must open phone login sheet.
19. Login must use MSG91 phone OTP.
20. `POST /auth/send-otp` sends OTP and returns masked phone plus retry time.
21. `POST /auth/verify-otp` verifies OTP and sets JWT in httpOnly secure cookie.
22. JWT must not be stored in localStorage.
23. On login, guest profile and local actions must migrate to the authenticated profile.
24. Migration must be idempotent using `guest_profile_id`.
25. Document checklist state must persist per user/profile/scheme.
26. Each checklist item states: not gathered, gathered, verified, or rejected.
27. "Ready to apply" activates only when all mandatory documents are gathered or verified.
28. Substitute guidance must be inline under missing mandatory documents.
29. DigiLocker OAuth must be user initiated through a button.
30. DigiLocker integration must store document metadata and verification status, not raw document files unless user explicitly downloads/uploads later.
31. Aadhaar pre-fill must be optional and user initiated.
32. Aadhaar number must never be stored in DB, logs, Redis, IndexedDB, or analytics.
33. UIDAI sandbox flow may pre-fill name, DOB, gender, address, and state only.
34. Application status values must be exactly: `not_started`, `documents_gathering`, `submitted`, `pending`, `approved`, `rejected`.
35. Status changes must be stored with timestamp and source.
36. Push notification reminders must be opt-in.
37. Saving a scheme schedules a reminder for 7 days later.
38. Submitted status older than 14 days schedules reminder to update status.
39. Proactive eligibility alerts must run when a new scheme is published.
40. Shareable action plan must generate PDF or WhatsApp-shareable image server-side.
41. Action plan must include matched schemes, documents, substitute options, and application steps.
42. High-contrast mode and font size settings must persist in profile and localStorage.
43. Font sizes: default, large, extra-large.
44. Profile management screen must allow view/edit profile fields and household members.
45. User must be able to delete account.
46. Session history must list past conversations with date, language, and matched scheme count.
47. Tap a history item to re-open it.
48. All error messages must include short text and a voice retry button.
49. Color status: green eligible, amber near-miss, red ineligible/error.
50. The app must not use decorative heavy images or animations that hurt low-end performance.
51. Offline mode must show cached scheme data and local profile.
52. Offline actions must queue with action type, payload, created_at, retry_count, and idempotency_key.
53. Sync queue must retry with exponential backoff up to 5 attempts.
54. Conflict resolution: server updated_at wins for profile fields unless local action is newer and field-level merge is possible.
55. Accessibility: all interactive controls must have accessible names, 44 px minimum touch target, visible focus, and color contrast >= WCAG AA.

## Data Models

Phase 4 depends on Phases 1-3 tables. New tables are additive.

### SQL DDL

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    phone_e164 TEXT NOT NULL,
    phone_verified_at TIMESTAMPTZ,
    primary_profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    language_code TEXT NOT NULL DEFAULT 'hi',
    high_contrast_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    font_size TEXT NOT NULL DEFAULT 'default' CHECK (font_size IN ('default', 'large', 'extra_large')),
    notification_opt_in BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, phone_e164)
);

CREATE TABLE otp_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    phone_e164 TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'msg91',
    provider_request_id TEXT,
    status TEXT NOT NULL CHECK (status IN ('sent', 'verified', 'expired', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE saved_schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    scheme_id TEXT NOT NULL REFERENCES schemes(id),
    saved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reminder_scheduled_at TIMESTAMPTZ,
    UNIQUE (organisation_id, user_id, profile_id, scheme_id)
);

CREATE TABLE document_checklist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    scheme_id TEXT NOT NULL REFERENCES schemes(id),
    document_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_gathered' CHECK (status IN ('not_gathered', 'gathered', 'verified', 'rejected')),
    source TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'digilocker', 'migration')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, profile_id, scheme_id, document_name)
);

CREATE TABLE digilocker_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    digilocker_user_id TEXT,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('connected', 'revoked', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE verified_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    source TEXT NOT NULL CHECK (source IN ('digilocker', 'uidai_sandbox')),
    document_type TEXT NOT NULL,
    issuer TEXT,
    document_uri TEXT,
    masked_identifier TEXT,
    verification_status TEXT NOT NULL CHECK (verification_status IN ('verified', 'failed', 'revoked')),
    verified_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE application_statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    scheme_id TEXT NOT NULL REFERENCES schemes(id),
    status TEXT NOT NULL CHECK (status IN ('not_started', 'documents_gathering', 'submitted', 'pending', 'approved', 'rejected')),
    notes TEXT,
    source TEXT NOT NULL DEFAULT 'user' CHECK (source IN ('user', 'operator', 'system')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, user_id, profile_id, scheme_id)
);

CREATE TABLE application_status_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    application_status_id UUID NOT NULL REFERENCES application_statuses(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    source TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    user_agent TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, endpoint)
);

CREATE TABLE notification_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'sent', 'failed', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE shareable_action_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    conversation_session_id UUID REFERENCES conversation_sessions(id) ON DELETE SET NULL,
    format TEXT NOT NULL CHECK (format IN ('pdf', 'image')),
    storage_provider TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE offline_sync_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    idempotency_key TEXT NOT NULL,
    action_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('received', 'applied', 'duplicate', 'failed')),
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, idempotency_key)
);
```

### Python SQLAlchemy Models

```python
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("organisation_id", "phone_e164"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    phone_e164: Mapped[str] = mapped_column(Text, nullable=False)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    primary_profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="hi")
    high_contrast_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    font_size: Mapped[str] = mapped_column(Text, nullable=False, default="default")
    notification_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SavedScheme(Base):
    __tablename__ = "saved_schemes"
    __table_args__ = (UniqueConstraint("organisation_id", "user_id", "profile_id", "scheme_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id"), nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reminder_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentChecklistItem(Base):
    __tablename__ = "document_checklist_items"
    __table_args__ = (UniqueConstraint("organisation_id", "profile_id", "scheme_id", "document_name"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id"), nullable=False)
    document_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="not_gathered")
    source: Mapped[str] = mapped_column(Text, nullable=False, default="manual")
    metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ApplicationStatus(Base):
    __tablename__ = "application_statuses"
    __table_args__ = (UniqueConstraint("organisation_id", "user_id", "profile_id", "scheme_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    scheme_id: Mapped[str] = mapped_column(Text, ForeignKey("schemes.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    __table_args__ = (UniqueConstraint("organisation_id", "endpoint"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

## API Specification

### Shared TypeScript Types

```ts
export interface SendOtpRequest {
  organisation_id: string;
  phone_e164: string;
}

export interface SendOtpResponse {
  challenge_id: string;
  masked_phone: string;
  retry_after_seconds: number;
}

export interface VerifyOtpRequest {
  organisation_id: string;
  challenge_id: string;
  otp: string;
  guest_profile_id?: string;
}

export interface AuthUser {
  id: string;
  phone_e164: string;
  language_code: LanguageCode;
  primary_profile_id?: string;
}

export interface SchemeCardView {
  scheme_id: string;
  name: string;
  plain_language_benefit: string;
  benefit_amount: string;
  eligibility_status: "eligible" | "near_miss" | "ineligible";
  failed_criterion?: string;
  how_to_qualify?: string;
  documents: ChecklistItemView[];
  application_steps: string[];
  application_url?: string;
  saved: boolean;
}

export interface ChecklistItemView {
  document_name: string;
  is_mandatory: boolean;
  status: "not_gathered" | "gathered" | "verified" | "rejected";
  accepted_substitutes: DocumentSubstitute[];
}

export interface UpdateChecklistRequest {
  profile_id: string;
  scheme_id: string;
  document_name: string;
  status: "not_gathered" | "gathered";
  idempotency_key: string;
}

export interface UpdateApplicationStatusRequest {
  profile_id: string;
  scheme_id: string;
  status: "not_started" | "documents_gathering" | "submitted" | "pending" | "approved" | "rejected";
  notes?: string;
}
```

### Shared Pydantic Models

```python
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SendOtpRequest(BaseModel):
    organisation_id: UUID
    phone_e164: str = Field(pattern=r"^\+[1-9]\d{7,14}$")


class SendOtpResponse(BaseModel):
    challenge_id: UUID
    masked_phone: str
    retry_after_seconds: int


class VerifyOtpRequest(BaseModel):
    organisation_id: UUID
    challenge_id: UUID
    otp: str = Field(min_length=4, max_length=8)
    guest_profile_id: str | None = None


class AuthUserModel(BaseModel):
    id: UUID
    phone_e164: str
    language_code: str
    primary_profile_id: UUID | None = None


class UpdateChecklistRequest(BaseModel):
    profile_id: UUID
    scheme_id: str
    document_name: str
    status: Literal["not_gathered", "gathered"]
    idempotency_key: str


class UpdateApplicationStatusRequest(BaseModel):
    profile_id: UUID
    scheme_id: str
    status: Literal["not_started", "documents_gathering", "submitted", "pending", "approved", "rejected"]
    notes: str | None = Field(default=None, max_length=500)


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict[str, str]


class ActionPlanRequest(BaseModel):
    profile_id: UUID
    conversation_session_id: UUID | None = None
    scheme_ids: list[str]
    format: Literal["pdf", "image"] = "pdf"
```

### POST /auth/send-otp

Request:

```json
{
  "organisation_id": "00000000-0000-0000-0000-000000000001",
  "phone_e164": "+919876543210"
}
```

Response:

```json
{
  "challenge_id": "2500e6f7-3ef7-47dd-9ec3-a08908900001",
  "masked_phone": "+91******3210",
  "retry_after_seconds": 30
}
```

Errors:

| Status | Code | Exact behavior |
|---|---|---|
| 400 | INVALID_PHONE | Show "Enter a valid mobile number." |
| 429 | OTP_RATE_LIMITED | Show "Too many OTP requests. Try again after 10 minutes." |
| 502 | OTP_PROVIDER_FAILED | Show "OTP could not be sent. Try again." |

### POST /auth/verify-otp

Response sets cookie:

```txt
Set-Cookie: adhikarai_session=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=2592000
```

Response:

```json
{
  "user": {
    "id": "e77ad652-8180-4572-ad35-096888900001",
    "phone_e164": "+919876543210",
    "language_code": "hi",
    "primary_profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777"
  },
  "migrated_guest_profile": true
}
```

### GET /me

Returns authenticated user and primary profile. If not logged in, returns `401 NOT_AUTHENTICATED`.

### POST /saved-schemes

Authenticated only.

Request:

```json
{
  "profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
  "scheme_id": "pm_kisan"
}
```

Response:

```json
{
  "saved": true,
  "reminder_scheduled_at": "2026-05-15T09:00:00+05:30"
}
```

### DELETE /saved-schemes/{scheme_id}

Authenticated only. Query: `profile_id`.

Behavior: delete saved scheme and cancel unsent saved-scheme reminder.

### PATCH /checklists

Request:

```json
{
  "profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
  "scheme_id": "pm_kisan",
  "document_name": "Aadhaar",
  "status": "gathered",
  "idempotency_key": "offline_01JABC"
}
```

Response:

```json
{
  "document_name": "Aadhaar",
  "status": "gathered",
  "ready_to_apply": false
}
```

### POST /digilocker/start

Authenticated only.

Request:

```json
{
  "profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
  "return_path": "/schemes/pm_kisan"
}
```

Response:

```json
{
  "authorization_url": "https://betaapi.digitallocker.gov.in/public/oauth2/1/authorize?response_type=code&client_id=...",
  "state": "dl_01JABC"
}
```

### GET /digilocker/callback

Query: `code`, `state`.

Behavior:

1. Exchange authorization code for token.
2. Fetch available document metadata.
3. Match known document types to checklist items.
4. Mark matched documents `verified`.
5. Redirect to original return path with `digilocker=success`.

Error behavior:

- Redirect with `digilocker=failed`.
- UI shows "DigiLocker verification failed. You can still mark documents manually."

### POST /aadhaar/prefill/start

Authenticated only. Sandbox/demo only unless production compliance is completed.

Response:

```json
{
  "authorization_url": "https://uidai-sandbox.example/authorize?state=uid_01JABC",
  "state": "uid_01JABC"
}
```

If UIDAI sandbox config missing, return `501 AADHAAR_PREFILL_NOT_CONFIGURED`.

### PATCH /application-status

Request:

```json
{
  "profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
  "scheme_id": "pm_kisan",
  "status": "submitted",
  "notes": "Submitted at CSC on Monday."
}
```

Response:

```json
{
  "status": "submitted",
  "updated_at": "2026-05-08T12:10:00+05:30",
  "next_reminder_at": "2026-05-22T09:00:00+05:30"
}
```

### POST /notifications/subscribe

Stores Web Push subscription.

### POST /action-plans

Request:

```json
{
  "profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
  "conversation_session_id": "7c036313-8f4a-4c5d-b00f-1e6b7bd00001",
  "scheme_ids": ["pm_kisan", "pmfby"],
  "format": "pdf"
}
```

Response:

```json
{
  "action_plan_id": "4ec7359e-fb20-46dc-a4b0-ec6300400001",
  "url": "https://res.cloudinary.com/adhikarai/action-plans/plan.pdf",
  "expires_at": "2026-06-07T12:00:00+05:30"
}
```

### POST /offline-sync

Authenticated only. Accepts queued offline actions.

Request:

```json
{
  "actions": [
    {
      "idempotency_key": "offline_01JABC",
      "action_type": "checklist.update",
      "payload": {
        "profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
        "scheme_id": "pm_kisan",
        "document_name": "Aadhaar",
        "status": "gathered"
      }
    }
  ]
}
```

Response:

```json
{
  "results": [
    {
      "idempotency_key": "offline_01JABC",
      "status": "applied"
    }
  ]
}
```

### DELETE /me

Deletes account.

Response:

```json
{
  "deleted": true
}
```

Behavior: set `users.deleted_at`, delete push subscriptions, delete saved schemes, delete checklist items, anonymize conversation messages by replacing content with `[deleted]`, keep aggregate analytics.

## Architecture and Implementation Approach

### Frontend Build Plan

1. Add Next.js 15 App Router routes:
   - `/`
   - `/schemes/[id]`
   - `/my-schemes`
   - `/history`
   - `/profile`
   - `/settings`
2. Add PWA manifest and service worker.
3. Add IndexedDB stores:

```ts
interface AdhikarDbSchema {
  schemes: { key: string; value: CachedScheme };
  guestProfile: { key: string; value: GuestProfile };
  conversations: { key: string; value: CachedConversation };
  checklists: { key: string; value: ChecklistItemView };
  syncQueue: { key: string; value: OfflineAction };
  settings: { key: string; value: unknown };
}
```

4. Build voice-first home using Phase 3 `AudioRecorder`.
5. Render scheme cards from Phase 1/2 match payload.
6. Add auth bottom sheet for restricted actions.
7. Add sync queue processor triggered on `online`, app start, and after login.

### Backend Build Plan

1. Add auth module:

```python
async def send_otp(request: SendOtpRequest) -> SendOtpResponse: ...
async def verify_otp(request: VerifyOtpRequest, response: Response) -> VerifyOtpResponse: ...
async def get_current_user(request: Request) -> User: ...
```

2. Add MSG91 provider:

```python
class OtpProvider(Protocol):
    async def send_otp(self, phone_e164: str) -> OtpSendResult: ...
    async def verify_otp(self, provider_request_id: str, otp: str) -> bool: ...
```

3. Add saved schemes/checklist/status routes.
4. Add notification scheduler with APScheduler initially; queue abstraction allows Celery/RQ later.
5. Add DigiLocker OAuth client.
6. Add action plan generator using server-side HTML to PDF.

Recommended PDF library: Playwright Chromium on Render may be heavy. Prefer `weasyprint` if system dependencies are available; otherwise generate a WhatsApp-shareable PNG with `Pillow` and a simple PDF with `reportlab`.

### UI States

Home:

```txt
idle -> recording -> uploading -> thinking -> speaking -> results
idle -> offline -> local_results
recording -> low_confidence -> idle
uploading -> network_error -> browser_asr_or_type
```

Checklist:

```txt
not_gathered -> gathered -> verified
verified -> rejected only from verification provider
gathered -> not_gathered allowed manually
```

Application status:

```txt
not_started -> documents_gathering -> submitted -> pending -> approved
submitted -> rejected
pending -> rejected
rejected -> documents_gathering allowed when user retries
```

### DigiLocker Flow

Use env-configured endpoints:

```txt
DIGILOCKER_BASE_URL=https://betaapi.digitallocker.gov.in/public
DIGILOCKER_AUTHORIZE_PATH=/oauth2/1/authorize
DIGILOCKER_TOKEN_PATH=/oauth2/1/token
DIGILOCKER_FILES_PATH=/oauth2/2/files/issued
```

If production partner credentials differ, only env vars change.

### Proactive Eligibility Alerts

When scheme status changes to active:

```python
async def run_proactive_match_for_scheme(scheme_id: str, organisation_id: UUID) -> None:
    profiles = await load_profiles_with_notification_opt_in(organisation_id)
    for profile in profiles:
        result = eligibility_engine.evaluate_scheme(profile, scheme)
        if result.is_match:
            await schedule_notification(
                user_id=profile.user_id,
                title="A new scheme matches your profile",
                body=f"{scheme.name} may help you. Tap to see details.",
                payload={"scheme_id": scheme_id},
            )
```

## Environment-Specific Implementation Notes

| Component | Local / GPU production | Hosted demo / free tier |
|---|---|---|
| Frontend | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` | Vercel `NEXT_PUBLIC_API_BASE_URL=https://adhikarai-api.onrender.com` |
| Backend | local FastAPI | Render |
| DB | local Postgres | Neon |
| Redis | local Redis | Upstash |
| ASR/LLM/Translation/TTS | Phase 3 local providers | Groq + AI4Bharat hosted + Google TTS |
| OTP | `OTP_PROVIDER=mock` for local unless MSG91 key set | `OTP_PROVIDER=msg91` |
| MSG91 send | `MSG91_SEND_OTP_URL=https://control.msg91.com/api/v5/otp` | same |
| MSG91 verify | `MSG91_VERIFY_OTP_URL=https://control.msg91.com/api/v5/otp/verify` | same |
| File storage | `STORAGE_PROVIDER=supabase` or local dev | `STORAGE_PROVIDER=cloudinary` |
| Cloudinary | optional | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` |
| DigiLocker | sandbox/beta credentials | beta credentials if approved |
| Aadhaar | `UIDAI_SANDBOX_ENABLED=true` with sandbox base URL | `UIDAI_SANDBOX_ENABLED=true` demo only |
| Push | local VAPID keys | Vercel/Render env VAPID keys |
| Keep warm | not needed | UptimeRobot `/health` every 10 minutes |

Required env vars:

```txt
JWT_SECRET=
JWT_COOKIE_NAME=adhikarai_session
JWT_TTL_SECONDS=2592000

OTP_PROVIDER=mock|msg91
MSG91_AUTH_KEY=
MSG91_TEMPLATE_ID=
MSG91_SEND_OTP_URL=https://control.msg91.com/api/v5/otp
MSG91_VERIFY_OTP_URL=https://control.msg91.com/api/v5/otp/verify
OTP_TTL_SECONDS=300
OTP_RETRY_AFTER_SECONDS=30

DIGILOCKER_CLIENT_ID=
DIGILOCKER_CLIENT_SECRET=
DIGILOCKER_REDIRECT_URI=
DIGILOCKER_BASE_URL=https://betaapi.digitallocker.gov.in/public

UIDAI_SANDBOX_ENABLED=false
UIDAI_SANDBOX_BASE_URL=
UIDAI_CLIENT_ID=
UIDAI_CLIENT_SECRET=

VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_SUBJECT=mailto:admin@adhikarai.local

STORAGE_PROVIDER=cloudinary|supabase
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
SUPABASE_STORAGE_URL=
SUPABASE_SERVICE_ROLE_KEY=

NEXT_PUBLIC_APP_NAME=AdhikarAI
NEXT_PUBLIC_DEFAULT_LANGUAGE=hi
NEXT_PUBLIC_ENABLE_PWA=true
```

## File and Folder Structure

```txt
adhikarai/
  frontend/
    app/
      layout.tsx
      page.tsx
      manifest.ts
      offline/page.tsx
      schemes/[id]/page.tsx
      my-schemes/page.tsx
      history/page.tsx
      profile/page.tsx
      settings/page.tsx
    public/
      icons/
        icon-192.png
        icon-512.png
    components/
      app-shell/
        BottomNav.tsx
        InstallPrompt.tsx
        OfflineBanner.tsx
      home/
        VoiceHome.tsx
        MicButton.tsx
        QuickStatus.tsx
      schemes/
        SchemeCard.tsx
        NearMissCard.tsx
        DocumentChecklist.tsx
        SubstituteGuidance.tsx
        ApplicationSteps.tsx
        StatusTracker.tsx
      auth/
        LoginSheet.tsx
        OtpForm.tsx
      profile/
        ProfileForm.tsx
        HouseholdMembers.tsx
      settings/
        AccessibilitySettings.tsx
    lib/
      api/
        auth.ts
        schemes.ts
        checklist.ts
        notifications.ts
      db/
        indexedDb.ts
        syncQueue.ts
      pwa/
        serviceWorker.ts
        push.ts
      i18n/
        messages.ts
        format.ts
    styles/
      globals.css
  backend/
    app/
      auth/
        jwt.py
        otp.py
        providers/
          msg91.py
          mock.py
      notifications/
        push.py
        scheduler.py
        proactive.py
      integrations/
        digilocker.py
        uidai_sandbox.py
      action_plans/
        generator.py
        templates/
          action_plan.html
      api/
        routes/
          auth.py
          me.py
          saved_schemes.py
          checklists.py
          application_status.py
          digilocker.py
          aadhaar_prefill.py
          notifications.py
          action_plans.py
          offline_sync.py
      db/
        models/
          user.py
          otp.py
          saved_scheme.py
          checklist.py
          digilocker.py
          application_status.py
          notification.py
          action_plan.py
          offline_sync.py
```

## Testing Requirements

### Unit Tests

1. `test_guest_cannot_save_scheme`
   - No auth cookie.
   - Expected: `401 NOT_AUTHENTICATED`, frontend opens login sheet.

2. `test_verify_otp_sets_http_only_cookie`
   - Mock MSG91 success.
   - Expected: `Set-Cookie` contains `HttpOnly`, `Secure`, `SameSite=Lax`.

3. `test_guest_profile_migration_idempotent`
   - Same `guest_profile_id` submitted twice.
   - Expected: one profile, second call returns migrated false or duplicate ignored.

4. `test_ready_to_apply_requires_mandatory_docs`
   - Mandatory Aadhaar missing.
   - Expected: false.
   - Mark gathered.
   - Expected: true if no other mandatory docs.

5. `test_status_submitted_schedules_14_day_reminder`
   - Update status to submitted.
   - Expected: notification job scheduled at +14 days.

6. `test_account_delete_anonymizes_messages`
   - Delete user.
   - Expected: message content becomes `[deleted]`.

### Integration Tests

1. PWA manifest route
   - `GET /manifest.webmanifest`
   - Expected: app name, icons, display standalone, start URL `/`.

2. Offline cache
   - Use Playwright service worker context.
   - Load app, go offline, reload.
   - Expected: app shell and cached schemes visible.

3. OTP flow
   - Send OTP with mock provider.
   - Verify OTP.
   - `GET /me` returns user.

4. DigiLocker callback mocked
   - Mock token and files response.
   - Expected: verified document row and checklist status `verified`.

5. Action plan generation
   - Request PDF for two schemes.
   - Expected: stored URL and file size > 5 KB.

### Manual Test Cases

1. Slow Android home
   - Chrome devtools Moto G4, Slow 3G.
   - Expected: visible home shell under 3 seconds after install.

2. Guest full flow
   - Clear storage.
   - Select Hindi.
   - Complete voice/text eligibility.
   - Expected: results visible, save prompts login.

3. Offline checklist
   - Login.
   - Save scheme.
   - Go offline.
   - Mark document gathered.
   - Go online.
   - Expected: sync queue applies action exactly once.

4. Accessibility
   - Enable high contrast and extra-large font.
   - Expected: no overlapping text, buttons remain usable.

5. Push reminder
   - Save scheme with test scheduler offset 1 minute.
   - Expected: notification received and opens scheme detail.

## Known Constraints and Edge Cases

1. DigiLocker production access requires partner approval and may differ from beta endpoints.
2. UIDAI Aadhaar pre-fill is sandbox/demo only until legal and compliance approvals are complete.
3. Web Push support on Android depends on browser and notification permission.
4. WhatsApp direct sharing cannot attach files silently; app must use Web Share API when available or show downloadable/shareable file.
5. Offline voice ASR is not supported in Phase 4; offline users can browse cached results and type notes/checklist actions.
6. PWA storage can be cleared by Android under storage pressure. Server sync protects authenticated data only.
7. Low-literacy design does not mean no text; every key action uses icon plus short label and optional audio.
8. Color alone cannot communicate status; icons and labels are required.
9. Render cold starts can exceed voice latency target. UptimeRobot health ping is required for demo.
10. Guest data migration can conflict with existing profile; user is shown a simple merge screen only if phone already has a profile.

## Dependencies on Previous Phases

1. Phase 1 scheme schema, eligibility rules, document requirements, and admin status events.
2. Phase 2 agent sessions, profile/household model, document-check endpoint, profile update flow.
3. Phase 3 voice recorder, language selector, ASR, translation, and TTS components.

