# AdhikarAI PRD - Phase 2: Agentic Conversation Layer

## Phase Summary

Phase 2 wraps the Phase 1 eligibility engine with a LangGraph-based multi-turn text agent. The agent builds a structured user profile through conversation, asks only the next highest-value question, persists session state in Redis for 30 days, supports household members, detects profile-changing life events, exposes profile update APIs, and streams messages over WebSocket.

Phase 2 includes a simple Next.js text UI for developer testing only. It is not the production low-literacy PWA; that arrives in Phase 4.

Primary user: a rural Indian beneficiary or assisting NGO/CSC operator using text during development.

Key product promise: the agent is not a general advice chatbot. It is a constrained welfare-scheme intake agent that collects facts, runs deterministic eligibility, and returns concise results with document guidance.

## Goals and Success Criteria

1. Build profiles through conversation.
   - Success: from an empty profile, the agent can collect enough facts to match at least one scheme or state that no confident match exists.
   - Success: the agent never asks for a field already present in `asked_fields` or confidently extracted from prior messages.

2. Minimise questions.
   - Success: question selection chooses the single field with highest expected information gain over active schemes.
   - Success: for seed data, common profiles produce results in <= 6 questions when the user answers directly.

3. Expose profile completeness.
   - Success: every WebSocket response includes `profile_completeness` from 0 to 100.
   - Success: results are produced automatically once completeness >= 75 and at least one high-confidence match or near miss exists.

4. Persist sessions.
   - Success: Redis session TTL is exactly 30 days after each user or agent turn.
   - Success: returning sessions greet by known name when available and do not re-ask answered fields.

5. Support households.
   - Success: a session can include multiple household members with individual sub-profiles.
   - Success: user can say "check for my mother" and the agent switches active member.

6. Handle life events.
   - Success: "I got married" updates marital status, appends a profile event, and re-runs eligibility.
   - Success: "I had a child" creates or updates child household member and re-runs relevant schemes.

7. Provide document sufficiency checks.
   - Success: `POST /schemes/{id}/document-check` returns whether available documents satisfy mandatory requirements or substitutes.

## User Stories

1. First conversation
   - User: "I am a farmer from Bihar and I need help."
   - Agent extracts occupation and state, then asks the best next question, e.g. income or land.
   - Edge case: if message is too vague, agent asks one clarification: "Which state do you live in?"

2. No repeated questions
   - User says age in first message.
   - Agent must not ask "How old are you?" later in the session.
   - If the user gives contradictory age later, agent asks a correction question once.

3. Household member
   - User: "My mother is a widow and she is 62."
   - Agent creates a member named "mother" with relationship `mother`, age `62`, gender `female`, marital status `widowed`.
   - Agent asks for missing BPL/income/state facts before matching pension schemes.

4. Returning session
   - User returns with same `session_id`.
   - Agent: "Namaste Sita. I remember your profile. Do you want to continue checking schemes for you or someone in your family?"
   - Edge case: if name unknown, greeting is "Namaste. I remember your previous answers."

5. Life event update
   - User: "I had a baby girl last month."
   - Agent detects `child_birth`, creates child member with gender `female` and approximate age `0`, asks if the mother is pregnant/lactating only if needed, then re-runs eligibility for mother and child.

6. Profile update API
   - Operator updates profile via PATCH.
   - System merges fields, records changed fields, invalidates cached match result, and returns new profile completeness.

7. Document check
   - User has Aadhaar and bank passbook but no income certificate.
   - API returns `is_sufficient=false`, missing income certificate, substitutes, and instructions to obtain original.

8. Zero matches
   - If no match and no near miss after sufficient profile, agent says: "I could not find a matching scheme from the current list. You can try again after adding income, caste, disability, or pregnancy details."
   - It must log the zero-match query in Phase 5; Phase 2 stores a placeholder `zero_match_events` table for forward compatibility.

## Functional Requirements

