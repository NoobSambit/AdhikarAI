# Phase 1-2 Core Recommendation PRD Compliance Audit

Date: 2026-05-28
Agent: Codex
Scope: Phase 1 + Phase 2 core recommendation flow

## Executive Summary

Overall status: Partially implemented, with critical wiring and evidence gaps.

The repository has real data models, migrations, seed data, deterministic rule evaluation, profile/session persistence, and REST/WebSocket route surfaces for the Phase 1 and Phase 2 flow. However, the intended core recommendation path is not fully implemented as a PRD-compliant flow. Most importantly, semantic scheme search is not wired into the agent recommendation path, the search implementation does not use the FAISS library despite the FAISS naming, the LangGraph graph is a pass-through scaffold and is not called by `/agent/message`, and the tests for route-level behavior are heavily mocked.

Biggest risks:

- FAISS/semantic search is exposed only through `/schemes/search` and admin/CLI rebuild paths; the agent does not use it for vague needs such as "help for pregnant woman".
- The agent evaluates all active scheme rules every turn rather than using semantic candidates before eligibility matching.
- The Phase 2 LangGraph implementation is scaffold-only and not wired into the runtime message flow.
- Profile fact extraction is deterministic regex/string parsing, not LLM JSON extraction with repair and confirmation behavior.
- Test coverage does not prove real database-backed `/profile/match`, real `/agent/message`, real semantic search, or real end-to-end recommendation wiring.

Ready for browser testing: Partial. The API and frontend surfaces exist and can be smoke-tested, but recommendation-quality browser testing will hit non-PRD behavior, especially for vague need discovery.

Ready for production: No. The core recommendation flow is not strict-PRD compliant, and the highest-risk integrations lack meaningful tests.

## Audit Sources

PRDs read:

- `docs/prd/phase-1-foundation-eligibility-engine.md`
- `docs/prd/phase-2-agentic-conversation-layer.md`

