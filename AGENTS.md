# AdhikarAI Agent Instructions

This file is the single source of truth for AI coding agents working in this repository.

Compatibility:

- Codex: reads `AGENTS.md` from the repository tree.
- Antigravity: use this `AGENTS.md` as the project rules file.
- Gemini CLI: Gemini defaults to `GEMINI.md`. Configure Gemini once to also load `AGENTS.md`, or symlink/copy this file to `GEMINI.md` only if your local Gemini setup cannot load `AGENTS.md`.

Recommended Gemini CLI settings:

```json
{
  "context": {
    "fileName": ["AGENTS.md", "GEMINI.md"]
  }
}
```

<!-- BEGIN EVERYTHING CODEX TOOLKIT -->
# Everything Codex Toolkit

Use the shared toolkit installed at `/home/noobsambit/.codex/everything-codex`.

Prefer project `AGENTS.md` first. Use toolkit skills, prompts, and rules when they fit the task.

Useful shared paths:

- `/home/noobsambit/.codex/everything-codex/skills/`
- `/home/noobsambit/.codex/everything-codex/agents/`
- `/home/noobsambit/.codex/everything-codex/prompts/`
- `/home/noobsambit/.codex/everything-codex/rules/`

Registered Codex skills, when installed with `--register-skills`, live under `/home/noobsambit/.codex/skills/`.

<!-- END EVERYTHING CODEX TOOLKIT -->

## Project Context

AdhikarAI is a multilingual, voice-first agentic AI platform that helps rural Indians discover and apply for government welfare schemes they are entitled to.

Primary user:

- Rural Indian beneficiary.
- May have very low literacy.
- May speak only a regional language.
- May use a low-end Android phone on 2G/3G.

Secondary user:

- NGO worker or CSC operator assisting multiple beneficiaries.

Core journey:

```txt
user speaks their situation in native language
-> agent asks clarifying questions
-> agent matches eligible government schemes
-> agent gives document checklist, substitute document guidance, and application steps
```

Non-negotiable stack:

- Frontend: Next.js 15, TypeScript, PWA, App Router.
- Backend: FastAPI, async Python, WebSockets.
- Agent: LangGraph.
- Local production LLM: Ollama with `llama3.1:8b` and `qwen2.5:7b`.
- Hosted demo LLM: Groq API with `llama-3.3-70b-versatile`.
- Local ASR: Whisper.cpp CUDA.
- Hosted ASR: Groq Whisper API with `whisper-large-v3-turbo`.
- Translation: IndicTrans2 locally, AI4Bharat hosted API for demo, Google Translate fallback only when configured.
- TTS: IndicTTS-compatible local service, Google Cloud TTS for demo.
- Embeddings: IndicBERT or multilingual-e5.
- Vector search: FAISS.
- Eligibility: Experta plus PostgreSQL JSONB rules.
- Database: PostgreSQL, Neon for hosted.
- Cache/session: Redis, Upstash for hosted.
- Auth: Phone OTP via MSG91.
- Hosting: Vercel frontend, Render backend, UptimeRobot keep-warm.

Implementation PRDs live in:

- `docs/prd/phase-1-foundation-eligibility-engine.md`
- `docs/prd/phase-2-agentic-conversation-layer.md`
- `docs/prd/phase-3-voice-multilingual-pipeline.md`
- `docs/prd/phase-4-user-facing-pwa-full-product.md`
- `docs/prd/phase-5-ngo-csc-dashboard-admin-panel.md`

Before implementing a feature, read the relevant PRD phase and treat it as the product contract.

## Highest Priority Rule: Cross-Layer Consistency

When the user asks for any change, the agent must check whether the change affects any of these layers:

1. Frontend UI/routes/components.
2. Frontend API client, TypeScript types, forms, validation, loading/error states.
3. Backend API routes, service logic, Pydantic schemas, auth/permissions.
4. Database schema, migrations, SQLAlchemy models, indexes, seed data.
5. Agent/LangGraph state, prompts, tools, memory, Redis session shape.
6. Voice, ASR, translation, TTS, language routing, latency behavior.
7. Tests: unit, integration, E2E, fixtures, mocks.
8. Environment/config: `.env.example`, settings, deployment variables.
9. Documentation: README, PRDs, API docs, operator docs, changelog.