1. Use LangGraph for the conversation graph.
2. Agent state must contain `messages`, `user_profile`, `household`, `active_member_id`, `asked_fields`, `remaining_required_fields`, `confidence_score`, `profile_completeness`, `session_id`, and `language_code`.
3. All agent responses must be short and concrete because later phases voice them to low-literacy users.
4. Agent must ask exactly one question per turn unless returning final results.
5. Agent must never ask for Aadhaar number, full bank account number, OTP, or document image in Phase 2.
6. Agent must not make legal guarantees; result wording must say "You appear eligible" rather than "You are guaranteed eligible."
7. Question selection must use active scheme rules from Phase 1.
8. The agent must not ask fields irrelevant to any remaining candidate scheme.
9. The agent must maintain `asked_fields` as `{member_id}:{field}` strings.
10. The agent must consider a field answered when extraction confidence >= 0.75.
11. If extraction confidence is between 0.5 and 0.75, the next agent message must be a confirmation question.
12. If extraction confidence < 0.5, the message must not update the profile.
13. The profile completeness score must be deterministic.
14. Completeness score formula:
    - Required base fields: `state_code`, `age`, `gender`, `occupation_type`, `annual_income`.
    - Score = answered weighted fields / relevant weighted fields * 100.
    - Relevant fields are derived from top 20 candidate active schemes after each turn.
15. Default field weights:
    - state_code: 15
    - age: 15
    - gender: 10
    - annual_income: 15
    - occupation_type: 15
    - caste_category: 8
    - marital_status: 8
    - land_holding_acres: 8
    - custom scheme-specific facts: 6 total, distributed equally
16. Stop asking and produce results when:
    - completeness >= 75, and
    - at least one match exists, or at least one near miss exists, or no unknown criteria remain for top 10 candidate schemes.
17. Hard stop after 8 agent questions in one session segment; produce best available result or explain missing facts.
18. Household member profiles must share household-level fields such as state, district, ration card availability, and income if explicitly stated as household income.
19. Member profiles must override household-level facts when the user provides member-specific facts.
20. Redis key format must be `session:{organisation_id}:{session_id}`.
21. Redis TTL must be reset to 30 days after every state write.
22. PostgreSQL must store canonical profiles and conversation metadata; Redis stores fast mutable LangGraph state.
23. WebSocket endpoint must accept JSON only.
24. WebSocket must stream message chunks for LLM-generated text, but eligibility result payload must be sent as one complete message.
25. Agent must call Phase 1 eligibility service function directly inside backend, not over HTTP, when running in the same FastAPI app.
26. A simple Next.js test UI must support entering `session_id`, language code, and text messages.
27. The test UI must show raw JSON state behind a collapsible "Debug" panel.
28. Document-check endpoint must use the scheme's active `required_documents` from the rule JSON.
29. Document matching must be case-insensitive and synonym-aware for common aliases: Aadhaar/Aadhar, bank passbook/bank statement, ration card/PDS card.
30. Substitute document guidance must include original document instructions when no substitute is available.
31. All profile updates must append to `profile_events`.
32. All profile update flows must re-run matching and store a `last_match_snapshot`.
33. Phase 2 must keep language_code in state but does not translate messages yet.
34. Allowed language codes in Phase 2: `en`, `hi`, `bn`, `te`, `mr`, `ta`, `gu`, `kn`, `ml`, `pa`, `or`.
35. Non-English messages in Phase 2 may be stored, but extraction quality is not guaranteed until Phase 3 translation.

## Data Models

Phase 2 depends on all Phase 1 tables. New tables below are additive.

### SQL DDL

