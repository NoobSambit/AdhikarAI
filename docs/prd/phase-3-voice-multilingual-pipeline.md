# AdhikarAI PRD - Phase 3: Voice and Multilingual Pipeline

## Phase Summary

Phase 3 adds the voice-first multilingual pipeline to the Phase 2 text agent. It introduces browser audio capture, ASR, language detection, translation, transliteration, TTS, low-confidence handling, and voice playback.

The product flow becomes:

```txt
microphone audio -> ASR -> language detection -> translation to English when required -> LangGraph agent -> translation back to user language -> TTS -> audio playback + transcript
```

The same internal service interfaces must work in both environments:

- Local / GPU production: Whisper.cpp CUDA, Ollama LLM, local IndicTrans2 microservice, local IndicTTS-compatible service.
- Hosted demo: Groq Whisper API, Groq Llama 3.3 70B, AI4Bharat hosted translation endpoint when credentials are available, Google Cloud TTS fallback/primary demo voice.

Important implementation correction: the browser cannot reliably capture raw 48 kHz WAV on every low-end Android device. The frontend must request 48 kHz mono and encode WAV when supported; if the device records at a different sample rate, the client or backend resamples to 48 kHz mono before ASR.

## Goals and Success Criteria

1. Add voice input.
   - Success: user can hold a mic button to speak, release to submit, and receive a transcript.
   - Success: continuous mode auto-submits after 1.5 seconds of detected silence.

2. Support hosted demo latency under 4 seconds for common short turns.
   - Success target for < 8 second utterance on broadband: ASR <= 1.2s, translation <= 0.7s each direction, agent <= 1.3s, TTS <= 0.8s.
   - Success target on 2G/3G: UI remains responsive, uploads show progress, and browser ASR fallback can trigger when server ASR round trip exceeds 2 seconds.

3. Preserve Phase 2 agent contract.
   - Success: all voice turns are converted into the same `ChatInputModel` consumed by Phase 2.
   - Success: low-confidence ASR never reaches the agent.

4. Support 10 Indian languages plus English.
   - Success: language selector persists in localStorage and profile/session.
   - Success: all system messages have localized static strings for low-confidence, retry, recording, and network failure states.

5. Add TTS output.
   - Success: each agent response can be played as audio and displayed as text.
   - Success: player supports play/pause, replay, and 0.75x/1x/1.5x speed controls.

6. Add typed romanised input support.
   - Success: typed Latin-script Hindi such as "mujhe kisan yojana chahiye" is detected as romanised Indian language and routed through transliteration before agent processing.

## User Stories

1. Push-to-talk voice turn
   - User holds the mic button and says: "Main Bihar se kisan hoon."
   - Frontend records audio, shows waveform bars, submits on release.
   - Backend returns transcript, language `hi`, then agent asks next question in Hindi.

2. Continuous voice mode
   - User taps continuous mode, speaks, pauses for 1.5 seconds.
   - Frontend stops recording automatically and submits audio.
   - Edge case: if background noise keeps amplitude above threshold for 12 seconds, frontend stops and shows "Tap once and speak again."

3. Low-confidence ASR
   - Whisper confidence is `0.62`.
   - Backend returns `type="low_confidence"`.
   - Frontend displays the localized retry message and does not send text to the agent.

4. Browser fallback
   - Hosted ASR takes more than 2 seconds or network request fails twice.
   - Frontend switches to Web Speech API if supported.
   - If browser ASR is unsupported, show "Internet is slow. Please type your message or try again."

5. Language override
   - ASR detects Hindi, but user selects Marathi.
   - Session language becomes Marathi for future responses.
   - ASR still records detected language in metadata for debugging.

6. Transliteration
   - User types: "meri maa vidhwa hai aur 62 saal ki hai"
   - Frontend/backend detects romanised Hindi.
   - Text is transliterated/translated before agent extraction.

7. TTS playback
   - Agent returns answer in Bengali.
   - Frontend auto-plays audio and shows transcript.
   - User can replay at 0.75x speed.

8. Translation failure
   - AI4Bharat hosted API fails with 5xx.
   - Backend retries once, falls back to Google Translate if configured, otherwise returns original text with warning `TRANSLATION_UNAVAILABLE`.

