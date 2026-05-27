# Error Codes

All machine-readable error codes returned by the AdhikarAI FastAPI backend. Every error follows the standard response format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "field": "optional_field_name",
    "request_id": "req_XXXXXXXXXXXX"
  }
}
```

---

## Auth & Session Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `NOT_AUTHENTICATED` | 401 | Please login with phone to continue. | `core/security.py` |
| `ADMIN_TOKEN_INVALID` | 401 | Admin token is invalid. | `core/security.py` |
| `DASHBOARD_SESSION_REQUIRED` | 401 | Please login to the dashboard. | `core/security.py` |
| `DASHBOARD_AUTH_NOT_CONFIGURED` | 503 | Dashboard login is not configured. | `api/routes/dashboard.py` |
| `DASHBOARD_DEV_LOGIN_DISABLED` | 403 | Dev dashboard login is disabled. | `api/routes/dashboard.py` |
| `DASHBOARD_INVALID_CREDENTIALS` | 401 | Email or code is not correct. | `api/routes/dashboard.py` |
| `DASHBOARD_MEMBER_AMBIGUOUS` | 400 | Multiple active dashboard members use this email. | `api/routes/dashboard.py` |

---

## OTP Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `OTP_PROVIDER_FAILED` | 502 | OTP could not be sent. Try again. | `services/phase4.py` |
| `OTP_RATE_LIMITED` | 429 | Too many OTP requests. Try again after 10 minutes. | `services/phase4.py` |
| `OTP_CHALLENGE_NOT_FOUND` | 404 | OTP request was not found. | `services/phase4.py` |
| `OTP_EXPIRED` | 410 | OTP expired. Request a new one. | `services/phase4.py` |
| `OTP_ATTEMPTS_EXCEEDED` | 429 | Too many OTP attempts. Request a new one. | `services/phase4.py` |
| `OTP_INVALID` | 401 | OTP is not correct. Try again. | `services/phase4.py` |

---

## RBAC & Permission Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `PERMISSION_DENIED` | 403 | You do not have access to this action. | `dashboard/rbac.py` |
| `ORG_SCOPE_DENIED` | 403 | You do not have access to this organisation. | `dashboard/rbac.py` |
| `BENEFICIARY_NOT_ASSIGNED` | 403 | This beneficiary is not assigned to you. | `dashboard/rbac.py` |
| `ASSIGNMENT_DENIED` | 403 | Operators can assign only to themselves. | `dashboard/beneficiaries.py` |

---

## Resource Not Found Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `SCHEME_NOT_FOUND` | 404 | Scheme was not found. | `services/schemes.py`, `services/phase4.py` |
| `PROFILE_NOT_FOUND` | 404 | Profile was not found. | `services/profiles.py`, `services/phase4.py` |
| `HOUSEHOLD_NOT_FOUND` | 404 | Household was not found. | `services/households.py` |
| `SESSION_NOT_FOUND` | 404 | This conversation was not found. | `services/sessions/session_service.py` |
| `ORGANISATION_NOT_FOUND` | 404 | Organisation was not found. | `services/schemes.py` |
| `BENEFICIARY_NOT_FOUND` | 404 | Beneficiary was not found. | `dashboard/beneficiaries.py` |
| `FOLLOWUP_NOT_FOUND` | 404 | Follow-up was not found. | `dashboard/beneficiaries.py` |
| `APPLICATION_STATUS_NOT_FOUND` | 404 | Application status was not found. | `dashboard/beneficiaries.py` |
| `BULK_JOB_NOT_FOUND` | 404 | Bulk job was not found. | `api/routes/dashboard.py` |
| `DRAFT_NOT_FOUND` | 404 | Draft was not found. | `admin_panel/scheme_drafts.py` |
| `QUALITY_FLAG_NOT_FOUND` | 404 | Quality flag was not found. | `admin_panel/queries.py` |
| `RULE_NOT_FOUND` | 404 | Eligibility rule was not found. | `services/schemes.py` |

---

## Conflict / State Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `SCHEME_ID_EXISTS` | 409 | Scheme ID already exists. | `services/schemes.py` |
| `DRAFT_ALREADY_PUBLISHED` | 409 | Draft is already published. | `admin_panel/scheme_drafts.py` |
| `SESSION_EXPIRED` | 410 | This conversation has expired. Please start again. | `services/sessions/session_service.py` |

---

## Validation Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `INVALID_REQUEST` | 422 | (varies — first Pydantic validation error) | `app/main.py` |
| `INVALID_PROFILE_PATCH` | 422 | Profile patch contains an unsupported field. | `services/profiles.py` |
| `ORGANISATION_REQUIRED` | 422 | Please include organisation_id for this session. | `services/sessions/session_service.py` |
| `AADHAAR_NOT_ALLOWED` | 422 | Do not enter Aadhaar number here. | `services/phase4.py` |
| `DRAFT_VALIDATION_FAILED` | 422 | Draft has validation errors. / Publish is blocked by validation errors. | `admin_panel/scheme_drafts.py` |

---

## CSV / Bulk Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `CSV_TOO_LARGE` | 413 | CSV must be 2 MB or smaller. | `dashboard/bulk_eligibility.py` |
| `CSV_INVALID_FORMAT` | 415 | Not a valid CSV file. | `dashboard/bulk_eligibility.py` |
| `CSV_TOO_MANY_ROWS` | 422 | CSV can include at most 500 rows. | `dashboard/bulk_eligibility.py` |

---

## Rate Limiting

| Code | HTTP | Message | Source |
|---|---|---|---|
| `RATE_LIMIT_EXCEEDED` | 429 | You have used today's limit. Please try tomorrow or visit a CSC. | `rate_limit/service.py` |

Response includes `retry_after_seconds` and `retry_at` in the error details.

---

## Voice / ASR Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `AUDIO_TOO_LARGE` | 413 | Audio file exceeds 8 MB. Please record a shorter message. | `voice/audio_utils.py` |
| `UNSUPPORTED_AUDIO_FORMAT` | 415 | This audio format is not supported. Please record again or type your message. | `voice/audio_utils.py`, `voice/providers/groq_whisper.py` |
| `AUDIO_RESAMPLE_FAILED` | 502 | Audio could not be processed. Please try again or type. | `voice/audio_utils.py` |
| `ASR_PROVIDER_ERROR` | 502 | Speech service failed. Please try again or type your message. | `voice/providers/*.py` |
| `ASR_TIMEOUT` | 504 | Speech service is slow. Please try again or type your message. | `voice/providers/*.py` |
| `VOICE_PROVIDER_MISCONFIGURED` | 500 | Voice provider is not configured. | `voice/providers/factory.py` |

---

## Translation Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `TRANSLATION_UNAVAILABLE` | 502 | Translation failed. You can read the text or type again. | `translation/providers/*.py` |
| `TRANSLATION_PROVIDER_MISCONFIGURED` | 500 | Translation provider is not configured. | `translation/providers/factory.py` |

---

## TTS Errors

| Code | HTTP | Message | Source |
|---|---|---|---|
| `TTS_PROVIDER_ERROR` | 502 | Voice playback failed. You can read the text or try again. | `tts/providers/*.py` |
| `TTS_AUDIO_NOT_FOUND` | 404 | Voice audio expired. You can replay after trying again. | `api/routes/tts.py` |
| `TTS_PROVIDER_MISCONFIGURED` | 500 | TTS provider is not configured. | `tts/providers/factory.py` |
