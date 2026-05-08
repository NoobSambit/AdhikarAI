# AdhikarAI Agent Change Log

## 2026-05-08 22:21 IST - Add Shared Agent Instructions

- Request: Create a project agent instruction file compatible with Codex, Gemini CLI, and Antigravity, including cross-layer change discipline and a change tracking system.
- Agent: Codex.
- Changed files:
  - `AGENTS.md`
  - `docs/agent-change-log.md`
- Cross-layer impact:
  - Frontend: not impacted
  - Backend: not impacted
  - Database: not impacted
  - UI/UX: not impacted
  - Tests: not impacted
  - Config/Env: not impacted
  - Docs: changed
- Schema/migration notes: not needed; documentation-only change.
- API contract notes: unchanged; documentation-only change.
- Verification:
  - `date '+%Y-%m-%d %H:%M %Z'` succeeded to timestamp the log entry.
- Follow-ups:
  - Configure Gemini CLI to load `AGENTS.md` directly, or symlink this file to `GEMINI.md` if the local Gemini setup cannot load custom context filenames.

