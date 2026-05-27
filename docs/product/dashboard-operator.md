# Dashboard Operator

The AdhikarAI dashboard is a dense, data-focused web interface for NGO workers and CSC operators to assist multiple beneficiaries. It is also used by NGO admins for oversight and by super admins for platform management.

---

## Roles

| Role | Access |
|---|---|
| `operator` | Own assigned beneficiaries only: read, write, notes, follow-ups, status updates |
| `ngo_admin` | All beneficiaries in their organisation: read, write, export, analytics |
| `super_admin` | All organisations: full access including scheme management and quality review |

See [RBAC & Tenancy](../engineering/rbac-and-tenancy.md) for the full permission matrix.

---

## Dashboard Routes (Frontend)

| Route | Description |
|---|---|
| `/dashboard/login` | Login page (dev/local mode only) |
| `/dashboard` | Main dashboard: recent beneficiaries, notifications, stats |
| `/dashboard/beneficiaries` | Beneficiary list with search, filter, pagination |
| `/dashboard/beneficiaries/{id}` | Beneficiary detail: profile, notes, follow-ups, scheme assignments, status |
| `/dashboard/bulk-eligibility` | CSV upload for bulk eligibility processing |
| `/dashboard/status-board` | Kanban-style application status view |
| `/dashboard/scheme-guide` | Published scheme summaries for operators |
| `/dashboard/exports` | CSV export of beneficiary list |
| `/dashboard/help` | Operator help documentation |

---

## Beneficiary Management

### List Beneficiaries

`GET /dashboard/beneficiaries`

Operators see only their assigned beneficiaries. NGO admins see all beneficiaries in their organisation. Super admins see all.

Filters:
- `q`: Free-text search on name, phone, state code
- `state_code`: Filter by state
- `status`: Filter by application status
- `followup_due`: Filter by follow-up due date
- `assigned_operator_id`: Filter by assigned operator (admin only)
- `limit`, `offset`: Pagination (max 200 per page)

### Create Beneficiary

`POST /dashboard/beneficiaries`

Required fields:
- `name`: Beneficiary name
- `phone_e164`: Phone number in E.164 format (e.g., `+919876543210`)
- `state_code`: 2-letter state code

Optional:
- `language_code`: Preferred language
- `gender`, `date_of_birth`, `caste`, `annual_income_inr`, `bpl_card`, `disability`
- `assigned_operator_id`: Assign to a specific operator

### Get Beneficiary Detail

`GET /dashboard/beneficiaries/{id}`

Returns: full profile, notes, follow-ups, scheme assignments with application status.

**Access control**: Operators can only access their assigned beneficiaries. Attempting to access an unassigned beneficiary returns `403 BENEFICIARY_NOT_ASSIGNED`.

### Update Beneficiary

`PATCH /dashboard/beneficiaries/{id}`

Updates profile fields. All fields are optional (partial update).

---

## Notes

`POST /dashboard/beneficiaries/{id}/notes`

Operators can add free-text notes to a beneficiary record. Notes are timestamped and actor-attributed.

```json
{"note": "Beneficiary visited CSC today. Documents collected."}
```

---

## Follow-ups

`POST /dashboard/beneficiaries/{id}/followups`

Schedule a follow-up action:

```json
{
  "due_date": "2026-06-15",
  "note": "Call to check application status",
  "followup_type": "call"
}
```

`PATCH /dashboard/followups/{id}` — Mark a follow-up as completed or update the note.

---

## Application Status

`PATCH /dashboard/application-status/{status_id}`

Updates the application status for a scheme assignment:

```json
{
  "status": "submitted",
  "notes": "Application submitted at district office"
}
```

Status values: `not_started`, `documents_collecting`, `submitted`, `approved`, `rejected`, `pending`

---

## Bulk Eligibility

`POST /dashboard/bulk-eligibility` (multipart CSV upload)

Upload a CSV of beneficiary profiles for batch eligibility screening.

**Current status**: **Partial**. The CSV is parsed, rows are stored in `BulkEligibilityRow`, but real eligibility matching per row is not yet implemented. The job is marked `completed` synchronously without running the eligibility engine per row.

CSV format: `name,gender,age,state_code,caste,annual_income_inr,bpl_card`

`GET /dashboard/bulk-eligibility/{job_id}` — Check job status.

`GET /dashboard/bulk-eligibility/{job_id}/download` — Download result CSV.

---

## Operator Notifications

`GET /dashboard/operator-notifications`

Returns unread notifications for the current actor (scoped to their organisation and member ID). Notifications are created by background jobs or admin actions.

`POST /dashboard/operator-notifications/{id}/read` — Mark as read.

---

## Status Board

`GET /dashboard/status-board`

Returns a summary of application statuses grouped by scheme, filterable by `state_code`. Useful for tracking pipeline health.

---

## Dashboard Login (Dev/Local Only)

**Current status**: Dev/local only.

`POST /dashboard/auth/login`

```json
{
  "email": "operator.local@example.test",
  "login_code": "local-e2e-login"
}
```

This sets an httpOnly dashboard JWT cookie. The `login_code` is shared and configured via `DASHBOARD_DEV_LOGIN_CODE`. It is not suitable for production.

In production, `DASHBOARD_AUTH_PROVIDER=disabled` means this endpoint returns `503 DASHBOARD_AUTH_NOT_CONFIGURED`.

---

## Security Notes

- All dashboard routes require `Depends(require_dashboard_actor)`.
- Operators cannot access beneficiaries not assigned to them.
- NGO admins cannot access beneficiaries in other organisations.
- Super admins can access all organisations.
- Dashboard sessions use httpOnly cookies with 1-hour idle timeout.
- Audit logs are written for create/update operations on beneficiaries, notes, and follow-ups.

---

## Known Limitations

- Real staff identity provider (SSO/OAuth) is not implemented. Production cannot have dashboard auth until a real provider is added.
- Bulk eligibility does not actually run the eligibility engine per CSV row.
- Delete beneficiary endpoint is not implemented.
- Dashboard filters are partial (some filter combinations may not behave as expected).
- Beneficiary export CSV has limited fields.
- Integration tests for cross-tenant denial paths are pending.
