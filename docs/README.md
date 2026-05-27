# AdhikarAI Documentation

**AdhikarAI** — multilingual, voice-first agentic AI platform for rural Indian welfare-scheme discovery.

---

## How to navigate these docs

| You want to... | Start here |
|---|---|
| Understand the product | [Overview](overview.md) |
| See the system architecture | [Architecture](architecture.md) |
| Check what is built | [Feature Map](feature-map.md) |
| Set up local development | [Local Development](setup/local-development.md) |
| Configure environment variables | [Environment Variables](setup/environment-variables.md) |
| Run or migrate the database | [Database & Migrations](setup/database-and-migrations.md) |
| Understand the voice/language pipeline | [Voice & Multilingual Pipeline](product/voice-multilingual-pipeline.md) |
| Understand the eligibility engine | [Scheme Eligibility](product/scheme-eligibility.md) |
| Understand dashboard / operator flows | [Dashboard Operator](product/dashboard-operator.md) |
| Understand auth, OTP, sessions | [Auth & Sessions](product/auth-and-sessions.md) |
| Read all backend API routes | [API Reference](engineering/api-reference.md) |
| Read the database schema | [Database Schema](engineering/database-schema.md) |
| Understand roles and tenancy | [RBAC & Tenancy](engineering/rbac-and-tenancy.md) |
| Run tests | [Testing Strategy](engineering/testing-strategy.md) |
| Deploy to staging | [Deployment Readiness](engineering/deployment-readiness.md) |
| Review security and privacy | [Security & Privacy](engineering/security-privacy.md) |
| Find a specific route or file | [Route Map](reference/route-map.md) · [File Purpose Index](reference/file-purpose-index.md) |
| Look up error codes | [Error Codes](reference/error-codes.md) |
| Read the glossary | [Glossary](reference/glossary.md) |

---

## Implementation Status (as of 2026-05-27)

| Layer | Status |
|---|---|
| FastAPI backend (55 tests pass) | **Implemented** |
| Next.js PWA + dashboard build | **Implemented** |
| PostgreSQL schema (5 migrations) | **Implemented** (SQL verified; live upgrade verified locally) |
| Eligibility engine (Experta + FAISS) | **Implemented** (unit-tested) |
| LangGraph agent graph | **Implemented** (graph topology; real LLM tested manually) |
| Phone OTP auth (mock provider) | **Implemented** |
| Phone OTP auth (MSG91 real SMS) | **Demo / Requires config** |
| Dashboard RBAC + tenancy | **Implemented** (unit-tested + local E2E verified) |
| Voice pipeline (ASR → translate → TTS) | **Implemented** (mocked; local providers not smoke-tested) |
| Playwright E2E suite | **Implemented** (6 spec files) |
| Bulk CSV eligibility processing | **Partial** (sync, no real eligibility run per row) |
| DigiLocker / Aadhaar prefill | **Demo / Sandbox only** |
| Real MSG91 OTP | **Not production-ready** |
| Real dashboard login (non-dev) | **Not production-ready** |
| Real voice providers (Whisper.cpp, Groq) | **Wired but not smoke-tested** |
| PWA push notifications | **Partial** (subscribe endpoint exists; delivery not real) |

For a full compliance matrix, see [docs/prd-compliance-audit.md](prd-compliance-audit.md).

---

## Directory Structure

```
docs/
  README.md                  ← this file
  overview.md                ← product summary, users, status
  architecture.md            ← system diagram, component boundaries
  feature-map.md             ← feature × status × route × test matrix
  agent-change-log.md        ← append-only implementation log
  prd-compliance-audit.md    ← Phase 1-5 PRD compliance evidence
  local-e2e-report.md        ← local bring-up and E2E workflow results
  e2e-testing.md             ← Playwright E2E setup and coverage
  deployment-readiness.md    ← staging/production env checklist

  setup/
    local-development.md     ← full local setup guide
    environment-variables.md ← all env vars annotated
    database-and-migrations.md
    redis.md
    troubleshooting.md

  product/
    beneficiary-pwa.md
    agent-conversation.md
    voice-multilingual-pipeline.md
    scheme-eligibility.md
    dashboard-operator.md
    admin-panel.md
    auth-and-sessions.md
    offline-pwa.md

  workflows/
    beneficiary-journey.md
    otp-login.md
    dashboard-login.md
    operator-beneficiary-management.md
    eligibility-matching.md
    document-checklist.md
    voice-turn.md
    bulk-eligibility.md
    scheme-admin-draft-publish.md
    rate-limiting.md

  engineering/
    frontend-structure.md
    backend-structure.md
    api-reference.md
    database-schema.md
    rbac-and-tenancy.md
    testing-strategy.md
    e2e-testing.md
    deployment-readiness.md
    security-privacy.md
    observability-and-health.md

  reference/
    route-map.md
    file-purpose-index.md
    config-reference.md
    error-codes.md
    glossary.md

  diagrams/
    system-context.md
    request-flows.md
    data-model.md

  prd/
    phase-1-foundation-eligibility-engine.md
    phase-2-agentic-conversation-layer.md
    phase-3-voice-multilingual-pipeline.md
    phase-4-user-facing-pwa-full-product.md
    phase-5-ngo-csc-dashboard-admin-panel.md
```

---

## Quick links

- [Local development](setup/local-development.md)
- [Architecture diagram](diagrams/system-context.md)
- [API reference](engineering/api-reference.md)
- [Change log](agent-change-log.md)