Supporting docs inspected:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/overview.md`
- `docs/feature-map.md`
- `docs/prd-compliance-audit.md`
- `docs/product/scheme-eligibility.md`
- `docs/workflows/beneficiary-journey.md`
- `docs/agent-change-log.md`

Backend source inspected:

- `backend/app/api/routes/profile_match.py`
- `backend/app/api/routes/schemes.py`
- `backend/app/api/routes/admin_index.py`
- `backend/app/api/routes/admin_schemes.py`
- `backend/app/api/routes/admin_ingestion.py`
- `backend/app/api/routes/agent_sessions.py`
- `backend/app/api/routes/ws_chat.py`
- `backend/app/api/routes/profiles.py`
- `backend/app/api/routes/households.py`
- `backend/app/api/routes/document_check.py`
- `backend/app/services/eligibility/`
- `backend/app/services/search/`
- `backend/app/services/sessions/session_service.py`
- `backend/app/services/sessions/redis_store.py`
- `backend/app/services/profiles.py`
- `backend/app/services/schemes.py`
- `backend/app/services/households.py`
- `backend/app/services/documents/`
- `backend/app/services/seeds.py`
- `backend/app/agent/`
- `backend/app/schemas/`
- `backend/app/db/models/`
- `backend/app/db/migrations/`
- `backend/app/seeds/`
- `backend/.env.example`
- `backend/pyproject.toml`

Tests inspected:

- `backend/tests/unit/test_criteria_evaluator.py`
- `backend/tests/unit/test_near_miss.py`
- `backend/tests/unit/test_rule_validation.py`
- `backend/tests/unit/test_seed_data.py`
- `backend/tests/unit/test_phase2_agent_utilities.py`
- `backend/tests/unit/test_phase2_session_store.py`
- `backend/tests/unit/test_phase2_document_check.py`
- `backend/tests/integration/test_profile_match_api.py`
- `backend/tests/integration/test_faiss_search.py`
- `backend/tests/integration/test_phase2_agent_routes.py`
- `backend/tests/integration/test_admin_scheme_api.py`
- `backend/tests/integration/test_expiry_checker.py`
- `frontend/tests/e2e/beneficiary-pwa.spec.ts`
- `frontend/tests/e2e/helpers.ts`

## Status Legend

- Implemented: code exists, wired into real flow, and meaningfully tested.
- Partially implemented: some behavior exists but important PRD details are missing.
- Implemented but not wired: code exists but real user/API flow does not use it.
- Scaffold only: files/classes/routes exist but behavior is fake/stubbed/minimal.
- Not implemented: no meaningful implementation found.
- Unclear: needs manual confirmation.

## Requirement Matrix

| ID | PRD Requirement | Expected Behavior | Implementation Evidence | Wiring Evidence | Test Evidence | Status | Priority | Notes |
|---|---|---|---|---|---|---|---|---|
| R1 | Phase 1 scheme database models and migrations | Tenant-scoped scheme/rule/index/storage tables with required fields and constraints | `backend/app/db/models/scheme.py`, `backend/app/db/models/eligibility_rule.py`, `backend/app/db/migrations/versions/0001_phase_1_foundation.py` | Models are used by scheme, match, search, seed, and admin services | No live migration test in this audit; prior docs mention SQL generation only | Partially implemented | High | Schema is substantial, but runtime DB upgrade is not proved here. |
| R2 | Seed central scheme data | At least 25 central schemes with rules, documents, substitutes, source metadata | `backend/app/seeds/central_schemes.v1.json` has 26 schemes and document substitutes | `backend/app/services/seeds.py` loads into public org as active schemes | `backend/tests/unit/test_seed_data.py` | Partially implemented | Medium | Seed file has global `source_last_checked_at`, not per-record `source_last_checked_at` as PRD states. |
| R3 | Eligibility rule schema | JSONB supports base fields, custom criteria, exclusions, required documents, substitutes | `backend/app/schemas/scheme.py` | Admin create/update and seed loader validate against `EligibilityCriteriaModel` | `test_rule_validation.py`, `test_seed_data.py` | Partially implemented | High | Arbitrary custom fields are allowed; no check that every rule-required field is representable by profile schema. |
| R4 | Rule validation | Reject contradictions, invalid state codes, bad docs, bad exclusions, invalid operators | `backend/app/services/eligibility/validation.py` | Used by admin scheme service and seed loader | `test_rule_validation.py`, `test_admin_scheme_api.py` is mocked for duplicate path | Partially implemented | High | Validation exists, but API tests are shallow/mocked and do not prove full admin persistence behavior. |
| R5 | Experta/rule-based eligibility engine | Experta orchestrates deterministic criterion evaluation | `backend/app/services/eligibility/experta_engine.py`, `engine.py`, `criteria.py` | `/profile/match` calls `SchemeEligibilityEngine().run_evaluation()` | `test_criteria_evaluator.py`, `test_near_miss.py` | Partially implemented | High | Deterministic rule evaluation is real. Experta usage is mostly a wrapper; `run_evaluation()` bypasses actual Fact/Rule orchestration. |
| R6 | `/profile/match` active scheme matching | Load latest active rules, ignore inactive/expired schemes, return matches/near misses/incomplete | `backend/app/services/eligibility/matcher.py`, `backend/app/services/schemes.py` | `backend/app/api/routes/profile_match.py` calls `match_profile()` | Unit evaluator tests; `test_profile_match_api.py` monkeypatches the matcher | Partially implemented | Critical | Runtime path exists, but DB-backed API behavior is not meaningfully tested. |
| R7 | Matched, near-miss, incomplete, ineligible handling | Match if all known criteria pass; near miss only exactly one failure and no unknowns; incomplete when requested | `backend/app/services/eligibility/criteria.py` | `matcher.py` maps evaluations to response arrays | `test_near_miss.py`, `test_criteria_evaluator.py` | Implemented | High | Core classifier logic is present and tested at unit level. |
| R8 | Cross-scheme exclusions | Exclusions evaluated before normal criteria and never returned as near miss | `backend/app/services/eligibility/criteria.py` lines handling `existing_scheme_ids` | Used by `SchemeEligibilityEngine` via `CriterionEvaluator` | `test_criteria_evaluator.py` | Implemented | High | Behavior is deterministic and wired into evaluation. |
| R9 | Required documents and substitute guidance in match results | Scheme summaries include active required documents and substitutes | `backend/app/services/schemes.py`, `backend/app/schemas/match.py`, `backend/app/services/documents/` | `scheme_summary()` includes `required_documents`; document check route uses active rule | `test_phase2_document_check.py`; no match-response document test | Partially implemented | Medium | Data is carried, but result formatting/application guidance is minimal and not tested through `/profile/match`. |
| R10 | FAISS index build | Build idempotent semantic index over active scheme text and metadata with content hash | `backend/app/services/search/faiss_index.py`, `backend/app/db/models/scheme.py` | Admin route `/admin/index/rebuild` and CLI `index rebuild` call rebuild | `test_faiss_search.py` only tests hash embedding determinism | Partially implemented | Critical | No `faiss` import found. Index is JSON vectors plus dot product, not a FAISS index. Rule-derived keywords are not included. |
| R11 | `/schemes/search` semantic search | Return top schemes by semantic similarity; rebuild once if missing; fallback text if rebuild fails | `backend/app/api/routes/schemes.py`, `backend/app/services/search/faiss_index.py` | Route calls `search_schemes()`; fallback `ILIKE` exists | No endpoint/rebuild/fallback integration test | Partially implemented | Critical | Missing-index path falls directly to text search; it does not rebuild once. Search also does not filter `valid_until`. |
| R12 | Admin/CLI index rebuild support | Admin endpoint and Typer command rebuild index using same service | `backend/app/api/routes/admin_index.py`, `backend/app/cli/main.py` | Both call `rebuild_faiss_index()` | No direct tests | Partially implemented | Medium | Publish does not trigger async rebuild despite PRD; rebuild itself is not real FAISS. |
| R13 | Agent session creation and persistence | Create/resume session, profile, household; Redis key with 30-day TTL; Postgres metadata | `backend/app/services/sessions/session_service.py`, `redis_store.py`, models/migration 0002 | `/agent/sessions` route calls `get_or_create_session()` | `test_phase2_session_store.py`; `test_phase2_agent_routes.py` mocks service | Partially implemented | High | Core code exists. Tests do not prove DB-backed session create/resume. TTL uses hard-coded 30 days rather than settings value. |
| R14 | Profile fact extraction from natural language | LLM JSON extraction with confidence, repair retry, confirmation handling | `backend/app/agent/extraction.py` | `/agent/message` uses `DeterministicFactExtractor().extract()` | `test_phase2_agent_utilities.py` | Partially implemented | Critical | Extraction is deterministic regex/string parsing. No LLM, no JSON repair prompt, and limited field coverage. |
| R15 | Confidence thresholds | >=0.75 merge, 0.5-0.75 confirmation question, <0.5 no profile update | `_merge_fact()` in `session_service.py`, `ExtractedFact.confidence` | Facts below 0.75 are ignored by `_merge_fact()` | Utility tests verify high-confidence extraction only | Partially implemented | High | Confirmation for 0.5-0.75 facts is not implemented in runtime flow. |
| R16 | Profile completeness | Deterministic weighted completeness over relevant fields from top 20 candidate schemes | `backend/app/agent/completeness.py` | `/agent/message` computes completeness from all active scheme rules | `test_phase2_agent_utilities.py` | Partially implemented | High | Formula is close, but "candidate" rules are not semantic/top candidates and hard-failed schemes are not removed. |
| R17 | Household member handling | Multiple members; switch active member from natural language; shared household fields | `session_service.py`, `households.py`, `schemas/agent.py`, models/migration 0002 | `/agent/message` creates/switches simple relationship members; member APIs exist | Utility test only checks life-event object; no route/service integration test | Partially implemented | Medium | Basic relation detection exists, but shared household field behavior and robust member switching are incomplete. |
| R18 | Life event detection | Marriage/child birth update profile/member and re-run eligibility | `backend/app/agent/life_events.py`, `session_service.py` | `/agent/message` applies life-event patches and creates child member | `test_phase2_agent_utilities.py` | Partially implemented | Medium | Regex-only detection; life-event profile patch is persisted as generic profile update; no DB-backed conversation test. |
| R19 | Agent asks one question and avoids known facts | Select one highest-value missing field, skip asked/known fields | `backend/app/agent/question_selection.py`, `session_service.py` | `/agent/message` calls selector when not returning result | `test_phase2_agent_utilities.py` | Partially implemented | High | One-question behavior is present. Expected information-gain is simplified and not based on semantic candidates. |
| R20 | Agent runs eligibility and returns payload | Run Phase 1 matching when enough info exists or max questions reached; return matched/near-miss schemes | `_run_match()` and result branch in `session_service.py` | `/agent/message` calls internal `match_profile()` directly every turn | `test_phase2_agent_routes.py` mocks `handle_chat_turn`; no real service test | Partially implemented | Critical | Internal matcher is wired, but result threshold behavior is not integration-tested and no FAISS candidate retrieval precedes matching. |
| R21 | Profile/session state persistence after agent turn | Store conversation messages, profile facts, asked fields, session expiry, last match snapshot | `session_service.py`, `profiles.py`, models/migration 0002 | `/agent/message` persists messages/profile/session; PATCH profile stores `last_match_snapshot` | No real `/agent/message` persistence test | Partially implemented | High | Conversation updates do not set `profile.last_match_snapshot`; PATCH profile does. |
| R22 | LangGraph implementation | Real graph nodes implement load, extract, life event, candidate search, match, format, persist | `backend/app/agent/graph.py` | No runtime usage found; `build_agent_graph()` is not called | No graph tests | Scaffold only | Critical | Graph nodes are pass-through functions. The real runtime is service-code based. |
| R23 | WebSocket chat | JSON-only WebSocket, streaming chunks for LLM text, complete result payloads | `backend/app/api/routes/ws_chat.py` | `/ws/chat` calls `handle_chat_turn()` and sends one JSON response | No WebSocket test in audited set | Partially implemented | Medium | JSON handling exists; streaming chunks are not implemented. |
| R24 | FAISS integrated into agent recommendations | Use semantic retrieval for vague needs/candidate schemes before deterministic eligibility | No implementation found in agent/session service | `rg` shows `search_schemes()` only in `routes/schemes.py`; agent path imports `active_scheme_rules()` and `match_profile()` | No tests | Not implemented | Critical | This is the key gap in the intended core flow. |
| R25 | Tests prove real core recommendation wiring | Meaningful tests for profile extraction -> search/candidates -> rule match -> response -> persistence | Tests listed below | Existing route tests monkeypatch key services | Narrow test run passed 24 tests | Partially implemented | Critical | Current tests prove utilities more than runtime integration. |

## Real Flow Analysis

### `/profile/match`

Actual current runtime flow:

```txt
POST /profile/match
-> check_guest_limit(organisation_id, request_id)
-> services.eligibility.matcher.match_profile()
-> services.schemes.active_scheme_rules()
-> load every active scheme for organisation where is_active=true, status='active', valid_until is null or future
-> latest active rule per scheme
-> SchemeEligibilityEngine.run_evaluation()
-> EligibilityEngine -> CriterionEvaluator
-> build matched_schemes, near_miss_schemes, optional incomplete_schemes
-> return MatchProfileResponse
```

Comparison to intended PRD flow:

- Deterministic rule matching is present.
- Cross-scheme exclusions are evaluated before normal criteria.
- Near-miss and incomplete handling exist.
- No semantic search or FAISS candidate narrowing happens in `/profile/match`; it evaluates all active schemes.
- API test coverage does not prove this DB-backed runtime path because `test_profile_match_api.py` monkeypatches `match_profile()`.

### `/schemes/search`

Actual current runtime flow:

```txt
GET /schemes/search?organisation_id=...&q=...
-> services.search.faiss_index.search_schemes()
-> find active FaissIndex metadata row named schemes_active
-> if metadata storage_path exists:
   -> read JSON payload from disk
   -> embed query
   -> dot-product query vector against stored vectors
   -> return search_mode='faiss'
