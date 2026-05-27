# Voice and Multilingual Pipeline

AdhikarAI is built voice-first. A rural beneficiary should be able to interact entirely in their native language by speaking — without needing to read or type.

---

## Pipeline Overview

A voice turn processes audio through four sequential stages:

```
[Browser mic] → [ASR] → [Translation to English] → [Agent] → [Translation to user language] → [TTS] → [Browser audio]
```

Each stage is backed by interchangeable providers selected at runtime via environment variables.

---

## Stage 1: Audio Recording (Browser)

**Component**: `frontend/components/voice/AudioRecorder.tsx`

- Uses the Web Audio API (`MediaRecorder`) to capture microphone audio.
- Supports push-to-talk and continuous recording modes.
- Records as WebM/Opus (browser default) or WAV.
- Waveform visualization via `WaveformVisualizer.tsx`.
- Language selection via `LanguageSelector.tsx`.
- Silence detection: stops recording after `NEXT_PUBLIC_SILENCE_MS` ms of audio below `NEXT_PUBLIC_SILENCE_THRESHOLD` amplitude.

---

## Stage 2: ASR — Automatic Speech Recognition

**Route**: `POST /voice/asr` (ASR only) or `POST /voice/turn` (full pipeline)

**File**: `app/voice/pipeline.py`, `app/voice/providers/`

### Providers

| Provider | Variable | Notes |
|---|---|---|
| `local` (Whisper.cpp) | `VOICE_PROVIDER=local` | CUDA-accelerated; binary path configurable |
| `groq` (Groq Whisper API) | `VOICE_PROVIDER=groq` | Requires `GROQ_API_KEY` |
| `browser` | Browser-side Web Speech API | Fallback for devices without server ASR |

### ASR Response

```json
{
  "transcript": "मुझे विधवा पेंशन के बारे में जानना है",
  "confidence": 0.92,
  "detected_language_code": "hi",
  "provider": "groq_whisper"
}
```

### Low-Confidence Handling

If `confidence < ASR_MIN_CONFIDENCE` (default 0.70):
- The pipeline returns `type: "low_confidence"` immediately.
- A localized message is returned in the beneficiary's selected language (e.g., "मैं आपकी आवाज़ नहीं सुन पाया. कृपया फिर से बोलें").
- The agent is **not called**.
- The voice turn is persisted with `status="low_confidence"`.

### Localized Fallback Messages

**File**: `app/voice/localized_messages.py`

Messages exist for these scenarios in all supported languages:
- `low_confidence`: "I couldn't hear you clearly. Please speak again."
- `asr_error`: "Something went wrong with voice. Please type your message."
- `agent_error`: "I couldn't understand. Please try again."

---

## Stage 3: Translation

**File**: `app/translation/client.py`, `app/translation/providers/`

If the detected language is not English, the transcript is translated to English before being sent to the agent.

### Providers

| Provider | Variable | Notes |
|---|---|---|
| `local_indictrans2` | `TRANSLATION_PROVIDER=local_indictrans2` | Requires IndicTrans2 local HTTP service at `TRANSLATION_SERVICE_URL` |
| `ai4bharat_hosted` | `TRANSLATION_PROVIDER=ai4bharat_hosted` | Requires `AI4BHARAT_TRANSLATE_URL` and `AI4BHARAT_API_KEY` |
| `google` | `TRANSLATION_PROVIDER=google` | Fallback; requires `GOOGLE_TRANSLATE_API_KEY` |

### Caching

Translations are cached in Redis keyed by `(provider, source_lang, target_lang, sha256(text)[:16])` with `TRANSLATION_CACHE_TTL_SECONDS` TTL (default 7 days). Cache hits avoid provider API calls.

---

## Stage 4: Agent

The English text is passed to the LangGraph agent via `handle_chat_turn()`. The agent returns a localized-language-agnostic English response.

---

## Stage 5: Back-Translation

