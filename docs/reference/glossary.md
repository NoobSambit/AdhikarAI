# Glossary

Key terms used throughout the AdhikarAI codebase and documentation.

---

## Users & Roles

| Term | Definition |
|---|---|
| **Beneficiary** | A rural Indian citizen who uses AdhikarAI to discover and apply for government welfare schemes. The primary user of the platform. May have low literacy and speak only a regional language. |
| **Profile** | A structured data record containing a beneficiary's demographic, economic, and location information. Used for eligibility matching. Stored in the `profiles` table. |
| **Household** | A family group that links multiple profiles together. Contains shared attributes like family income, ration card type, and member count. |
| **Operator** | An NGO worker or CSC (Common Service Centre) operator who assists beneficiaries via the dashboard. Can access only assigned beneficiaries within their organisation. |
| **NGO Admin** | An administrator within an NGO organisation. Can access all beneficiaries within their organisation. Can manage operators and view analytics. |
| **Super Admin** | A platform-wide administrator with full access across all organisations. Can manage schemes, review quality flags, and view platform analytics. |
| **Organisation** | The top-level tenant entity. Every data record is scoped to an organisation. NGOs, CSCs, and government bodies each have their own organisation. |
| **Organisation Member** | A staff user (operator, NGO admin, or super admin) within an organisation. Stored in `organisation_members`. |

---

## Schemes & Eligibility

| Term | Definition |
|---|---|
| **Scheme** | A government welfare programme (e.g., PM-KISAN, Ujjwala). Stored in the `schemes` table with eligibility rules, benefit details, and validity dates. |
| **Eligibility Rule** | A JSONB-defined set of criteria that determines whether a beneficiary qualifies for a scheme. Rules are data-driven, not hardcoded. |
| **Near Miss** | A scheme where the beneficiary fails exactly one eligibility criterion. Near-miss schemes are shown separately with the single unmet criterion highlighted. |
| **Cross-Scheme Exclusion** | A rule that disqualifies a beneficiary from a scheme if they are already enrolled in a conflicting scheme (e.g., mutually exclusive central programmes). |
| **Document Checklist** | The list of documents a beneficiary needs to apply for a scheme. Includes substitute document guidance when originals are unavailable. |
| **Substitute Document** | An alternative document that can be used in place of a missing original (e.g., self-declaration + MLA recommendation in place of a BPL card). |
| **Scheme Draft** | An admin's working copy of a new or updated scheme. Goes through draft → preview → publish workflow before becoming active. |

---

## Agent & Conversation

| Term | Definition |
|---|---|
| **Agent** | The LangGraph-based AI conversation system that asks clarifying questions and matches eligible schemes. Constrained to welfare-scheme intake only — not a general chatbot. |
| **Session** | A conversation session between a beneficiary and the agent. Each session has a unique ID, a profile, and up to 8 agent turns. Stored in `conversation_sessions`. |
| **Turn** | A single exchange within a conversation: one user message and one agent response. |
| **Fact Extraction** | The LLM-based process of extracting structured profile data (age, income, caste, etc.) from the user's natural language message. |
| **Profile Completeness** | A 0–100% score indicating how much of the beneficiary's profile is filled in. Drives the agent's question selection: once completeness ≥ 75% or after 8 questions, eligibility matching runs. |
| **Question Selection** | The agent's logic for choosing the next most useful clarifying question based on which profile fields are still unknown. |

---

## Voice & Language

| Term | Definition |
|---|---|
| **ASR** | Automatic Speech Recognition — converts audio to text. Providers: Whisper.cpp (local), Groq Whisper (hosted). |
| **Low-Confidence ASR** | When ASR confidence is below 0.70, the agent is not called. A localized fallback message asks the user to speak more clearly or type instead. |
| **Voice Turn** | A full voice pipeline cycle: ASR → translate to English → agent → translate back to user language → TTS. Metrics are persisted but raw audio is not stored. |
| **TTS** | Text-to-Speech — synthesizes audio from text for the agent's response. Providers: IndicTTS (local), Google Cloud TTS (hosted). |
| **IndicTrans2** | An Indian language translation system. Used for translating between regional languages and English. |
| **AI4Bharat** | An Indian AI research initiative providing hosted translation APIs for Indian languages. |
| **Browser ASR Fallback** | When the server-side ASR is slow, the frontend can fall back to the browser's Web Speech API after a configurable timeout. |

---

## Auth & Security

| Term | Definition |
|---|---|
| **OTP Challenge** | A one-time password sent to a beneficiary's phone for authentication. Stored as a PBKDF2 hash. Expires after 5 minutes. Max 5 verification attempts. |
| **Dashboard Session** | An httpOnly cookie-based session for dashboard operators and admins. Uses a JWT with `typ: "dashboard"` to distinguish from beneficiary sessions. |
| **httpOnly Cookie** | A browser cookie that is inaccessible to JavaScript. Used for all session tokens in AdhikarAI to prevent XSS token theft. |
| **Admin Token** | A shared secret (`X-Admin-Token` header) used to authenticate admin API routes (scheme CRUD, ingestion). Not a user-specific credential. |

---

## Infrastructure

| Term | Definition |
|---|---|
| **Redis Memory Fallback** | When `REDIS_URL=memory://`, the backend uses in-memory data structures instead of Redis. Used for local development. Not allowed in staging/production. |
| **FAISS Index** | A vector similarity search index used for semantic scheme search. Built from scheme embeddings using `multilingual-e5-small`. |
| **Neon** | Serverless PostgreSQL provider used for hosted/staging deployments. |
| **Upstash** | Serverless Redis provider used for hosted/staging deployments. |
| **Render** | PaaS for hosting the FastAPI backend. |
| **Vercel** | PaaS for hosting the Next.js frontend. |
| **UptimeRobot** | External monitoring service used to keep-warm the Render backend on free tier. |

---

## Data & Operations

| Term | Definition |
|---|---|
| **Audit Log** | A record of dashboard write operations (beneficiary create, update, note add, etc.). Stored in the `audit_logs` table. |
| **Bulk Eligibility** | A CSV-based workflow where operators upload beneficiary data for batch eligibility checking. Currently partial (synchronous, no per-row evaluation). |
| **Quality Flag** | A system-generated or admin-created flag indicating a potential data quality issue. Reviewed by super admins. |
| **Unmatched Query** | A beneficiary query that resulted in zero scheme matches. Tracked for admin review to identify coverage gaps. |
| **Offline Sync** | PWA feature where changes made while offline are queued in IndexedDB and replayed when connectivity returns. The sync queue exists but the automated retry loop is not yet implemented. |
| **Seed Data** | Pre-populated data (sample schemes, eligibility rules) loaded via the CLI `seed` command for development and testing. |