```sql
CREATE TABLE households (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    state_code TEXT,
    district TEXT,
    village TEXT,
    pincode TEXT,
    ration_card_type TEXT,
    annual_household_income INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$')
);

CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    household_id UUID REFERENCES households(id) ON DELETE SET NULL,
    display_name TEXT,
    relationship_to_primary TEXT NOT NULL DEFAULT 'self',
    age INTEGER CHECK (age IS NULL OR (age >= 0 AND age <= 120)),
    date_of_birth DATE,
    gender TEXT CHECK (gender IS NULL OR gender IN ('female', 'male', 'other', 'unknown')),
    caste_category TEXT CHECK (caste_category IS NULL OR caste_category IN ('SC', 'ST', 'OBC', 'GENERAL', 'UNKNOWN')),
    annual_income INTEGER CHECK (annual_income IS NULL OR annual_income >= 0),
    land_holding_acres NUMERIC(8,2) CHECK (land_holding_acres IS NULL OR land_holding_acres >= 0),
    occupation_type TEXT,
    marital_status TEXT CHECK (marital_status IS NULL OR marital_status IN ('single', 'married', 'widowed', 'divorced', 'separated', 'unknown')),
    state_code TEXT,
    district TEXT,
    existing_scheme_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    custom_attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    profile_completeness INTEGER NOT NULL DEFAULT 0 CHECK (profile_completeness >= 0 AND profile_completeness <= 100),
    last_match_snapshot JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$')
);

CREATE INDEX idx_profiles_org_household ON profiles (organisation_id, household_id);

CREATE TABLE conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    session_id TEXT NOT NULL,
    household_id UUID REFERENCES households(id) ON DELETE SET NULL,
    primary_profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    active_profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    language_code TEXT NOT NULL DEFAULT 'en',
    confidence_score NUMERIC(4,3) NOT NULL DEFAULT 0,
    profile_completeness INTEGER NOT NULL DEFAULT 0,
    asked_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    remaining_required_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    redis_key TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, session_id)
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    conversation_session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    language_code TEXT NOT NULL DEFAULT 'en',
    message_type TEXT NOT NULL DEFAULT 'text',
    structured_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_conversation_messages_session ON conversation_messages (organisation_id, conversation_session_id, created_at);

CREATE TABLE profile_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('conversation', 'api_patch', 'system')),
    changed_fields JSONB NOT NULL,
    previous_values JSONB NOT NULL DEFAULT '{}'::jsonb,
    new_values JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence_score NUMERIC(4,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE document_check_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    scheme_id TEXT NOT NULL REFERENCES schemes(id),
    documents_available JSONB NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE zero_match_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    conversation_session_id UUID REFERENCES conversation_sessions(id) ON DELETE SET NULL,
    profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    original_query_text TEXT,
    language_code TEXT NOT NULL DEFAULT 'en',
    profile_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Python SQLAlchemy Models

```python
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Household(Base):
    __tablename__ = "households"
    __table_args__ = (CheckConstraint("state_code IS NULL OR state_code ~ '^IN-[A-Z]{2}$'"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    state_code: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    village: Mapped[str | None] = mapped_column(Text)
    pincode: Mapped[str | None] = mapped_column(Text)
    ration_card_type: Mapped[str | None] = mapped_column(Text)
    annual_household_income: Mapped[int | None] = mapped_column(Integer)
    metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    household_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("households.id", ondelete="SET NULL"))
    display_name: Mapped[str | None] = mapped_column(Text)
    relationship_to_primary: Mapped[str] = mapped_column(Text, nullable=False, default="self")
    age: Mapped[int | None] = mapped_column(Integer)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(Text)
    caste_category: Mapped[str | None] = mapped_column(Text)
    annual_income: Mapped[int | None] = mapped_column(Integer)
    land_holding_acres: Mapped[float | None] = mapped_column(Numeric(8, 2))
    occupation_type: Mapped[str | None] = mapped_column(Text)
    marital_status: Mapped[str | None] = mapped_column(Text)
    state_code: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    existing_scheme_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    custom_attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    profile_completeness: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_match_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    __table_args__ = (UniqueConstraint("organisation_id", "session_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    household_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("households.id", ondelete="SET NULL"))
    primary_profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    active_profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="en")
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)
    profile_completeness: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    asked_fields: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    remaining_required_fields: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    redis_key: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    conversation_session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="en")
    message_type: Mapped[str] = mapped_column(Text, nullable=False, default="text")
    structured_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProfileEvent(Base):
    __tablename__ = "profile_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    changed_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    previous_values: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    new_values: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

## API Specification