The agent's English response is translated back to the beneficiary's selected language using the same translation provider and cache.

---

## Stage 6: TTS — Text-to-Speech

**File**: `app/tts/client.py`, `app/tts/providers/`

The translated response is synthesized to audio.

### Providers

| Provider | Variable | Notes |
|---|---|---|
| `local_indictts` | `TTS_PROVIDER=local_indictts` | Requires IndicTTS-compatible local HTTP service |
| `google` | `TTS_PROVIDER=google` | Requires `GOOGLE_APPLICATION_CREDENTIALS` |

### Response

```json
{
  "audio_url": "/voice/audio/abc123.mp3",
  "duration_ms": 3200
}
```

TTS audio URLs are cached in Redis with `TTS_CACHE_TTL_SECONDS` TTL (default 24 hours).

---

## Voice Turn Response

A complete voice turn returns:

```json
{
  "type": "question",
  "transcript": "मुझे विधवा पेंशन के बारे में जानना है",
  "detected_language_code": "hi",
  "selected_language_code": "hi",
  "confidence": 0.92,
  "content": "आपकी आयु क्या है?",
  "audio_url": "/voice/audio/response.mp3",
  "profile_completeness": 35,
  "timings": {
    "asr_ms": 840,
    "translation_to_en_ms": 120,
    "agent_ms": 1200,
    "translation_from_en_ms": 115,
    "tts_ms": 650,
    "total_ms": 2925
  }
}
```

Target latency for hosted demo: < 4 seconds total.

---

## WebSocket Voice (`/ws/voice`)

For lower-latency streaming, the voice pipeline also supports a WebSocket endpoint:

```
Client → {type: "start", session_id, language_code, mime_type}
Client → [binary audio chunks...]
Client → {type: "end"}
Server → VoiceTurnResponseModel (same as POST /voice/turn)
```

The WebSocket accumulates binary chunks and runs the full pipeline on `end`. The same `VoicePipeline` is used as for the REST endpoint.

---

## Voice Turn Persistence

Every voice turn is persisted to the `voice_turns` table:

| Column | Content |
|---|---|
| `provider` | ASR provider used |
| `transcript` | Raw ASR transcript |
| `normalized_transcript` | English-translated transcript |
| `detected_language_code` | Language detected by ASR |
| `selected_language_code` | Language chosen by user |
| `asr_confidence` | ASR confidence score |
| `status` | `agent_completed` or `low_confidence` or `asr_error` |
| `timings` | JSONB with per-stage latencies |
| `input_audio_mime_type` | MIME type of uploaded audio |
| `input_audio_size_bytes` | Size of audio upload |
| `input_audio_duration_ms` | Client-reported duration |

**Raw audio is never stored** (`STORE_AUDIO_DEBUG=false` by default).

---

## Language Support

Languages are identified by BCP-47 codes. The following languages are expected to be supported by IndicTrans2 and IndicTTS:

- Hindi (`hi`), Bengali (`bn`), Telugu (`te`), Marathi (`mr`), Tamil (`ta`)
- Gujarati (`gu`), Kannada (`kn`), Malayalam (`ml`), Punjabi (`pa`)
- Odia (`or`), Assamese (`as`), Urdu (`ur`)

Language detection is handled by the ASR provider. The user can also manually select their language via the language selector component.

---

## Known Limitations

- Real voice providers (Whisper.cpp, Groq, IndicTrans2, AI4Bharat, IndicTTS, Google) are **wired but not smoke-tested** against actual hardware or credentials in CI.
- Browser ASR fallback (`VOICE_PROVIDER=browser`) relies on the Web Speech API, which is not available in all browsers and may not support regional Indian languages.
- The BROWSER_ASR_FALLBACK is client-side only; no server-side processing.
- Voice WebSocket is not tested in the browser.
- TTS audio URLs are currently ephemeral (no persistent storage); long-lived cached URLs may break if the backend restarts without a persistent Redis.