## Functional Requirements

1. Add `VOICE_PROVIDER` env var with allowed values `local`, `groq`, `browser`.
2. Add `TRANSLATION_PROVIDER` env var with allowed values `local_indictrans2`, `ai4bharat_hosted`, `google`.
3. Add `TTS_PROVIDER` env var with allowed values `local_indictts`, `google`.
4. Browser must request microphone permission only after user action.
5. Audio recording component must support push-to-talk and continuous modes.
6. Push-to-talk mode starts recording on pointer down and stops on pointer up/cancel.
7. Continuous mode starts on tap and stops after 1.5 seconds of silence.
8. Silence threshold must be configurable with `NEXT_PUBLIC_SILENCE_THRESHOLD=0.018`.
9. Max utterance duration must be `VOICE_MAX_UTTERANCE_SECONDS=20`.
10. Frontend must render real-time waveform amplitude bars while mic is active.
11. Frontend must request mono audio and prefer 48 kHz.
12. Frontend must encode WAV when supported.
13. Backend must validate uploaded audio size <= `VOICE_MAX_UPLOAD_MB=8`.
14. Backend must resample all audio to 48 kHz mono WAV before local Whisper.cpp.
15. Hosted Groq ASR may accept `webm`, `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `wav`, or `ogg`; backend still normalizes response shape.
16. ASR response shape must always include `transcript`, `detected_language_code`, `confidence`, `duration_ms`, and `provider`.
17. If ASR confidence < 0.70, backend returns low-confidence and must not call the agent.
18. Low-confidence frontend message in English: "We didn't catch that. Please try again."
19. Low-confidence message must be localized for all supported languages.
20. Language detection must prefer ASR detected language unless user selected a language manually.
21. Language selector must appear on first launch and in settings.
22. Language selector must show these languages: English, Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada, Malayalam, Punjabi, Odia.
23. The original user request asked for 10 Indian languages; this PRD includes 11 Indian languages plus English because Phase 2 already allowed Odia. Implementation must support the full list and may hide Odia behind config if launch scope requires exactly 10.
24. Language selection must persist to `localStorage.language_code` and session profile.
25. Translation to English must occur before Phase 2 extraction when `language_code != "en"`.
26. Agent responses must be translated from English to user language before TTS and display, except when the agent already generated in the target language.
27. For hosted demo, Groq LLM may be instructed to answer in English only before translation to reduce mixed-language drift.
28. Transliteration detection must run only for typed text, not ASR transcripts.
29. Romanised Indian text detection must require Latin script plus at least two known romanised tokens or langdetect confidence for a non-English Indian language.
30. Transliteration output must be stored alongside original typed text.
31. Local translation service must be a FastAPI microservice on port 8001.
32. Local translation service must expose `POST /translate`.
33. Translation response must preserve placeholders such as scheme names, amounts, and URLs.
34. Local TTS must return an audio buffer with content type `audio/wav` or `audio/mpeg`.
35. Hosted Google Cloud TTS must return base64 audio decoded by backend before streaming to frontend.
36. TTS playback component must auto-play after agent reply unless user disabled autoplay.
37. TTS playback must show transcript text alongside audio for partial-literacy users.
38. Backend must cache TTS output by hash of `(text, language_code, voice_name, speaking_rate)` for 24 hours in Redis.
39. Backend must cache translations by hash of `(text, source_lang, target_lang, provider)` for 7 days in Redis.
40. WebSocket must support voice message events as separate schemas from text message events.
41. Audio upload endpoint must support REST fallback for browsers where binary WebSocket is unstable.
42. Every voice turn must store timing metrics for ASR, translation, agent, TTS, and total latency.
43. Voice metrics must not store raw audio by default.
44. Raw audio storage is out of scope unless `STORE_AUDIO_DEBUG=true` and admin token is present.
45. All user-facing error messages must include a speak/type fallback.

## Data Models

Phase 3 depends on Phase 1 and Phase 2 tables. New tables are additive.

### SQL DDL

```sql
CREATE TABLE voice_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    conversation_session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    provider TEXT NOT NULL CHECK (provider IN ('local', 'groq', 'browser')),
    input_audio_mime_type TEXT,
    input_audio_duration_ms INTEGER,
    input_audio_size_bytes INTEGER,
    transcript TEXT,
    normalized_transcript TEXT,
    detected_language_code TEXT,
    selected_language_code TEXT NOT NULL,
    asr_confidence NUMERIC(4,3),
    status TEXT NOT NULL CHECK (status IN ('received', 'transcribed', 'low_confidence', 'agent_completed', 'failed')),
    error_code TEXT,
    error_message TEXT,
    timings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_voice_turns_session ON voice_turns (organisation_id, conversation_session_id, created_at);