-> otherwise or on exception:
   -> fallback_text_search() with ILIKE over name/description/plain_language_summary
   -> return search_mode='fallback_text'
```

Comparison to intended PRD flow:

- Route and fallback text search exist.
- Missing-index path does not rebuild once before fallback.
- The implementation does not import or call the FAISS library.
- Index payload is a JSON file of vectors, not a FAISS index file.
- The search text includes name, description, plain-language summary, benefit type, benefit amount, and ministry, but rule-derived keywords are not passed in rebuild.
- Search filters active/status but does not filter `valid_until`.

### `/agent/sessions`

Actual current runtime flow:

```txt
POST /agent/sessions
-> ensure organisation exists
-> if session row exists and not expired:
   -> rebuild state from PostgreSQL
   -> write Redis state
   -> return remembered greeting
-> else:
   -> create Household
   -> create Profile
   -> create ConversationSession
   -> write Redis state
   -> return new greeting
```

Comparison to intended PRD flow:

- PostgreSQL conversation metadata, profile, household, and Redis state are present.
- Redis key format matches `session:{organisation_id}:{session_id}`.
- TTL is 30 days, but it is hard-coded in `session_service.py` instead of using `SESSION_TTL_SECONDS` from settings.
- Resume behavior rebuilds from PostgreSQL when a DB row exists; it does not first rely on Redis state as the PRD describes.
- Tests are either memory-store only or mocked route tests.

### `/agent/message`

Actual current runtime flow:

```txt
POST /agent/message
-> resolve organisation from request or session
-> load AgentState from Redis or PostgreSQL
-> append/persist user ConversationMessage
-> DeterministicFactExtractor extracts simple regex/string facts
-> detect_life_event() with simple string matching
-> create/switch basic household member when relation words are detected
-> merge facts with confidence >= 0.75
-> load all active scheme rules
-> compute profile completeness over those rules
-> run match_profile(... include_incomplete=true, limit=10)
-> if completeness >= 75 and result condition passes, or max question count reached:
   -> return result payload
   -> insert ZeroMatchEvent if no matches/near misses