### Shared TypeScript Types

```ts
export type AgentMessageType = "question" | "result" | "clarification" | "error" | "state";

export interface HouseholdMemberProfile {
  id: string;
  display_name?: string;
  relationship_to_primary: string;
  age?: number;
  gender?: "female" | "male" | "other" | "unknown";
  caste_category?: "SC" | "ST" | "OBC" | "GENERAL" | "UNKNOWN";
  annual_income?: number;
  land_holding_acres?: number;
  occupation_type?: string;
  marital_status?: string;
  state_code?: string;
  district?: string;
  existing_scheme_ids: string[];
  custom_attributes: Record<string, unknown>;
  profile_completeness: number;
}

export interface AgentState {
  session_id: string;
  language_code: string;
  messages: Array<{ role: "user" | "assistant" | "system" | "tool"; content: string }>;
  user_profile: HouseholdMemberProfile;
  household: { id: string; members: HouseholdMemberProfile[] };
  active_member_id: string;
  asked_fields: string[];
  remaining_required_fields: string[];
  confidence_score: number;
  profile_completeness: number;
}

export interface WsChatClientMessage {
  session_id: string;
  message: string;
  language_code: string;
}

export interface WsChatServerMessage {
  type: "question" | "result" | "clarification" | "error";
  content: string;
  profile_completeness: number;
  session_id: string;
  payload?: unknown;
}
```

### Shared Pydantic Models

```python
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class HouseholdMemberProfileModel(BaseModel):
    id: str | None = None
    display_name: str | None = None
    relationship_to_primary: str = "self"
    age: int | None = Field(default=None, ge=0, le=120)
    gender: Literal["female", "male", "other", "unknown"] | None = None
    caste_category: Literal["SC", "ST", "OBC", "GENERAL", "UNKNOWN"] | None = None
    annual_income: int | None = Field(default=None, ge=0)
    land_holding_acres: float | None = Field(default=None, ge=0)
    occupation_type: str | None = None
    marital_status: str | None = None
    state_code: str | None = None
    district: str | None = None
    existing_scheme_ids: list[str] = []
    custom_attributes: dict[str, Any] = {}
    profile_completeness: int = Field(default=0, ge=0, le=100)


class CreateSessionRequest(BaseModel):
    organisation_id: UUID
    session_id: str | None = None
    language_code: str = "en"


class CreateSessionResponse(BaseModel):
    session_id: str
    profile_id: UUID
    household_id: UUID
    greeting: str
    profile_completeness: int


class ChatInputModel(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=2000)
    language_code: str = "en"


class ChatOutputModel(BaseModel):
    type: Literal["question", "result", "clarification", "error"]
    content: str
    profile_completeness: int
    session_id: str
    payload: dict[str, Any] | None = None


class PatchProfileRequest(BaseModel):
    organisation_id: UUID
    fields: dict[str, Any]
    source: Literal["conversation", "api_patch"] = "api_patch"


class PatchProfileResponse(BaseModel):
    profile: HouseholdMemberProfileModel
    changed_fields: list[str]
    profile_completeness: int
    match_snapshot: dict[str, Any]


class DocumentCheckRequest(BaseModel):
    organisation_id: UUID
    profile_id: UUID | None = None
    documents_available: list[str]


class MissingDocumentModel(BaseModel):
    name: str
    accepted_substitutes: list[dict[str, Any]]
    original_document_instructions: str


class DocumentCheckResponse(BaseModel):
    is_sufficient: bool
    missing: list[MissingDocumentModel]
    substitutes_available: list[dict[str, Any]]
    matched_documents: list[str]
```

### POST /agent/sessions

Creates or resumes a session.

Request:

```json
{
  "organisation_id": "00000000-0000-0000-0000-000000000001",
  "session_id": null,
  "language_code": "en"
}
```

Response `201`:

```json
{
  "session_id": "sess_01J2V7W7Z5AMZ5X6Q6M",
  "profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
  "household_id": "148e76be-fae3-4fd8-9a0e-9cfa64c30001",
  "greeting": "Namaste. Tell me about your situation, and I will check schemes for you.",
  "profile_completeness": 0
}
```