CREATE TABLE translation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    conversation_session_id UUID REFERENCES conversation_sessions(id) ON DELETE SET NULL,
    provider TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    input_text_hash TEXT NOT NULL,
    input_text_preview TEXT NOT NULL,
    output_text_preview TEXT,
    status TEXT NOT NULL CHECK (status IN ('success', 'fallback_success', 'failed')),
    latency_ms INTEGER,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_translation_events_session ON translation_events (organisation_id, conversation_session_id, created_at);

CREATE TABLE tts_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    conversation_session_id UUID REFERENCES conversation_sessions(id) ON DELETE SET NULL,
    provider TEXT NOT NULL,
    language_code TEXT NOT NULL,
    voice_name TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    audio_mime_type TEXT NOT NULL,
    audio_size_bytes INTEGER,
    speaking_rate NUMERIC(4,2) NOT NULL DEFAULT 1.0,
    status TEXT NOT NULL CHECK (status IN ('success', 'cache_hit', 'failed')),
    latency_ms INTEGER,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_language_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    session_id TEXT,
    language_code TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('selector', 'asr_detected', 'profile_patch')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organisation_id, profile_id)
);
```

### Python SQLAlchemy Models

```python
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VoiceTurn(Base):
    __tablename__ = "voice_turns"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    conversation_session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    input_audio_mime_type: Mapped[str | None] = mapped_column(Text)
    input_audio_duration_ms: Mapped[int | None] = mapped_column(Integer)
    input_audio_size_bytes: Mapped[int | None] = mapped_column(Integer)
    transcript: Mapped[str | None] = mapped_column(Text)
    normalized_transcript: Mapped[str | None] = mapped_column(Text)
    detected_language_code: Mapped[str | None] = mapped_column(Text)
    selected_language_code: Mapped[str] = mapped_column(Text, nullable=False)
    asr_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    timings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TranslationEvent(Base):
    __tablename__ = "translation_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    conversation_session_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    source_lang: Mapped[str] = mapped_column(Text, nullable=False)
    target_lang: Mapped[str] = mapped_column(Text, nullable=False)
    input_text_hash: Mapped[str] = mapped_column(Text, nullable=False)
    input_text_preview: Mapped[str] = mapped_column(Text, nullable=False)
    output_text_preview: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TTSEvent(Base):
    __tablename__ = "tts_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organisation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    conversation_session_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(Text, nullable=False)
    voice_name: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(Text, nullable=False)
    audio_mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    audio_size_bytes: Mapped[int | None] = mapped_column(Integer)
    speaking_rate: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=1.0)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

## API Specification

### Shared TypeScript Types

```ts
export type VoiceProvider = "local" | "groq" | "browser";
export type TranslationProvider = "local_indictrans2" | "ai4bharat_hosted" | "google";
export type TtsProvider = "local_indictts" | "google";

export type LanguageCode =
  | "en" | "hi" | "bn" | "te" | "mr" | "ta" | "gu" | "kn" | "ml" | "pa" | "or";

export interface AsrResponse {
  transcript: string;
  detected_language_code: LanguageCode;
  confidence: number;
  duration_ms: number;
  provider: VoiceProvider;
}

export interface VoiceTurnResponse {
  type: "transcript" | "low_confidence" | "result" | "question" | "clarification" | "error";
  transcript?: string;
  detected_language_code?: LanguageCode;
  selected_language_code: LanguageCode;
  confidence?: number;
  content: string;
  profile_completeness: number;
  audio_url?: string;
  timings: {
    asr_ms?: number;
    translation_to_en_ms?: number;
    agent_ms?: number;
    translation_from_en_ms?: number;
    tts_ms?: number;
    total_ms: number;
  };
  payload?: unknown;
}

export interface TranslateRequest {
  text: string;
  source_lang: LanguageCode;
  target_lang: LanguageCode;
}

export interface TranslateResponse {
  translated_text: string;
  source_lang: LanguageCode;
  target_lang: LanguageCode;
  provider: TranslationProvider;
  cached: boolean;
}
```

