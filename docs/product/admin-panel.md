# Admin Panel

The admin panel is the super-admin and NGO-admin layer of the AdhikarAI dashboard. It provides tools for scheme management, quality monitoring, analytics, and platform oversight.

---

## Access

Admin panel routes (`/admin/*`) are accessible to users with the following dashboard roles:
- `super_admin`: Full access to all admin features
- `ngo_admin`: Limited analytics access within their organisation

All admin API routes are prefixed `/admin` and require `require_dashboard_actor`.

---

## Frontend Routes

| Route | Description | Min Role |
|---|---|---|
| `/admin/schemes` | Scheme draft editor and publish workflow | `super_admin` |
| `/admin/quality` | Quality flags review | `super_admin` |
| `/admin/unmatched-queries` | Beneficiary queries that matched no schemes | `super_admin` |
| `/admin/analytics` | Platform analytics dashboard | `ngo_admin` |

---

## Scheme Draft / Publish Workflow

**Status**: Partial — draft creation, preview, and publish work; history returns empty.

### Create Draft

`POST /admin/scheme-drafts`

```json
{
  "draft_payload": {
    "name": "Widow Pension Scheme",
    "description": "Monthly pension for widows aged 40-79",
    "benefit_type": "cash",
    "benefit_amount_inr": 500,
    "eligibility_rules": {...}
  },
  "change_summary": "Increased benefit amount from 400 to 500"
}
```

Creates a `SchemeDraft` row. If editing an existing scheme, links via `scheme_id`.

### Preview Draft

`POST /admin/scheme-drafts/{draft_id}/preview`

Returns the draft payload with validation results (checks rule JSON schema, required fields). Does not publish.

### Publish Draft

`POST /admin/scheme-drafts/{draft_id}/publish`

Validates and applies the draft to the scheme table:
- If scheme exists: updates scheme fields, creates a `SchemeAuditLog` entry.
- If new scheme: creates the `Scheme` row and sets status to `draft` (operator must then publish).
- Records a `SchemeAuditLog` entry with `change_summary` and actor.

### History

`GET /admin/schemes/{scheme_id}/history`

Returns `[]` currently — scheme history audit trail is recorded but query is not yet implemented.

---

## Unmatched Queries

**Status**: Partial — table exists, fixture data shows in E2E, no auto-generation.

`GET /admin/unmatched-queries`

Returns grouped unmatched query texts: beneficiary queries that did not match any scheme. These are candidates for new scheme rules or content gaps.

`GET /admin/unmatched-queries.csv`

Exports the unmatched query list as a CSV file.

---

## Quality Flags

**Status**: Partial — table exists, fixture data shows in E2E, no auto-generation.

`GET /admin/quality-flags`

Returns quality flags: issues flagged by the quality monitor job (e.g., schemes with missing documents, rules with missing criteria, or conversation sessions with zero matches).

`POST /admin/quality-flags/{flag_id}/review`

```json
{"review_notes": "Scheme rules updated to fix gap."}
```

Marks a flag as reviewed with notes.

---

## Analytics

**Status**: Partial — basic counts are returned; no dashboarding or trend data.

`GET /admin/analytics?organisation_id=...`

Returns aggregate counts:
- Total beneficiaries
- Beneficiaries by status
- Scheme matches
- Recent audit log activity

Super admins can pass `organisation_id` to scope analytics to a specific NGO. NGO admins only see their own organisation.

---

## Audit Logs

All admin write operations (scheme draft creation, publish, quality review) are recorded in `audit_logs`:

| Column | Content |
|---|---|
| `actor_member_id` | OrganisationMember who performed the action |
| `action` | Action type (e.g., `scheme.draft.create`, `scheme.publish`) |
| `resource_type` | `scheme`, `scheme_draft`, `quality_flag`, etc. |
| `resource_id` | ID of the affected resource |
| `payload` | JSONB snapshot of the change |
| `created_at` | Timestamp |

---

## Known Limitations

- Real staff SSO/authentication is not implemented. Admin login works in local-dev mode only.
- Quality flag auto-generation job exists in the scheduler config but is not fully implemented.
- Unmatched query population is manual (test fixture) in local E2E; no automatic recording from conversation sessions yet.
- Scheme audit history query not implemented.
- No frontend scheme editor UI with field-by-field form — admin currently uses the draft JSON directly.