Resume behavior:

- If Redis state exists, return existing profile and greeting.
- If Redis expired but PostgreSQL session exists and `expires_at > now()`, rebuild Redis state from PostgreSQL messages/profile.
- If both expired, return `410 SESSION_EXPIRED`.

### GET /agent/sessions/{session_id}

Query: `organisation_id`.

Response: current `AgentState`.

Error `404 SESSION_NOT_FOUND`: "This conversation was not found."

### WebSocket /ws/chat

Client sends:

```json
{
  "session_id": "sess_01J2V7W7Z5AMZ5X6Q6M",
  "message": "I am a widow, 62 years old, from Uttar Pradesh.",
  "language_code": "en"
}
```

Server streams:

```json
{
  "type": "question",
  "content": "Do you have a BPL card or ration card?",
  "profile_completeness": 68,
  "session_id": "sess_01J2V7W7Z5AMZ5X6Q6M",
  "payload": {
    "asked_field": "self.custom_attributes.is_bpl"
  }
}
```

Result message:

```json
{
  "type": "result",
  "content": "You appear eligible for 2 schemes. The strongest match is Indira Gandhi National Widow Pension Scheme.",
  "profile_completeness": 86,
  "session_id": "sess_01J2V7W7Z5AMZ5X6Q6M",
  "payload": {
    "matched_schemes": [],
    "near_miss_schemes": []
  }
}
```

WebSocket errors:

| Code | Message | Behavior |
|---|---|---|
| `SESSION_NOT_FOUND` | "This conversation was not found. Please start again." | Close with code 4404. |
| `MESSAGE_TOO_LONG` | "Please send a shorter message." | Keep socket open. |
| `AGENT_TIMEOUT` | "I am taking too long. Please try once more." | Keep socket open. |
| `INVALID_JSON` | "Message format is not valid." | Close with code 4400. |

### POST /agent/message

REST fallback for tests. Same request/response as one WebSocket turn.

### PATCH /profile/{id}

Request:

```json
{
  "organisation_id": "00000000-0000-0000-0000-000000000001",
  "fields": {
    "marital_status": "married",
    "custom_attributes": {
      "has_child": true
    }
  },
  "source": "api_patch"
}
```

Response:

```json
{
  "profile": {
    "id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
    "relationship_to_primary": "self",
    "marital_status": "married",
    "existing_scheme_ids": [],
    "custom_attributes": {"has_child": true},
    "profile_completeness": 54
  },
  "changed_fields": ["marital_status", "custom_attributes.has_child"],
  "profile_completeness": 54,
  "match_snapshot": {
    "matched_schemes": [],
    "near_miss_schemes": []
  }
}
```

Errors:

| Status | Code | Behavior |
|---|---|---|
| 404 | PROFILE_NOT_FOUND | Do not create implicitly. |
| 422 | INVALID_PROFILE_PATCH | Return field-specific issue. |

### POST /households/{household_id}/members

Adds a household member.

Request: `HouseholdMemberProfileModel` without `id`.

Response: created member profile.

### DELETE /households/{household_id}/members/{profile_id}

Soft-delete is deferred. Phase 2 hard-deletes only if profile has no saved status records. Since saved statuses arrive in Phase 4, this endpoint may hard-delete in Phase 2.

### POST /schemes/{id}/document-check

Request:

```json
{
  "organisation_id": "00000000-0000-0000-0000-000000000001",
  "profile_id": "a2bc79d6-5c5f-4b14-9d66-1f0a6e1a7777",
  "documents_available": ["Aadhaar", "Bank statement"]
}
```

Response:

```json
{
  "is_sufficient": false,
  "missing": [
    {
      "name": "Income certificate",
      "accepted_substitutes": [
        {
          "name": "BPL card",
          "instructions": "Use your ration card or BPL card if the application portal accepts it for income proof.",
          "estimated_cost_inr": 0,
          "estimated_time_days": 1,
          "issuing_authority": "Food and Civil Supplies Department"
        }
      ],
      "original_document_instructions": "Visit the tehsil, revenue office, or state e-district portal to apply for an income certificate. Expected time: 7 to 21 days. Expected cost: INR 0 to 50 depending on state."
    }
  ],
  "substitutes_available": [
    {
      "for_document": "Income certificate",
      "substitute": "BPL card"
    }
  ],
  "matched_documents": ["Aadhaar", "Bank statement"]
}
```

## Architecture and Implementation Approach

### Libraries

```txt
langgraph>=0.2
langchain-core>=0.3
langchain-ollama>=0.2
langchain-groq>=0.2
redis[hiredis]>=5.0
websockets>=12.0
jsonschema>=4.23
```

### LangGraph State

```python
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AdhikarAgentState(TypedDict):
    session_id: str
    organisation_id: str
    messages: Annotated[list[dict[str, str]], add_messages]
    user_profile: dict[str, Any]
    household: dict[str, Any]
    active_member_id: str
    asked_fields: list[str]
    remaining_required_fields: list[str]
    confidence_score: float
    profile_completeness: int
    language_code: str
    last_match_result: dict[str, Any] | None
    turn_count_since_result: int
```

### Graph Nodes

```txt
load_session
extract_profile_facts
detect_life_event
merge_profile_update
compute_candidate_schemes
compute_profile_completeness
should_match_or_ask
select_next_question
run_eligibility_match
format_result
persist_session
```

Edges:

```txt
START -> load_session
load_session -> extract_profile_facts
extract_profile_facts -> detect_life_event
detect_life_event -> merge_profile_update
merge_profile_update -> compute_candidate_schemes
compute_candidate_schemes -> compute_profile_completeness
compute_profile_completeness -> should_match_or_ask
should_match_or_ask(match) -> run_eligibility_match
should_match_or_ask(ask) -> select_next_question
run_eligibility_match -> format_result
select_next_question -> persist_session
format_result -> persist_session
persist_session -> END
```

### Exact Function Signatures

```python
async def get_or_create_session(request: CreateSessionRequest) -> CreateSessionResponse: ...

async def handle_chat_turn(input_message: ChatInputModel) -> ChatOutputModel: ...

async def websocket_chat_endpoint(websocket: WebSocket) -> None: ...

def extract_profile_facts(message: str, state: AdhikarAgentState, llm: BaseChatModel) -> ExtractedFacts: ...

def detect_life_event(message: str, llm: BaseChatModel) -> LifeEvent | None: ...

def merge_profile_update(profile: dict[str, Any], extracted: ExtractedFacts) -> ProfileMergeResult: ...

def compute_information_gain(field: str, candidate_rules: list[EligibilityCriteriaModel]) -> float: ...

def select_next_question(state: AdhikarAgentState, candidate_rules: list[EligibilityCriteriaModel]) -> Question: ...

def compute_profile_completeness(profile: dict[str, Any], candidate_rules: list[EligibilityCriteriaModel]) -> int: ...

async def patch_profile(profile_id: UUID, request: PatchProfileRequest) -> PatchProfileResponse: ...

async def check_documents(scheme_id: str, request: DocumentCheckRequest) -> DocumentCheckResponse: ...
```

### Extraction Prompt Contract

The LLM must return strict JSON:

```json
{
  "facts": [
    {"field": "age", "value": 62, "confidence": 0.94, "member_reference": "self"},
    {"field": "marital_status", "value": "widowed", "confidence": 0.92, "member_reference": "self"}
  ],
  "active_member_reference": "self",
  "needs_confirmation": []
}
```

If the model returns invalid JSON, retry once with a repair prompt. If still invalid, do not update profile and ask: "I did not understand that. Which state do you live in?"

### Question Selection

Algorithm:

1. Build candidate scheme set from active rules.
2. Remove schemes already impossible due to known hard failures, except keep near-miss candidates.
3. For each missing field, count how many candidate schemes reference it.
4. Weight the field by:
   - number of candidate schemes affected,
   - criterion restrictiveness,
   - whether field is required by top benefit categories.