### Shared Pydantic Models

```python
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

LanguageCode = Literal["en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or"]


class AsrResponseModel(BaseModel):
    transcript: str
    detected_language_code: LanguageCode
    confidence: float = Field(ge=0, le=1)
    duration_ms: int
    provider: Literal["local", "groq", "browser"]


class VoiceTurnResponseModel(BaseModel):
    type: Literal["transcript", "low_confidence", "result", "question", "clarification", "error"]
    transcript: str | None = None
    detected_language_code: LanguageCode | None = None
    selected_language_code: LanguageCode
    confidence: float | None = Field(default=None, ge=0, le=1)
    content: str
    profile_completeness: int = Field(ge=0, le=100)
    audio_url: str | None = None
    timings: dict[str, int]
    payload: dict[str, Any] | None = None


class TranslateRequestModel(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    source_lang: LanguageCode
    target_lang: LanguageCode


class TranslateResponseModel(BaseModel):
    translated_text: str
    source_lang: LanguageCode
    target_lang: LanguageCode
    provider: Literal["local_indictrans2", "ai4bharat_hosted", "google"]
    cached: bool


class TtsRequestModel(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language_code: LanguageCode
    speaking_rate: float = Field(default=1.0, ge=0.75, le=1.5)


class TtsResponseModel(BaseModel):
    audio_url: str
    audio_mime_type: str
    provider: Literal["local_indictts", "google"]
    cached: bool
```

### POST /voice/asr

Multipart form:

| Field | Type | Required |
|---|---|---|
| `organisation_id` | string UUID | yes |
| `session_id` | string | yes |
| `language_code` | string | yes |
| `audio` | file | yes |
| `client_duration_ms` | integer | no |

Response `200`:

```json
{
  "transcript": "main bihar se kisan hoon",
  "detected_language_code": "hi",
  "confidence": 0.91,
  "duration_ms": 1040,
  "provider": "groq"
}
```

Response `200` low confidence is not returned here; low-confidence handling is in `/voice/turn`. If direct ASR confidence is low, this endpoint still returns the transcript and confidence for developer debugging.

Errors:

| Status | Code | Exact behavior |
|---|---|---|
| 413 | AUDIO_TOO_LARGE | Return "Audio is too large. Please speak for less than 20 seconds." |
| 415 | UNSUPPORTED_AUDIO_FORMAT | Return "This audio format is not supported. Please record again." |
| 504 | ASR_TIMEOUT | Return "Speech service is slow. Please try again or type your message." |
| 502 | ASR_PROVIDER_ERROR | Return "Speech service failed. Please try again." |

### POST /voice/turn

Runs the complete voice pipeline.

Multipart form:

| Field | Type | Required |
|---|---|---|
| `organisation_id` | string UUID | yes |
| `session_id` | string | yes |
| `selected_language_code` | language code | yes |
| `audio` | file | yes |
| `client_duration_ms` | integer | no |

Response `200` question:

```json
{
  "type": "question",
  "transcript": "main bihar se kisan hoon",
  "detected_language_code": "hi",
  "selected_language_code": "hi",
  "confidence": 0.91,
  "content": "Aapki umar kitni hai?",
  "profile_completeness": 38,
  "audio_url": "/voice/tts/audio/tts_01JVOICE.mp3",
  "timings": {
    "asr_ms": 900,
    "translation_to_en_ms": 310,
    "agent_ms": 820,
    "translation_from_en_ms": 290,
    "tts_ms": 410,
    "total_ms": 2730
  },
  "payload": {
    "asked_field": "self.age"
  }
}
```

Response `200` low confidence:

```json
{
  "type": "low_confidence",
  "selected_language_code": "hi",
  "confidence": 0.54,
  "content": "Hum theek se sun nahi paaye. Kripya dobara boliye.",
  "profile_completeness": 38,
  "timings": {
    "asr_ms": 980,
    "total_ms": 1002
  }
}
```