Do not make isolated backend changes that leave the frontend, DB, generated types, tests, or UI stale.

Do not make isolated frontend changes that depend on backend fields or routes that do not exist.

Do not make schema/model changes without migrations and test/seed updates when relevant.

If a change genuinely affects only one layer, say that explicitly in the plan and final response.

## Cross-Layer Impact Checklist

Before coding, answer these privately or in the plan for non-trivial work:

```txt
Does this change alter an API request or response?
If yes: update backend route, Pydantic schema, TypeScript type, API client, UI usage, tests.

Does this change alter stored data?
If yes: update SQL migration, SQLAlchemy model, seed data, fixtures, indexes, and migration tests.

Does this change alter eligibility behavior?
If yes: update rule validation, Experta evaluator, near-miss behavior, seed examples, and match tests.

Does this change alter user-visible UI?
If yes: update component state, accessibility labels, mobile layout, loading/error states, and UI tests.

Does this change alter auth, roles, or tenant scope?
If yes: update permission checks, organisation_id filtering, tests for cross-tenant denial, and docs.

Does this change alter voice or language behavior?
If yes: update ASR/translation/TTS provider interface, localized messages, fallback states, and latency tests.

Does this change require env vars?
If yes: update config model, `.env.example`, deployment notes, and startup validation.
```

No task is complete until impacted layers are updated or explicitly marked not impacted.

## Required Execution Workflow

For every implementation task:

1. Inspect existing code and relevant PRD sections.
2. State assumptions and success criteria for non-trivial work.
3. Identify impacted layers using the Cross-Layer Impact Checklist.
4. Make the smallest coherent change across all impacted layers.
5. Add or update tests that prove the change.
6. Run the narrowest useful verification first, then broader checks if risk warrants it.
7. Update the agent change log.
8. In the final response, include:
   - what changed,
   - impacted layers,
   - verification run,
   - anything not done or blocked.

## Agent Change Log System

Maintain an append-only implementation log at:

```txt
docs/agent-change-log.md
```

If the file does not exist, create it on the first code-changing task.

Do not log purely exploratory reads, planning-only turns, or failed attempts that made no file changes.

Add one entry per completed implementation task using this exact template:

```md
## YYYY-MM-DD HH:mm TZ - Short Task Title

- Request: one sentence describing what the user asked.
- Agent: Codex / Gemini CLI / Antigravity / other.
- Changed files:
  - `path/to/file`
- Cross-layer impact:
  - Frontend: changed / not impacted
  - Backend: changed / not impacted
  - Database: changed / not impacted
  - UI/UX: changed / not impacted
  - Tests: changed / not impacted
  - Config/Env: changed / not impacted
  - Docs: changed / not impacted
- Schema/migration notes: migration added / not needed, with reason.
- API contract notes: changed / unchanged, with reason.
- Verification:
  - command run and result
- Follow-ups:
  - none, or concrete remaining work
```

Change log rules:

- Append new entries at the top, below the title.
- Never delete or rewrite older entries unless the user explicitly asks.
- Never include secrets, tokens, OTPs, private phone numbers, Aadhaar numbers, or raw user documents.
- Use masked identifiers where needed, for example `+91******3210`.
- If verification could not run, write the exact reason.

## Behavioral Guidelines to Reduce Common LLM Coding Mistakes