5. Exclude fields in `asked_fields`.
6. Return the highest score.

Pseudo-code:

```python
def select_next_question(state: AdhikarAgentState, rules: list[EligibilityCriteriaModel]) -> Question:
    scores: dict[str, float] = {}
    for rule in rules:
        for field in missing_fields_for_rule(state["user_profile"], rule):
            key = f"{state['active_member_id']}:{field}"
            if key in state["asked_fields"]:
                continue
            scores[field] = scores.get(field, 0.0) + field_information_weight(field, rule)
    if not scores:
        return Question(field="fallback", text="Do you want me to show the best schemes I found so far?")
    field = max(scores, key=scores.get)
    return render_question(field, state["language_code"])
```

Default English question templates:

| Field | Question |
|---|---|
| `state_code` | "Which state do you live in?" |
| `age` | "How old are you?" |
| `gender` | "Should I mark this profile as woman, man, or other?" |
| `annual_income` | "About how much money does your household earn in one year?" |
| `occupation_type` | "What work do you mainly do?" |
| `caste_category` | "Do you belong to SC, ST, OBC, or General category?" |
| `marital_status` | "Are you married, unmarried, widowed, divorced, or separated?" |
| `land_holding_acres` | "How much farming land does your family have, in acres?" |
| `custom_attributes.is_bpl` | "Do you have a BPL card or ration card for a poor household?" |

### Redis State

Key: `session:{organisation_id}:{session_id}`

TTL: `SESSION_TTL_DAYS=30`

Stored JSON:

```json
{
  "state": {},
  "updated_at": "2026-05-08T12:00:00+05:30",
  "version": "phase2.langgraph.v1"
}
```

## Environment-Specific Implementation Notes

| Component | Local / GPU production | Hosted demo / free tier |
|---|---|---|
| LLM provider | `LLM_PROVIDER=ollama` | `LLM_PROVIDER=groq` |
| LLM endpoint | `OLLAMA_BASE_URL=http://localhost:11434` | `GROQ_BASE_URL=https://api.groq.com/openai/v1` |
| Primary model | `OLLAMA_MODEL=llama3.1:8b` | `GROQ_CHAT_MODEL=llama-3.3-70b-versatile` |
| Fallback model | `OLLAMA_FALLBACK_MODEL=qwen2.5:7b` | `GROQ_FALLBACK_MODEL=llama-3.1-8b-instant` |
| Chat endpoint | `POST /api/chat` on Ollama | `POST /chat/completions` under Groq base URL |
| Redis | `REDIS_URL=redis://localhost:6379/0` | `REDIS_URL=rediss://default:<token>@<upstash-host>:6379` |
| Session TTL | `SESSION_TTL_SECONDS=2592000` | same |
| FastAPI | `http://localhost:8000` | `https://adhikarai-api.onrender.com` |
| Frontend test UI | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` | `NEXT_PUBLIC_API_BASE_URL=https://adhikarai-api.onrender.com` |
| WebSocket URL | `NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000` | `NEXT_PUBLIC_WS_BASE_URL=wss://adhikarai-api.onrender.com` |
| Render keep-warm | off | UptimeRobot pings `/health` every 10 minutes |

LLM generation config:

```txt
AGENT_TEMPERATURE=0.1
AGENT_MAX_TOKENS=512
AGENT_JSON_REPAIR_RETRIES=1
AGENT_MAX_QUESTIONS_BEFORE_RESULT=8
```

## File and Folder Structure