### POST /translate

Public backend wrapper, same shape as local translation microservice.

Request:

```json
{
  "text": "I am a farmer from Bihar.",
  "source_lang": "en",
  "target_lang": "hi"
}
```

Response:

```json
{
  "translated_text": "मैं बिहार से किसान हूँ।",
  "source_lang": "en",
  "target_lang": "hi",
  "provider": "ai4bharat_hosted",
  "cached": false
}
```

### POST /tts

Request:

```json
{
  "text": "आपकी उम्र कितनी है?",
  "language_code": "hi",
  "speaking_rate": 1.0
}
```

Response:

```json
{
  "audio_url": "/voice/tts/audio/tts_01JVOICE.mp3",
  "audio_mime_type": "audio/mpeg",
  "provider": "google",
  "cached": false
}
```

### WebSocket /ws/voice

Client text control message:

```json
{
  "type": "start",
  "session_id": "sess_01J2V7",
  "organisation_id": "00000000-0000-0000-0000-000000000001",
  "selected_language_code": "hi",
  "mime_type": "audio/webm"
}
```

Client binary messages: audio chunks.

Client end message:

```json
{"type": "end"}
```

Server message:

```json
{
  "type": "partial_status",
  "stage": "asr",
  "content": "Listening..."
}
```

Final server message: `VoiceTurnResponse`.

If binary WebSocket fails, frontend must use `POST /voice/turn`.

## Architecture and Implementation Approach

### Frontend Components

```tsx
type RecordingMode = "push_to_talk" | "continuous";

export function AudioRecorder(props: {
  mode: RecordingMode;
  languageCode: LanguageCode;
  onVoiceTurn: (blob: Blob, metadata: AudioMetadata) => Promise<void>;
  onFallbackText: (text: string) => Promise<void>;
}): JSX.Element;

export function WaveformVisualizer(props: {
  analyserNode: AnalyserNode | null;
  isActive: boolean;
}): JSX.Element;

export function LanguageSelector(props: {
  value: LanguageCode;
  onChange: (code: LanguageCode) => void;
}): JSX.Element;

export function TtsPlayer(props: {
  audioUrl: string;
  transcript: string;
  autoPlay: boolean;
}): JSX.Element;
```

### Backend Service Interfaces

```python
class ASRProvider(Protocol):
    async def transcribe(self, audio: bytes, mime_type: str, language_hint: str | None) -> AsrResponseModel: ...


class TranslationProviderClient(Protocol):
    async def translate(self, request: TranslateRequestModel) -> TranslateResponseModel: ...


class TTSProviderClient(Protocol):
    async def synthesize(self, request: TtsRequestModel) -> bytes: ...


async def run_voice_turn(request: VoiceTurnRequest, audio: UploadFile) -> VoiceTurnResponseModel: ...
```

### Local ASR with Whisper.cpp

Command template:

```txt
WHISPER_CPP_BINARY=/opt/whisper.cpp/build/bin/whisper-cli
WHISPER_CPP_MODEL_PATH=/models/ggml-large-v3.bin
WHISPER_CPP_ARGS=-l auto -otxt -ojf --print-progress false --no-timestamps
```

Backend flow:

1. Save upload to temp file under `/tmp/adhikarai/audio`.
2. Run `ffmpeg` to resample:

```txt
ffmpeg -y -i input.webm -ac 1 -ar 48000 output.wav
```

3. Spawn Whisper subprocess with timeout `ASR_TIMEOUT_SECONDS=12`.
4. Parse JSON output when available.
5. If Whisper.cpp does not provide confidence, estimate confidence from average token probability when available; otherwise set `0.80` and mark `confidence_method="provider_default"`.

### Hosted ASR with Groq

Endpoint:

```txt
POST https://api.groq.com/openai/v1/audio/transcriptions
Authorization: Bearer ${GROQ_API_KEY}
model=whisper-large-v3-turbo
response_format=verbose_json
```

Implementation must map Groq response to `AsrResponseModel`. If verbose confidence is unavailable, derive a conservative confidence:

```python
confidence = 0.85 if transcript.strip() and no_provider_error else 0.0
```