-> else:
   -> select_next_question() from missing fields in all active rules
   -> append asked_field
   -> return one question
-> persist profile, session row, assistant ConversationMessage, Redis state
```

Comparison to intended PRD flow:

- It does extract and persist some structured profile facts.
- It asks one question per non-result turn.
- It does call the internal Phase 1 matcher directly.
- It does not use LangGraph runtime.
- It does not use LLM JSON extraction or JSON repair.
- It does not implement medium-confidence confirmation.
- It does not use FAISS/semantic retrieval for candidate schemes.
- It runs eligibility every turn, not only when enough information exists.
- It does not store `last_match_snapshot` for conversation-driven profile updates.

## FAISS Integration Finding

What FAISS was intended to do:

- Phase 1 intended semantic search over active scheme descriptions and summaries, returning top schemes such as PMMVY/JSY for "help for pregnant woman first child".
- The broader core recommendation flow expects semantic scheme search/FAISS to help retrieve relevant schemes where needed before deterministic rule matching.
- Phase 2 completeness is intended to operate over top candidate active schemes, not an arbitrary all-schemes set.

What FAISS currently does:

- `/schemes/search` is the only public recommendation-adjacent route that calls `search_schemes()`.
- `/admin/index/rebuild` and the CLI `index rebuild` call `rebuild_faiss_index()`.
- No `faiss` import or FAISS index object usage was found in `backend/app` or `backend/tests`.
- The index is stored as JSON vectors and scored with a dot product in Python.
- If the index is missing, search falls back to text search. It does not rebuild once before fallback.

Whether it is integrated into agent recommendations:

- No. `search_schemes()` is not imported or called from `backend/app/services/sessions/session_service.py` or `backend/app/agent/`.
- The agent uses `active_scheme_rules()` and `match_profile()` over all active schemes.

Direct answers:

- Is FAISS used when the user asks a vague need like "help for pregnant woman"? No.
- Is FAISS used to select candidate schemes before rule matching? No.
- Or is FAISS only exposed as a separate `/schemes/search` endpoint? Yes, plus admin/CLI rebuild support.

Impact on recommendation quality:

- Vague user needs are not used to retrieve semantically relevant schemes.
- A message like "help for pregnant woman" is likely to extract only gender from deterministic parsing. Pregnancy-specific custom criteria such as `is_pregnant_or_lactating` remain unknown unless explicitly supplied in structured form or later collected.
- Question selection is diluted across all active schemes instead of focusing on pregnancy/maternity candidates.
- Recommendation quality will look inconsistent in browser tests for real beneficiary language, even when rule evaluation itself is deterministic.

## Agent Behavior Finding

How facts are extracted:

- Facts are extracted by `DeterministicFactExtractor` in `backend/app/agent/extraction.py`.
- It recognizes a limited set of English words, state aliases, age/income/land regexes, relationship words, and a special `profile_facts:` structured message format.
- It blocks messages containing sensitive patterns such as Aadhaar, OTP, or bank account text by returning no facts.

Whether LLM extraction is actually used:

- No LLM extraction is used in the runtime `/agent/message` path.
- No `BaseChatModel`, Ollama/Groq chat call, JSON repair prompt, or extraction prompt contract was found in the agent runtime.

How profile completeness works:

- `compute_profile_completeness()` uses deterministic weights for base fields and rule-referenced fields.
- It takes the first 20 rules from the supplied active-rule list.
- The supplied rules come from all active schemes, not semantically retrieved or hard-failure-pruned candidates.

When matching runs:

- `/agent/message` runs `_run_match()` every turn with `include_incomplete=true`.
- The response becomes a result only if completeness is at least 75 with a qualifying result condition, or after `agent_max_questions_before_result`.

What kind of response is returned:

- Question response: short text plus `payload={"asked_field": ...}`.
- Result response: short summary plus full `match_snapshot` containing matched, near-miss, incomplete, evaluated count, and request ID.
- Result text is minimal. Scheme document lists are in payload, but application guidance is not richly formatted in the backend result.

Whether the agent is truly LangGraph-based or mostly service-code based:

- Mostly service-code based.
- `backend/app/agent/graph.py` defines a `StateGraph`, but every node is a pass-through function and `build_agent_graph()` is not called from runtime services.
- The actual conversation logic lives in `backend/app/services/sessions/session_service.py`.

## Eligibility Engine Finding

Whether matching is deterministic and rule-based:

- Yes. `CriterionEvaluator` deterministically evaluates profile fields, custom criteria, and exclusions against `EligibilityCriteriaModel`.

Whether near-miss logic is correct:

- Mostly yes for the implemented field types. It returns near miss only when exactly one criterion failed and no criteria are unknown.
- Cross-scheme exclusions return ineligible before normal criteria and are not near misses.

Whether incomplete/unknown criteria are handled:

- Yes at evaluator and matcher level. Unknown fields produce `status="incomplete"`, and `/profile/match` includes incomplete schemes only when `include_incomplete=true`.

Whether documents/substitutes are carried into results:

- Yes, `scheme_summary()` carries `required_documents` from the active rule into matched/near-miss/incomplete scheme summaries.
- Document sufficiency and substitute matching exist in `backend/app/services/documents/document_matcher.py`.
- Backend match result formatting does not add detailed application steps; the frontend currently adds generic application steps.

Important caveat:

- The Experta class exists but is not meaningfully used as an expert-system graph. It delegates directly to pure Python evaluation.

## Tests Reviewed

Backend unit tests:

- `backend/tests/unit/test_criteria_evaluator.py`: proves cross-scheme exclusion, unknown criterion classification, and one custom `lte` criterion at unit level.
- `backend/tests/unit/test_near_miss.py`: proves exactly-one-failure near miss and two-failure ineligible logic.
- `backend/tests/unit/test_rule_validation.py`: proves min/max age contradiction, substitute instruction validation, broken exclusion, and invalid state code.
- `backend/tests/unit/test_seed_data.py`: proves at least 25 seed schemes, required documents, global source timestamp, and rule validation.
- `backend/tests/unit/test_phase2_agent_utilities.py`: proves question skipping, one-question text, completeness calculation, deterministic extraction, structured `profile_facts:` extraction, sensitive structured blocking, and simple life event detection.
- `backend/tests/unit/test_phase2_session_store.py`: proves `memory://` session store uses 30-day TTL and state version.
- `backend/tests/unit/test_phase2_document_check.py`: proves document alias matching, substitute matching, and missing-document guidance.

