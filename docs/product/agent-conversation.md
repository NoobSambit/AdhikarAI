# Agent Conversation

The AdhikarAI conversational agent is a constrained welfare-scheme intake agent. It is not a general-purpose chatbot. Its only job is to gather enough information from the beneficiary to match eligible government schemes.

---

## Design Constraints

- **One question at a time**: The agent always asks exactly one clarifying question per turn.
- **No re-asking**: Once a field has been answered with sufficient confidence, it is not asked again.
- **Hard stop**: After `AGENT_MAX_QUESTIONS_BEFORE_RESULT` questions (default 8), the agent forces a result even if the profile is incomplete.
- **Sensitive field guard**: The agent never asks for Aadhaar numbers, OTPs, bank account numbers, or raw identity document numbers.
- **Scoped to welfare**: The agent redirects off-topic messages back to welfare scheme discovery.

---

## LangGraph Graph

**File**: `app/agent/graph.py`

The agent is implemented as a LangGraph `StateGraph` with 10 nodes:

```
START
  └── load_session
      └── extract_profile_facts
          └── detect_life_event
              └── merge_profile_update
                  └── compute_candidate_schemes
                      └── compute_profile_completeness
                          └── should_match_or_ask
                              ├── (completeness >= 75%) → run_eligibility_match → format_result
                              └── (completeness < 75%)  → select_next_question
                                  └── persist_session → END
```

---

## Agent State

**File**: `app/agent/state.py`

The agent state (`AdhikarAgentState`) tracks:

| Field | Type | Description |
|---|---|---|
| `session_id` | str | Conversation session identifier |
| `organisation_id` | UUID | Organisation scope |
| `profile_facts` | dict | Extracted profile fields from conversation |
| `asked_fields` | list[str] | Fields already asked |
| `profile_completeness` | int | 0–100 completeness score |
| `matched_schemes` | list | Eligible matched schemes |
| `near_miss_schemes` | list | Near-miss schemes |
| `agent_question` | str | The next question to ask |
| `life_event` | str or None | Detected life event (e.g., "widow", "new_baby") |
| `turn_count` | int | Number of turns in this session |

---

## Profile Fact Extraction

**File**: `app/agent/extraction.py`

Each user message is passed to the LLM with a structured prompt that asks it to extract profile fields in JSON format.

Supported fields extracted from free text:
- `age`, `gender`, `state_code`, `district`
- `caste`, `bpl_card`, `disability`
- `annual_income_inr`, `land_hectares`
- `marital_status`, `education_level`
- `occupation`, `household_size`

Sensitive field guard: if the user's message contains patterns matching Aadhaar numbers, OTPs, or bank accounts, those are stripped before LLM processing.

---

## Life Event Detection

**File**: `app/agent/life_events.py`

The agent detects life events from context that can shortcut the question flow:
- "My husband died recently" → `life_event: widow`
- "I just had a baby" → `life_event: new_mother`
- "I lost my job" → `life_event: unemployed`
- "I want to start a business" → `life_event: entrepreneur`

Life events pre-fill relevant profile fields.

---

## Profile Completeness

**File**: `app/agent/completeness.py`

Profile completeness is a 0–100 integer score calculated by how many required fields for the candidate schemes have been answered.

- Fields required by at least one candidate scheme count more.
- Fields already answered don't count toward the remaining score.
- When completeness ≥ 75%, the agent triggers eligibility matching instead of asking another question.

---

## Question Selection

**File**: `app/agent/question_selection.py`

When the agent decides to ask a question, it picks the next field to ask about based on:
1. Which fields are required by the most candidate schemes.
2. Which fields haven't been asked yet.
3. Which field would most reduce uncertainty.

Questions are formulated in the user's preferred language (the agent response is in English; translation happens in the voice pipeline or is handled by the response translation step).

---

## Result Formatting

**File**: `app/agent/result_formatter.py`

When eligibility matching completes, the agent formats the result as a structured response:

```json
{
  "type": "result",
  "content": "Based on your information, you are eligible for the following schemes:",
  "payload": {
    "matched_schemes": [...],
    "near_miss_schemes": [...],
    "profile_completeness": 82
  }
}
```

---

## Session Storage

**File**: `app/services/sessions/redis_store.py`

Conversation sessions are stored in Redis:
- Key: `session:{organisation_id}:{session_id}`
- Value: JSON-serialized agent state
- TTL: `SESSION_TTL_SECONDS` (default 30 days)

In addition to Redis, session metadata (start time, active profile, turn count) is persisted to `conversation_sessions` in PostgreSQL. Each user message and agent response is stored in `conversation_messages`.

---

## Chat Turn Handler

**File**: `app/services/sessions/session_service.py`

`handle_chat_turn(input, db)` is the main entry point called by the REST and WebSocket routes, and by the voice pipeline. It:

1. Loads or creates a Redis session.
2. Runs the LangGraph agent graph.
3. Persists the conversation message to PostgreSQL.
4. Returns a `ChatOutputModel`.

---

## REST and WebSocket APIs

| Route | Description |
|---|---|
| `POST /agent/sessions` | Create a new conversation session |
| `POST /agent/message` | Send a typed message; get an agent response |
| `WS /ws/chat` | WebSocket chat (text messages) |
| `WS /ws/voice` | WebSocket voice (binary audio chunks) |

---

## LLM Providers

| Provider | Variable | Notes |
|---|---|---|
| Ollama (local) | `LLM_PROVIDER=ollama` | `llama3.1:8b` primary, `qwen2.5:7b` fallback |
| Groq (hosted) | `LLM_PROVIDER=groq` | `llama-3.3-70b-versatile` primary; requires `GROQ_API_KEY` |

---

## Developer Chat UI

**Route**: `/dev-chat`
**Component**: `frontend/components/dev-chat/ChatWindow.tsx`

A development-only chat UI that sends messages directly to the agent API and shows raw JSON debug state alongside the conversation. Not the production beneficiary UX.

---

## Known Limitations

- The LangGraph graph node implementations (`pass_through`) are stubs — the real logic lives in the session service. The graph is not fully wired to call the session service node by node.
- Real LLM behavior is tested manually, not in automated CI tests (LLM responses are mocked in unit tests).
- Adversarial conversation tests (checking that the sensitive field guard holds under attack) are listed as a gap in the compliance audit.
- Re-ask prevention relies on the `asked_fields` list in Redis; if Redis is cleared, questions may repeat.