### Local Translation Microservice

Runs separately:

```txt
TRANSLATION_SERVICE_URL=http://localhost:8001
TRANSLATION_MODEL_EN_INDIC=ai4bharat/indictrans2-en-indic-1B
TRANSLATION_MODEL_INDIC_EN=ai4bharat/indictrans2-indic-en-1B
TRANSLATION_MODEL_INDIC_INDIC=ai4bharat/indictrans2-indic-indic-1B
```

Endpoint `POST http://localhost:8001/translate`:

```json
{
  "text": "मैं बिहार से किसान हूँ।",
  "source_lang": "hi",
  "target_lang": "en"
}
```

Response:

```json
{
  "translated_text": "I am a farmer from Bihar.",
  "source_lang": "hi",
  "target_lang": "en",
  "provider": "local_indictrans2",
  "cached": false
}
```

### Hosted Translation

Because AI4Bharat hosted API access and endpoint shape can vary by program/account, the implementation must not hard-code an undocumented URL. Use:

```txt
AI4BHARAT_TRANSLATE_URL=<provided hosted endpoint>
AI4BHARAT_API_KEY=<secret>
AI4BHARAT_TIMEOUT_SECONDS=3
GOOGLE_TRANSLATE_API_KEY=<secret fallback>
GOOGLE_TRANSLATE_URL=https://translation.googleapis.com/language/translate/v2
```

If `AI4BHARAT_TRANSLATE_URL` is empty and hosted translation is selected, startup must fail with:

```json
{
  "code": "TRANSLATION_PROVIDER_MISCONFIGURED",
  "message": "AI4Bharat hosted translation URL is not configured."
}
```

### TTS

Hosted Google Cloud TTS endpoint:

```txt
POST https://texttospeech.googleapis.com/v1/text:synthesize
```

Default voice mapping:

| Language | Google voice |
|---|---|
| `hi` | `hi-IN-Wavenet-A` |
| `bn` | `bn-IN-Wavenet-A` |
| `te` | `te-IN-Standard-A` |
| `mr` | `mr-IN-Wavenet-A` |
| `ta` | `ta-IN-Wavenet-A` |
| `gu` | `gu-IN-Wavenet-A` |
| `kn` | `kn-IN-Wavenet-A` |
| `ml` | `ml-IN-Wavenet-A` |
| `pa` | `pa-IN-Standard-A` |
| `or` | fallback `hi-IN-Wavenet-A` with text display if Odia voice unavailable in account |
| `en` | `en-IN-Wavenet-A` |

Local TTS config:

```txt
LOCAL_TTS_URL=http://localhost:8002
LOCAL_TTS_MODEL=ai4bharat/indic-parler-tts
LOCAL_TTS_TIMEOUT_SECONDS=8
```

The local TTS provider is wrapped behind `/synthesize`:

```json
{
  "text": "आपकी उम्र कितनी है?",
  "language_code": "hi",
  "speaker": "default_female",
  "speaking_rate": 1.0
}
```

### End-to-End Voice Pipeline

```python
async def run_voice_turn(request: VoiceTurnRequest, audio: UploadFile) -> VoiceTurnResponseModel:
    started = monotonic()
    asr = await asr_provider.transcribe(await audio.read(), audio.content_type, request.selected_language_code)
    if asr.confidence < settings.ASR_MIN_CONFIDENCE:
        return low_confidence_response(asr, request.selected_language_code)

    selected_lang = request.selected_language_code or asr.detected_language_code
    english_text = asr.transcript
    if selected_lang != "en":
        english_text = (await translator.translate(TranslateRequestModel(
            text=asr.transcript,
            source_lang=selected_lang,
            target_lang="en",
        ))).translated_text

    agent_response = await handle_chat_turn(ChatInputModel(
        session_id=request.session_id,
        message=english_text,
        language_code=selected_lang,
    ))

    localized_content = agent_response.content
    if selected_lang != "en":
        localized_content = (await translator.translate(TranslateRequestModel(
            text=agent_response.content,
            source_lang="en",
            target_lang=selected_lang,
        ))).translated_text

    audio_url = await tts_cache.get_or_create(localized_content, selected_lang)
    return VoiceTurnResponseModel(...)
```