Backend integration tests:

- `backend/tests/integration/test_profile_match_api.py`: route-level test, but it monkeypatches `match_profile()`. It does not prove database-backed matching.
- `backend/tests/integration/test_faiss_search.py`: tests only `HashEmbeddingProvider` determinism. It does not test index rebuild, `/schemes/search`, fallback behavior, or FAISS.
- `backend/tests/integration/test_phase2_agent_routes.py`: route-level test, but it monkeypatches `get_or_create_session()`, `handle_chat_turn()`, and `get_session_state()`. It does not prove real conversation behavior.
- `backend/tests/integration/test_admin_scheme_api.py`: admin token and mocked duplicate path. It does not prove CRUD persistence.
- `backend/tests/integration/test_expiry_checker.py`: fake DB test for expiry status mutation. Useful but not DB-backed.

Frontend tests:

- `frontend/tests/e2e/beneficiary-pwa.spec.ts`: typed-flow test expects `/agent/message` response and visible UI, but requires a live backend and was not run in this audit. It checks broad UI response shape, not semantic retrieval or deterministic eligibility correctness.

Missing tests:

- DB-backed `/profile/match` with seed schemes and real active rules.
- `/schemes/search?q=pregnant woman` proving PMMVY/JSY appear.
- Missing-index rebuild-once behavior.
- Real FAISS index file creation/search.
- `/agent/message` real flow from session creation through persistence and matching.
- Agent use of semantic search candidate schemes.
- Medium-confidence confirmation question behavior.
- LangGraph graph execution.
- WebSocket chat behavior.

