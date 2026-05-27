# AdhikarAI

**AdhikarAI** is a multilingual, voice-first agentic AI platform that helps rural Indian beneficiaries discover and apply for government welfare schemes they are entitled to.

A rural beneficiary speaks their situation in their native language. The AI agent asks clarifying questions, matches eligible government schemes, and provides a document checklist, substitute-document guidance, and step-by-step application instructions. NGO workers and CSC operators can use the dashboard to assist multiple beneficiaries.

---

## Quick Start

→ **[Local development setup](docs/setup/local-development.md)**

→ **[Environment variables reference](docs/setup/environment-variables.md)**

→ **[Full documentation index](docs/README.md)**

---

## Repository Layout

```
backend/       FastAPI async Python backend
frontend/      Next.js 15 PWA + dashboard
docs/          Project documentation (start here)
```

---

## Implementation Status

The project covers Phases 1–5 of the product roadmap. The backend builds and all 55 automated tests pass. The Next.js PWA and dashboard build and the Playwright E2E suite runs. The product is **not production-ready end-to-end**: real SMS OTP, voice providers, and hosted infrastructure require additional configuration. See [docs/overview.md](docs/overview.md) for a precise status breakdown.

---

## Documentation

Full documentation lives under [`docs/`](docs/README.md). Key sections:

| Section | What is covered |
|---|---|
| [Setup](docs/setup/local-development.md) | Local PostgreSQL, Redis, backend, frontend, seed data |
| [Architecture](docs/architecture.md) | System diagram, request flow, component boundaries |
| [Feature Map](docs/feature-map.md) | All features, status, tests, and routes |
| [API Reference](docs/engineering/api-reference.md) | Every backend route with auth requirements |
| [Database Schema](docs/engineering/database-schema.md) | Tables, columns, migrations |
| [RBAC & Tenancy](docs/engineering/rbac-and-tenancy.md) | Roles, permissions, org scoping |
| [Deployment](docs/engineering/deployment-readiness.md) | Staging/production checklist |
| [Security](docs/engineering/security-privacy.md) | Secrets, Aadhaar guards, cookie auth |
| [Testing](docs/engineering/testing-strategy.md) | Unit, integration, Playwright E2E |

---

## License

Private — not licensed for public distribution.