```txt
adhikarai/
  backend/
    app/
      agent/
        __init__.py
        graph.py
        state.py
        prompts.py
        extraction.py
        life_events.py
        question_selection.py
        completeness.py
        result_formatter.py
      db/
        models/
          household.py
          profile.py
          conversation.py
          profile_event.py
      schemas/
        agent.py
        household.py
        document_check.py
      services/
        sessions/
          redis_store.py
          session_service.py
        documents/
          document_matcher.py
          guidance.py
      api/
        routes/
          agent_sessions.py
          ws_chat.py
          profiles.py
          households.py
          document_check.py
    tests/
      unit/
        test_question_selection.py
        test_profile_completeness.py
        test_life_event_detection.py
        test_document_check.py
      integration/
        test_ws_chat.py
        test_session_resume.py
        test_patch_profile.py
  frontend/
    app/
      dev-chat/
        page.tsx
    components/
      dev-chat/
        ChatWindow.tsx
        MessageList.tsx
        DebugStatePanel.tsx
    lib/
      api.ts
      websocket.ts
```

## Testing Requirements

### Unit Tests

1. `test_select_question_skips_asked_field`
   - State: `asked_fields=["self:age"]`
   - Candidate rules require age and income.
   - Expected: next question is not age.

2. `test_completeness_score_weighted`
   - Profile has state, age, gender.
   - Expected score based on field weights for candidate rules.

3. `test_life_event_marriage`
   - Message: "I got married last week."
   - Expected event type `marriage`, profile patch `marital_status=married`.

4. `test_life_event_child_birth`
   - Message: "I had a baby girl last month."
   - Expected child profile created with gender female and relationship child.

5. `test_document_check_accepts_substitute`
   - Required bank passbook with accepted substitute bank statement.
   - Available documents: `["bank statement"]`
   - Expected: sufficient for that document.

6. `test_document_check_missing_no_substitute`
   - Missing mandatory income certificate with no substitutes.
   - Expected: `is_sufficient=false`, original instructions present.

### Integration Tests

1. Session create and resume
   - Create session.
   - Send one message.
   - Fetch session.
   - Expected: Redis state contains message and TTL > 29 days.

2. WebSocket one-turn flow
   - Send farmer message.
   - Expected: server returns question or result with `profile_completeness`.

3. Profile patch re-runs match
   - Patch occupation to farmer and state to Bihar.
   - Expected: `last_match_snapshot` changes and `profile_events` row inserted.

4. Hard stop after 8 questions
   - Mock question selector to ask 8 times.
   - Expected: ninth turn returns result or missing facts summary.

### Manual Test Conversation

Input sequence:

```txt
User: I am Sita from Bihar. I do farming.
Agent: How old are you?
User: 34.
Agent: About how much money does your household earn in one year?
User: Around 80000.
Agent: How much farming land does your family have, in acres?
User: One acre.
Agent: You appear eligible for PM-KISAN and may also check crop insurance.
```

Expected state:

```json
{
  "display_name": "Sita",
  "state_code": "IN-BR",
  "occupation_type": "farmer",
  "age": 34,
  "annual_income": 80000,
  "land_holding_acres": 1,
  "profile_completeness": 75
}
```

## Known Constraints and Edge Cases

1. Phase 2 text extraction in Indian languages is best effort until Phase 3 translation.
2. The agent cannot verify truthfulness of profile answers.
3. The agent must not request sensitive identifiers.
4. Redis loss means active conversation state may be rebuilt only from PostgreSQL messages and profile, not from every intermediate graph variable.
5. LLM output can be invalid JSON; retry once and then fall back to deterministic question.
6. Household income ambiguity is common. If user says "we earn 80000", store as household income and copy to active profile only when no individual income exists.
7. Age vs DOB conflicts: DOB wins if both present and conflict by more than one year; ask confirmation.
8. Contradictory gender or marital status facts require confirmation before overwrite.
9. User may ask general political/legal questions; agent must redirect: "I can help check welfare schemes. Tell me your age, state, work, or family situation."
10. User may ask for another person without permission. Phase 2 assumes assisted use and stores household members; consent UX arrives in Phase 4.
11. Profile completeness is not eligibility confidence. It measures enough facts to evaluate likely schemes.

## Dependencies on Previous Phases

1. Phase 1 database schema and migrations must be applied.
2. Phase 1 seed schemes and eligibility rules must exist.
3. Phase 1 eligibility engine must expose an internal Python service callable by the agent.
4. Phase 1 document requirements inside rule JSON are required for document-check endpoint.