Weak/static/over-mocked tests:

- `test_profile_match_api.py` does not exercise the matcher.
- `test_phase2_agent_routes.py` does not exercise session service behavior.
- `test_faiss_search.py` does not exercise search, endpoint, or FAISS.
- Frontend E2E checks response type/UI visibility but not recommendation correctness.

Tests run during this audit:

```txt
cd backend && uv run --extra test pytest \
  tests/unit/test_criteria_evaluator.py \
  tests/unit/test_near_miss.py \
  tests/unit/test_rule_validation.py \
  tests/unit/test_phase2_agent_utilities.py \
  tests/unit/test_phase2_session_store.py \
  tests/unit/test_phase2_document_check.py \
  tests/unit/test_seed_data.py \
  tests/integration/test_profile_match_api.py \
  tests/integration/test_faiss_search.py \
  tests/integration/test_phase2_agent_routes.py
```

Result: 24 passed in 0.69s.

## Major Gaps

1. FAISS is not wired into the agent recommendation path.
   - Why it matters: vague need discovery is a core product promise; the agent cannot use semantic search to focus maternity, pension, farmer, or housing recommendations.
   - Affected files: `backend/app/services/sessions/session_service.py`, `backend/app/services/search/faiss_index.py`, `backend/app/agent/completeness.py`, `backend/app/agent/question_selection.py`.
   - Suggested fix direction: add a candidate retrieval step before completeness/question selection and matching, using semantic search for initial vague needs and deterministic rule pruning after facts are known.
   - Blocks browser testing: Yes for recommendation-quality testing; no for route/UI smoke testing.

2. The search implementation is not actual FAISS.
   - Why it matters: PRD and stack require FAISS; current implementation is JSON vector storage plus Python dot-product scoring, which will not scale or behave like FAISS.
   - Affected files: `backend/app/services/search/faiss_index.py`, `backend/tests/integration/test_faiss_search.py`.
   - Suggested fix direction: use `faiss-cpu` index classes, persist/read actual FAISS index files plus ID mapping, and keep text fallback as a tested fallback.
   - Blocks browser testing: Partial. Browser can call search, but search quality/performance claims are not valid.

3. LangGraph is scaffold-only and not used by `/agent/message`.
   - Why it matters: Phase 2 explicitly requires LangGraph for conversation graph behavior. Current node names exist, but all nodes pass through and runtime logic is centralized in service code.
   - Affected files: `backend/app/agent/graph.py`, `backend/app/services/sessions/session_service.py`.
   - Suggested fix direction: move the actual turn steps into graph nodes or have `handle_chat_turn()` invoke the compiled graph with real node implementations.
   - Blocks browser testing: No for smoke testing; yes for claiming Phase 2 PRD compliance.