## Environment-Specific Implementation Notes

| Component | Local / GPU production | Hosted demo / free tier |
|---|---|---|
| Voice provider | `VOICE_PROVIDER=local` | `VOICE_PROVIDER=groq` |
| Browser fallback | `NEXT_PUBLIC_ENABLE_BROWSER_ASR=true` | same |
| ASR model | `WHISPER_CPP_MODEL_PATH=/models/ggml-large-v3.bin` | `GROQ_WHISPER_MODEL=whisper-large-v3-turbo` |
| ASR endpoint | local subprocess | `GROQ_AUDIO_TRANSCRIPTIONS_URL=https://api.groq.com/openai/v1/audio/transcriptions` |
| LLM | `OLLAMA_MODEL=llama3.1:8b`, fallback `qwen2.5:7b` | `GROQ_CHAT_MODEL=llama-3.3-70b-versatile`, fallback `llama-3.1-8b-instant` |
| Translation | `TRANSLATION_PROVIDER=local_indictrans2` | `TRANSLATION_PROVIDER=ai4bharat_hosted` |
| Translation endpoint | `TRANSLATION_SERVICE_URL=http://localhost:8001` | `AI4BHARAT_TRANSLATE_URL=<account-provided>` |
| Translation fallback | none by default | `GOOGLE_TRANSLATE_URL=https://translation.googleapis.com/language/translate/v2` |
| TTS | `TTS_PROVIDER=local_indictts` | `TTS_PROVIDER=google` |
| TTS endpoint | `LOCAL_TTS_URL=http://localhost:8002` | `GOOGLE_TTS_URL=https://texttospeech.googleapis.com/v1/text:synthesize` |
| Latency timeout | `VOICE_TURN_TIMEOUT_SECONDS=20` | `VOICE_TURN_TIMEOUT_SECONDS=12` |
| Browser ASR threshold | `BROWSER_ASR_FALLBACK_AFTER_MS=2000` | same |
| Audio max upload | `VOICE_MAX_UPLOAD_MB=8` | `VOICE_MAX_UPLOAD_MB=8` |
| Silence detection | `NEXT_PUBLIC_SILENCE_MS=1500` | same |

Required env vars:

```txt
VOICE_PROVIDER=local|groq|browser
ASR_MIN_CONFIDENCE=0.70
VOICE_MAX_UTTERANCE_SECONDS=20
VOICE_MAX_UPLOAD_MB=8
BROWSER_ASR_FALLBACK_AFTER_MS=2000
NEXT_PUBLIC_SILENCE_MS=1500
NEXT_PUBLIC_SILENCE_THRESHOLD=0.018

GROQ_API_KEY=
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_WHISPER_MODEL=whisper-large-v3-turbo
GROQ_CHAT_MODEL=llama-3.3-70b-versatile

TRANSLATION_PROVIDER=local_indictrans2|ai4bharat_hosted|google
TRANSLATION_SERVICE_URL=http://localhost:8001
AI4BHARAT_TRANSLATE_URL=
AI4BHARAT_API_KEY=
GOOGLE_TRANSLATE_API_KEY=

TTS_PROVIDER=local_indictts|google
LOCAL_TTS_URL=http://localhost:8002
GOOGLE_TTS_URL=https://texttospeech.googleapis.com/v1/text:synthesize
GOOGLE_APPLICATION_CREDENTIALS=
TTS_CACHE_TTL_SECONDS=86400
TRANSLATION_CACHE_TTL_SECONDS=604800
```

## File and Folder Structure