Merge with project-specific instructions as needed.

Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```txt
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

These guidelines are working if: fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Product-Specific Engineering Rules

### Low-Literacy and Low-Bandwidth First

- Design for low-end Android devices and 2G/3G.
- Keep UI text short, concrete, and translatable.
- Use icons plus short labels for navigation. Never rely on text-only navigation.
- Every important error state must offer a speak/type fallback.
- Avoid heavy animations, oversized images, decorative backgrounds, and large bundles.
- Test mobile layouts for text overflow and touch target size.

### Multi-Tenancy

- Every tenant-scoped table must include `organisation_id`.
- Every tenant-scoped query must filter by `organisation_id`.
- Never trust `organisation_id` from request body alone when an authenticated actor exists.
- Operators can access only assigned beneficiaries.
- NGO admins can access only their organisation.
- Super admins can access all organisations.

### Database and Migrations

- Any SQLAlchemy model change that affects persistence requires a migration.
- Any migration that changes runtime behavior requires tests or a clear manual verification.
- Keep schema, SQLAlchemy models, Pydantic schemas, TypeScript types, and seed data aligned.
- Do not store Aadhaar numbers, OTPs, raw access tokens, or full bank account numbers.
- Store document verification metadata, not raw documents, unless a PRD or user explicitly requires storage.

### API Contracts

- All API changes must update:
  - Pydantic request/response models,
  - TypeScript request/response types,
  - frontend API client,
  - tests,
  - relevant docs when behavior changes.
- Use stable machine-readable error codes.
- User-facing error messages must be short and actionable.

### Eligibility Rules

- Eligibility rules must be data-driven through PostgreSQL JSONB, not hard-coded into app logic.
- Cross-scheme exclusions must be evaluated before normal criteria.
- Near-miss results require exactly one failed criterion and no unknown required criteria.
- Rule changes must not require code deployments unless evaluator capabilities change.

### Agent and Voice Pipeline

- The LangGraph agent is a constrained welfare-scheme intake agent, not a general chatbot.
- The agent must ask one question at a time.
- The agent must not re-ask fields already answered with sufficient confidence.
- Low-confidence ASR must not be sent to the agent.
- Preserve provider interfaces so local and hosted environments return the same internal shapes.
- Target hosted voice round-trip latency remains under 4 seconds for normal short turns.

### Frontend and UI

- Use Next.js App Router and TypeScript.
- Use PWA-safe patterns and IndexedDB for offline data.
- Keep components accessible: visible focus, accessible names, WCAG AA contrast, 44 px touch targets.
- Cards use 8 px radius or less unless a design system later says otherwise.
- Do not put cards inside cards.
- Do not create marketing landing pages for app surfaces. Build the actual usable experience.
- For scheme cards, keep benefit, amount, eligibility status, checklist, substitute guidance, and apply action aligned with backend data.

### Testing

Prefer tests that prove behavior over snapshot churn.

Minimum expectations:

- Backend logic: unit tests for evaluators, validators, services.
- API changes: integration tests for request/response and error codes.
- DB changes: migration test or explicit migration verification.
- Frontend behavior: component or E2E tests for critical user flows.
- Voice/language behavior: provider mocks and fallback tests.Compatibility:

- Codex: reads `AGENTS.md` from the repository tree.
- Antigravity: use this `AGENTS.md` as the project rules file.
- Gemini CLI: Gemini defaults to `GEMINI.md`. Configure Gemini once to also load `AGENTS.md`, or symlink/copy this file to `GEMINI.md` only if your local Gemini setup cannot load `AGENTS.md`.
- Permissions: cross-tenant and role-denial tests.

If tests cannot run, explain why and provide the exact command that should be run later.

## Safety and Security

- Never print, log, commit, or expose secrets.
- Never store Aadhaar numbers.
- Never store OTP values in plaintext.
- Never store raw DigiLocker/UIDAI tokens without encryption.
- Never use production government integrations unless credentials and compliance status are explicit.
- Never run destructive commands without explicit user approval.
- Do not scrape government websites unless a future requirement explicitly approves scraping and legal review.

## Final Response Expectations

After completing work, answer concisely with:

- Summary of changes.
- Cross-layer impact.
- Verification run.
- Change log entry status.
- Known gaps or follow-ups.

Do not claim a feature is complete if frontend, backend, DB, tests, or configuration are knowingly out of sync.