4. LLM fact extraction and confirmation behavior are missing.
   - Why it matters: low-literacy natural language input will exceed the regex extractor quickly, especially for pregnancy, disability, BPL, household income, and custom scheme facts.
   - Affected files: `backend/app/agent/extraction.py`, `backend/app/services/sessions/session_service.py`, `backend/app/core/config.py`.
   - Suggested fix direction: implement the PRD JSON extraction contract with configured Ollama/Groq providers, one repair retry, medium-confidence confirmation, and deterministic fallback for simple structured input.
   - Blocks browser testing: Yes for realistic beneficiary language testing.

5. Tests do not prove real core wiring.
   - Why it matters: the strict audit standard requires code, wiring, and meaningful tests. Current route tests monkeypatch the most important services.
   - Affected files: `backend/tests/integration/test_profile_match_api.py`, `backend/tests/integration/test_phase2_agent_routes.py`, `backend/tests/integration/test_faiss_search.py`, `frontend/tests/e2e/beneficiary-pwa.spec.ts`.
   - Suggested fix direction: add DB-backed integration fixtures for seed data, match API, search API, session create/message, persistence, and candidate selection.
   - Blocks browser testing: Partial. Smoke testing can continue, but failures will be hard to diagnose without backend integration tests.

6. Profile match snapshots are not persisted for conversation updates.
   - Why it matters: PRD says profile update flows should re-run matching and store `last_match_snapshot`; `/agent/message` re-runs matching but does not set it.
   - Affected files: `backend/app/services/sessions/session_service.py`, `backend/app/services/profiles.py`, `backend/app/db/models/profile.py`.
   - Suggested fix direction: persist the match snapshot on conversation profile updates, matching `patch_profile()` behavior.
   - Blocks browser testing: No for basic UI testing; yes for session/resume correctness testing.

7. Candidate/question selection is not PRD-grade.
   - Why it matters: the agent may ask broad high-weight questions driven by all schemes rather than the user's actual stated need.
   - Affected files: `backend/app/agent/question_selection.py`, `backend/app/agent/completeness.py`, `backend/app/services/sessions/session_service.py`.
   - Suggested fix direction: derive candidate schemes from semantic search plus known hard-failure pruning; compute completeness and information gain against that candidate set.
   - Blocks browser testing: Yes for evaluating whether conversations converge in <=6 questions.

## Production Readiness

Ready for production: no.

Reasons:

- Core semantic retrieval is not integrated into recommendations.
- The search implementation is not true FAISS.
- LangGraph is scaffold-only.
- LLM extraction and confidence-confirmation behavior are missing.
- Tests do not prove real runtime wiring.

Ready for serious browser testing: partial.

Explanation:

- Ready for route/UI smoke testing with a seeded local backend.
- Not ready for serious recommendation-quality testing or PRD sign-off because vague need inputs and semantic candidate selection are not implemented in the agent path.

## Recommended Fix Plan

1. Critical fixes
   - Replace JSON-vector "faiss" storage with real FAISS index build/search and tested ID mapping.
   - Wire semantic candidate retrieval into the agent recommendation flow before completeness, question selection, and matching.
   - Add DB-backed integration tests for `/profile/match`, `/schemes/search`, `/agent/sessions`, and `/agent/message`.
   - Replace/pass through the LangGraph scaffold with real graph node execution or explicitly refactor runtime to call the compiled graph.

2. High-priority fixes
   - Implement LLM extraction contract with JSON repair and deterministic fallback.
   - Add medium-confidence confirmation behavior.
   - Persist `last_match_snapshot` during conversation-driven profile updates.
   - Improve candidate pruning for question selection and completeness.
   - Add real WebSocket chat tests.

3. Medium-priority fixes
   - Add integration tests for admin scheme create/update/publish/archive without monkeypatching.
   - Add tests for document lists in `/profile/match` result payloads.
   - Add test coverage for `valid_until` filtering in semantic search.
   - Add tests for household member switching and shared household fields.

4. Later improvements
   - Add benchmark coverage for 500 active schemes.
   - Add richer backend result formatting for document checklist, substitutes, and application guidance.
   - Add multilingual extraction coverage after Phase 3 translation is in the loop.
   - Add browser E2E assertions that recommendation results match seeded expected schemes for representative profiles.

## Open Questions

- Should semantic retrieval always precede eligibility matching, or only when the user message contains a vague need that does not map to enough structured facts?
- Should `/profile/match` remain all-active-schemes deterministic matching, while the agent uses a separate candidate-selection service?
- What is the expected behavior for custom criteria that the profile schema cannot represent directly?
- Should deterministic structured `profile_facts:` input remain as a supported developer/testing path after LLM extraction is added?
- Should the agent store every match snapshot, only result-turn snapshots, or the latest snapshot after every turn?
- Is the product willing to call the current JSON-vector implementation "semantic search" temporarily, or must Phase 1 compliance require real FAISS before further browser QA?

## Appendix: Evidence

Useful file references:

- `backend/app/api/routes/profile_match.py`: `/profile/match` route calls `match_profile()`.
- `backend/app/services/eligibility/matcher.py`: loads active scheme rules and maps evaluation results.
- `backend/app/services/eligibility/criteria.py`: deterministic criterion, exclusion, near-miss, and incomplete logic.
- `backend/app/services/eligibility/experta_engine.py`: Experta wrapper delegates to pure Python `EligibilityEngine`.
- `backend/app/services/schemes.py`: active scheme filtering, latest rule loading, scheme summaries.
- `backend/app/api/routes/schemes.py`: `/schemes/search` route calls `search_schemes()`.
- `backend/app/services/search/faiss_index.py`: JSON-vector index build/search and fallback text search.
- `backend/app/services/search/embeddings.py`: sentence-transformers provider with hash fallback.
- `backend/app/api/routes/admin_index.py`: admin index rebuild endpoint.
- `backend/app/cli/main.py`: Typer `scheme`, `index`, and `expiry-check` commands.
- `backend/app/services/sessions/session_service.py`: actual `/agent/message` runtime flow.
- `backend/app/agent/graph.py`: pass-through LangGraph scaffold.
- `backend/app/agent/extraction.py`: deterministic extractor.
- `backend/app/agent/completeness.py`: deterministic weighted completeness.
- `backend/app/agent/question_selection.py`: one-question selector.
- `backend/app/agent/life_events.py`: simple life event detector.
- `backend/app/services/profiles.py`: PATCH profile re-runs match and stores `last_match_snapshot`.
- `backend/app/db/migrations/versions/0001_phase_1_foundation.py`: Phase 1 tables.
- `backend/app/db/migrations/versions/0002_phase_2_agentic_conversation.py`: Phase 2 profile/session tables.
- `backend/app/seeds/central_schemes.v1.json`: 26 seed schemes.
- `frontend/lib/api.ts`: frontend calls `/agent/sessions` and `/agent/message`.
- `frontend/tests/e2e/beneficiary-pwa.spec.ts`: browser typed-flow smoke test.

Commands used:

```sh
sed -n '1,260p' AGENTS.md
sed -n '1,260p' docs/prd/phase-1-foundation-eligibility-engine.md
sed -n '261,620p' docs/prd/phase-1-foundation-eligibility-engine.md
sed -n '621,1040p' docs/prd/phase-1-foundation-eligibility-engine.md
sed -n '1041,1500p' docs/prd/phase-1-foundation-eligibility-engine.md
sed -n '1,300p' docs/prd/phase-2-agentic-conversation-layer.md
sed -n '301,700p' docs/prd/phase-2-agentic-conversation-layer.md
sed -n '701,1100p' docs/prd/phase-2-agentic-conversation-layer.md
sed -n '1,320p' docs/architecture.md
sed -n '1,220p' docs/overview.md
sed -n '1,220p' docs/feature-map.md
sed -n '1,220p' docs/prd-compliance-audit.md
sed -n '1,260p' docs/product/scheme-eligibility.md
sed -n '1,240p' docs/workflows/beneficiary-journey.md
sed -n '1,120p' docs/agent-change-log.md
sed -n '700,830p' docs/agent-change-log.md
rg "FAISS|faiss|semantic|embedding|search" docs/prd backend docs -n
rg "match_profile|SchemeEligibilityEngine|near_miss|incomplete" backend/app backend/tests -n
rg "LangGraph|StateGraph|extract_profile|profile_completeness|asked_fields" backend/app backend/tests docs/prd -n
rg "profile/match|schemes/search|agent/message|agent/sessions" backend/app docs -n
rg "import faiss|faiss\." backend/app backend/tests -n
rg "search_schemes|rebuild_faiss_index|scheme_embedding_text|active_search_schemes" backend/app/services/sessions backend/app/agent backend/app/api -n
rg "DeterministicFactExtractor|BaseChatModel|llm|Groq|Ollama|extract_profile_facts|pending_confirmation|needs_confirmation" backend/app/agent backend/app/services/sessions backend/tests -n
rg "last_match_snapshot|ProfileEvent|ZeroMatchEvent|turn_count_since_result|agent_max_questions" backend/app/services/sessions backend/app/services/profiles.py backend/tests -n
rg --files backend/app/services/eligibility backend/app/services/search backend/app/services/sessions backend/app/agent backend/app/api/routes backend/app/schemas backend/app/db/models backend/app/db/migrations backend/app/seeds backend/tests frontend/tests docs | sort
git status --short
cd backend && uv run --extra test pytest tests/unit/test_criteria_evaluator.py tests/unit/test_near_miss.py tests/unit/test_rule_validation.py tests/unit/test_phase2_agent_utilities.py tests/unit/test_phase2_session_store.py tests/unit/test_phase2_document_check.py tests/unit/test_seed_data.py tests/integration/test_profile_match_api.py tests/integration/test_faiss_search.py tests/integration/test_phase2_agent_routes.py
```

Verification command result:

```txt
24 passed in 0.69s
```