```txt
adhikarai/
  backend/
    app/
      voice/
        __init__.py
        pipeline.py
        audio_utils.py
        confidence.py
        providers/
          base.py
          whisper_cpp.py
          groq_whisper.py
          browser_asr.py
      translation/
        __init__.py
        client.py
        providers/
          base.py
          local_indictrans2.py
          ai4bharat_hosted.py
          google_translate.py
        transliteration.py
        language_detection.py
      tts/
        __init__.py
        client.py
        cache.py
        providers/
          base.py
          local_indictts.py
          google_tts.py
      api/
        routes/
          voice.py
          translate.py
          tts.py
      db/
        models/
          voice_turn.py
          translation_event.py
          tts_event.py
      schemas/
        voice.py
        translation.py
        tts.py
    services/
      translation_service/
        main.py
        model_loader.py
        requirements.txt
      tts_service/
        main.py
        model_loader.py
        requirements.txt
    tests/
      unit/
        test_language_detection.py
        test_transliteration.py
        test_audio_validation.py
        test_voice_pipeline_low_confidence.py
      integration/
        test_voice_turn_groq_mock.py
        test_translate_cache.py
        test_tts_cache.py
  frontend/
    app/
      dev-voice/
        page.tsx
    components/
      voice/
        AudioRecorder.tsx
        WaveformVisualizer.tsx
        LanguageSelector.tsx
        TtsPlayer.tsx
        VoiceStatus.tsx
    lib/
      audio/
        wavEncoder.ts
        silenceDetection.ts
        browserAsr.ts
      i18n/
        languages.ts
        messages.ts
```

## Testing Requirements

### Unit Tests

1. `test_audio_rejects_large_upload`
   - Input: fake file size 9 MB.
   - Expected: `413 AUDIO_TOO_LARGE`.

2. `test_low_confidence_blocks_agent`
   - Mock ASR confidence `0.69`.
   - Expected: no call to `handle_chat_turn`, response type `low_confidence`.

3. `test_language_override_wins`
   - ASR detects `hi`, selected language `mr`.
   - Expected: response selected language `mr`.

4. `test_romanised_hindi_detection`
   - Input: "meri maa vidhwa hai".
   - Expected: romanised language detected as `hi`.

5. `test_translation_cache_key`
   - Same text/source/target/provider twice.
   - Expected: second response `cached=true`.

6. `test_tts_cache_key_includes_speaking_rate`
   - Same text but rates 1.0 and 0.75.
   - Expected: different cache keys.

### Integration Tests

1. `POST /voice/turn` with mocked Groq ASR
   - Mock transcript "I am a farmer from Bihar."
   - Expected: backend calls agent and returns question/result.

2. Local translation service
   - Request Hindi to English.
   - Expected: HTTP 200 with non-empty translated text.

3. Google TTS mocked
   - Mock `audioContent` base64.
   - Expected: audio file/Redis blob stored and URL returned.

4. Browser fallback
   - Simulate ASR timeout > 2000 ms in frontend unit test.
   - Expected: `startBrowserAsr()` called when supported.

### Manual Test Cases

1. Hindi push-to-talk
   - Speak: "Main Bihar se kisan hoon."
   - Expected: Hindi transcript, Hindi agent question audio.

2. Tamil typed romanised input
   - Type: "naan vivasayi"
   - Expected: romanised detection attempts Tamil transliteration; if confidence low, ask clarification rather than corrupting profile.

3. Noisy environment
   - Speak with fan noise.
   - Expected: waveform visible; if low confidence, localized retry prompt.

4. Slow network
   - Throttle network to Slow 3G.
   - Expected: UI shows upload progress; browser ASR fallback after 2 seconds if available; no frozen controls.

## Known Constraints and Edge Cases

1. Browser Web Speech API is not consistently available on all Android browsers.
2. Low-end phones may not record at 48 kHz; backend resampling is required.
3. Groq Whisper confidence may not always include word-level probabilities; conservative confidence fallback must be documented in metadata.
4. AI4Bharat hosted endpoint details require credentials. The app must use env-configured URL and fail clearly if missing.
5. Google TTS voice availability differs by account/region. If a voice name fails, fallback to same language standard voice; if language unavailable, return text-only response.
6. Translation can distort scheme names. Preserve known scheme names and currency amounts with placeholders before translation.
7. Multi-turn voice on 2G may exceed 4 seconds; target is hosted demo under normal network, while UI must remain usable on slow network.
8. Continuous mode may mis-detect silence in noisy homes. Push-to-talk remains primary.
9. Phase 3 does not implement the full production PWA offline queue.
10. Phase 3 does not store document audio or user recordings by default.

## Dependencies on Previous Phases

1. Phase 1 eligibility engine and scheme data.
2. Phase 2 LangGraph agent, Redis session state, and WebSocket chat.
3. Phase 2 profile/session tables for storing language and voice turn metadata.

