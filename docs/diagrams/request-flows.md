# Request Flow Diagrams

Key request flows through the AdhikarAI system.

---

## Beneficiary Agent Turn (Text)

```mermaid
sequenceDiagram
    participant User as Beneficiary
    participant PWA as Next.js PWA
    participant API as FastAPI
    participant Agent as LangGraph
    participant Redis as Redis
    participant DB as PostgreSQL
    participant LLM as LLM

    User->>PWA: Types message
    PWA->>API: POST /agent/message {session_id, message, language_code}
    API->>Agent: handle_chat_turn()
    Agent->>Redis: Load session state
    Agent->>LLM: Extract profile facts from message
    LLM-->>Agent: Structured facts JSON
    Agent->>Agent: Update profile, compute completeness
    alt completeness >= 75% or questions >= 8
        Agent->>DB: Load candidate schemes
        Agent->>Agent: Run eligibility match + near-miss
        Agent-->>API: {type: "result", payload: matched_schemes}
    else completeness < 75%
        Agent->>Agent: Select next question
        Agent-->>API: {type: "question", content: "What is your caste?"}
    end
    Agent->>DB: Store conversation message
    Agent->>Redis: Persist updated session state
    API-->>PWA: ChatOutputModel
    PWA->>User: Display question or results
```

---

## Voice Turn (Full Pipeline)

```mermaid
sequenceDiagram
    participant User as Beneficiary
    participant PWA as Next.js PWA
    participant API as FastAPI
    participant ASR as ASR Provider
    participant TR as Translation
    participant Agent as Agent/Session
    participant TTS as TTS Provider
    participant Cache as Redis Cache
    participant DB as PostgreSQL

    User->>PWA: Records audio
    PWA->>API: POST /voice/turn (multipart audio)
    API->>API: Validate audio (size, type, duration)
    API->>ASR: Transcribe audio
    ASR-->>API: {transcript, confidence, detected_language}
    alt confidence < 0.70
        API->>DB: Store VoiceTurn (low confidence)
        API-->>PWA: {type: "low_confidence", content: localized_message}
    else confidence >= 0.70
        API->>TR: Translate to English
        TR->>Cache: Check cache
        Cache-->>TR: Hit or miss
        TR-->>API: English text
        API->>Agent: handle_chat_turn(english_text)
        Agent-->>API: ChatOutputModel
        API->>TR: Translate response to user language
        TR-->>API: Localized response
        API->>TTS: Synthesize audio
        TTS->>Cache: Check/store cache
        TTS-->>API: audio_url
        API->>DB: Store VoiceTurn (metrics only, no raw audio)
        API-->>PWA: {type, content, audio_url, timings}
    end
    PWA->>User: Play audio + show text
```

---

## OTP Authentication

```mermaid
sequenceDiagram
    participant User as Beneficiary
    participant PWA as Next.js PWA
    participant API as FastAPI
    participant DB as PostgreSQL
    participant OTP as OTP Provider

    User->>PWA: Enters phone number
    PWA->>API: POST /auth/send-otp {phone_e164}
    API->>API: Generate 6-digit OTP
    API->>API: Hash OTP (PBKDF2, 120k iterations)
    API->>DB: Create OtpChallenge (hash, expiry 5min, max 5 attempts)
    API->>OTP: Send SMS
    OTP-->>User: SMS arrives
    API-->>PWA: {challenge_id, expires_in_seconds}

    User->>PWA: Enters OTP
    PWA->>API: POST /auth/verify-otp {challenge_id, otp}
    API->>DB: Load OtpChallenge
    alt expired
        API-->>PWA: 410 OTP_EXPIRED
    else attempts exceeded
        API-->>PWA: 429 OTP_ATTEMPTS_EXCEEDED
    else hash mismatch
        API->>DB: Increment attempts
        API-->>PWA: 401 OTP_INVALID
    else hash matches
        API->>DB: Upsert User
        API->>API: Create JWT
        API-->>PWA: Set httpOnly cookie + return User
    end
```

---

## Dashboard RBAC Enforcement

```mermaid
sequenceDiagram
    participant Op as Operator (Org A)
    participant API as FastAPI
    participant DB as PostgreSQL

    Op->>API: GET /dashboard/beneficiaries/{id}
    API->>API: Extract JWT from cookie
    API->>API: Decode → DashboardActor(role=operator, org=OrgA)
    API->>DB: SELECT beneficiary WHERE id=?
    DB-->>API: Beneficiary(org=OrgA, assigned_operator=Other)
    API->>API: assert_beneficiary_access()
    Note over API: role=operator AND assigned_operator ≠ actor.member_id
    API-->>Op: 403 BENEFICIARY_NOT_ASSIGNED
```

---

## Dashboard Login (Dev Mode)

```mermaid
sequenceDiagram
    participant User as Operator
    participant FE as Dashboard UI
    participant API as FastAPI
    participant DB as PostgreSQL

    User->>FE: Enters email + dev code
    FE->>API: POST /dashboard/auth/login {email, login_code}
    API->>API: Check DASHBOARD_AUTH_PROVIDER=dev
    API->>API: Check DASHBOARD_DEV_LOGIN_ENABLED=true
    API->>API: Verify login_code == DASHBOARD_DEV_LOGIN_CODE
    API->>DB: SELECT organisation_member WHERE email=?
    alt Not found or inactive
        API-->>FE: 401 DASHBOARD_INVALID_CREDENTIALS
    else Found
        API->>API: Create dashboard JWT (typ=dashboard, role, org, member_id)
        API-->>FE: Set httpOnly cookie + return actor
    end
    FE->>User: Redirect to /dashboard
```

---

## Rate Limiting

```mermaid
sequenceDiagram
    participant Client as Client
    participant API as FastAPI
    participant Redis as Redis

    Client->>API: Any rate-limited request
    API->>Redis: INCR rate:{org}:{type}:{actor}:{date}
    Redis-->>API: current count
    alt count <= limit
        API->>API: Process request normally
        API-->>Client: 200 Success
    else count > limit
        API->>API: Calculate seconds until midnight UTC
        API-->>Client: 429 RATE_LIMIT_EXCEEDED {retry_after_seconds, retry_at}
    end
```

---

## Scheme Draft → Publish

```mermaid
sequenceDiagram
    participant Admin as Super Admin
    participant FE as Admin UI
    participant API as FastAPI
    participant DB as PostgreSQL

    Admin->>FE: Creates scheme draft
    FE->>API: POST /admin/scheme-drafts {payload}
    API->>DB: Insert SchemeDraft (status=draft)
    API-->>FE: {draft_id}

    Admin->>FE: Clicks Preview
    FE->>API: POST /admin/scheme-drafts/{id}/preview
    API->>API: Validate draft payload (rules, fields)
    alt Validation errors
        API-->>FE: 422 DRAFT_VALIDATION_FAILED {errors}
    else Valid
        API-->>FE: {valid: true, preview: {...}}
    end

    Admin->>FE: Clicks Publish
    FE->>API: POST /admin/scheme-drafts/{id}/publish
    API->>API: Re-validate draft
    API->>DB: Upsert Scheme from draft
    API->>DB: Create SchemeAuditLog
    API->>DB: Update SchemeDraft status=published
    API-->>FE: {scheme_id, published: true}
```
