export type AgentMessageType = "question" | "result" | "clarification" | "error" | "state";
export type LanguageCode = "en" | "hi" | "bn" | "te" | "mr" | "ta" | "gu" | "kn" | "ml" | "pa" | "or";
export type VoiceProvider = "local" | "groq" | "browser";
export type TtsProvider = "local_indictts" | "google";

export interface ChatOutput {
  type: AgentMessageType;
  content: string;
  profile_completeness: number;
  session_id: string;
  payload?: unknown;
}

export interface CreateSessionResponse {
  session_id: string;
  profile_id: string;
  household_id: string;
  greeting: string;
  profile_completeness: number;
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
  timings: Record<string, number>;
  payload?: unknown;
}

export interface TtsResponse {
  audio_url: string;
  audio_mime_type: string;
  provider: TtsProvider;
  cached: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function createSession(organisationId: string, sessionId: string, languageCode: string) {
  const response = await fetch(`${API_BASE_URL}/agent/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      organisation_id: organisationId,
      session_id: sessionId || null,
      language_code: languageCode
    })
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return (await response.json()) as CreateSessionResponse;
}

export async function sendMessage(organisationId: string, sessionId: string, languageCode: string, message: string) {
  const response = await fetch(`${API_BASE_URL}/agent/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      organisation_id: organisationId,
      session_id: sessionId,
      language_code: languageCode,
      message
    })
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return (await response.json()) as ChatOutput;
}

export async function fetchSessionState(organisationId: string, sessionId: string) {
  const url = new URL(`${API_BASE_URL}/agent/sessions/${sessionId}`);
  url.searchParams.set("organisation_id", organisationId);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function sendVoiceTurn(
  organisationId: string,
  sessionId: string,
  selectedLanguageCode: string,
  audio: Blob,
  clientDurationMs?: number,
  onProgress?: (percent: number) => void
) {
  const form = new FormData();
  form.set("organisation_id", organisationId);
  form.set("session_id", sessionId);
  form.set("selected_language_code", selectedLanguageCode);
  if (clientDurationMs !== undefined) {
    form.set("client_duration_ms", String(clientDurationMs));
  }
  form.set("audio", audio, "voice.webm");
  onProgress?.(15);
  const response = await fetch(`${API_BASE_URL}/voice/turn`, { method: "POST", body: form });
  onProgress?.(85);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  onProgress?.(100);
  return (await response.json()) as VoiceTurnResponse;
}

export async function synthesizeSpeech(text: string, languageCode: string, speakingRate: number) {
  const response = await fetch(`${API_BASE_URL}/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language_code: languageCode, speaking_rate: speakingRate })
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return (await response.json()) as TtsResponse;
}

export function resolveAudioUrl(audioUrl: string) {
  return audioUrl.startsWith("http") ? audioUrl : `${API_BASE_URL}${audioUrl}`;
}
