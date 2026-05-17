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

export interface SendOtpResponse {
  challenge_id: string;
  masked_phone: string;
  retry_after_seconds: number;
}

export interface AuthUser {
  id: string;
  phone_e164: string;
  language_code: LanguageCode;
  primary_profile_id?: string;
  high_contrast_enabled: boolean;
  font_size: "default" | "large" | "extra_large";
  notification_opt_in: boolean;
}

export interface ChecklistItemView {
  document_name: string;
  is_mandatory: boolean;
  status: "not_gathered" | "gathered" | "verified" | "rejected";
  accepted_substitutes: Array<Record<string, unknown>>;
}

export interface SchemeCardView {
  scheme_id: string;
  name: string;
  plain_language_benefit: string;
  benefit_amount: string;
  eligibility_status: "eligible" | "near_miss" | "ineligible";
  failed_criterion?: string;
  how_to_qualify?: string;
  documents: ChecklistItemView[];
  application_steps: string[];
  application_url?: string;
  saved: boolean;
}

export type DashboardRole = "super_admin" | "ngo_admin" | "operator";

export interface DashboardMe {
  member_id: string;
  organisation_id: string;
  role: DashboardRole;
  display_name: string;
  permissions: string[];
}

export interface DashboardBeneficiary {
  id: string;
  name: string;
  phone_e164?: string;
  state_code: string;
  language_code: string;
  village?: string;
  district?: string;
  profile_id: string;
  assigned_operator_id?: string;
  application_statuses: Array<{ id?: string; scheme_id: string; status: string }>;
  follow_up?: { id?: string; due_date: string; reason?: string; status?: string };
}

export interface DashboardListResponse {
  items: DashboardBeneficiary[];
  total: number;
}

export interface QualityFlag {
  id: string;
  flag_type: string;
  severity: "info" | "warning" | "critical";
  details: Record<string, unknown>;
  reviewed_at?: string;
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
  const response = await fetch(`${API_BASE_URL}/voice/turn`, { method: "POST", body: form, credentials: "include" });
  onProgress?.(85);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  onProgress?.(100);
  return (await response.json()) as VoiceTurnResponse;
}

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) }
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return (await response.json()) as T;
}

export async function sendOtp(organisationId: string, phoneE164: string) {
  return jsonFetch<SendOtpResponse>("/auth/send-otp", {
    method: "POST",
    body: JSON.stringify({ organisation_id: organisationId, phone_e164: phoneE164 })
  });
}

export async function verifyOtp(organisationId: string, challengeId: string, otp: string, guestProfileId?: string, languageCode: LanguageCode = "hi") {
  return jsonFetch<{ user: AuthUser; migrated_guest_profile: boolean }>("/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({ organisation_id: organisationId, challenge_id: challengeId, otp, guest_profile_id: guestProfileId, language_code: languageCode })
  });
}

export async function getMe() {
  return jsonFetch<{ user: AuthUser; primary_profile?: { id: string } }>("/me");
}

export async function updateMe(settings: Partial<Pick<AuthUser, "language_code" | "high_contrast_enabled" | "font_size" | "notification_opt_in">> & { guest_profile_id?: string }) {
  return jsonFetch<{ user: AuthUser }>("/me", { method: "PATCH", body: JSON.stringify(settings) });
}

export async function saveScheme(profileId: string, schemeId: string) {
  return jsonFetch<{ saved: boolean; reminder_scheduled_at: string }>("/saved-schemes", {
    method: "POST",
    body: JSON.stringify({ profile_id: profileId, scheme_id: schemeId })
  });
}

export async function updateChecklist(payload: {
  profile_id: string;
  scheme_id: string;
  document_name: string;
  status: ChecklistItemView["status"];
  idempotency_key: string;
  is_mandatory?: boolean;
  accepted_substitutes?: Array<Record<string, unknown>>;
}) {
  return jsonFetch<{ items: ChecklistItemView[]; ready_to_apply: boolean }>("/checklists", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function updateApplicationStatus(profileId: string, schemeId: string, status: string) {
  return jsonFetch("/application-status", {
    method: "PATCH",
    body: JSON.stringify({ profile_id: profileId, scheme_id: schemeId, status })
  });
}

export async function syncOffline(events: Array<Record<string, unknown>>) {
  return jsonFetch("/offline-sync", { method: "POST", body: JSON.stringify({ events }) });
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

export async function getDashboardMe() {
  return jsonFetch<DashboardMe>("/dashboard/me");
}

export async function listDashboardBeneficiaries(params: Record<string, string> = {}) {
  const query = new URLSearchParams(params);
  return jsonFetch<DashboardListResponse>(`/dashboard/beneficiaries${query.size ? `?${query}` : ""}`);
}

export async function createDashboardBeneficiary(payload: Record<string, unknown>) {
  return jsonFetch<DashboardBeneficiary>("/dashboard/beneficiaries", { method: "POST", body: JSON.stringify(payload) });
}

export async function getStatusBoard() {
  return jsonFetch<Record<string, Array<Record<string, string>>>>("/dashboard/status-board");
}

export async function updateDashboardApplicationStatus(statusId: string, status: string) {
  return jsonFetch(`/dashboard/application-status/${statusId}`, { method: "PATCH", body: JSON.stringify({ status }) });
}

export async function getSchemeGuide() {
  return jsonFetch<{ items: Array<Record<string, string>> }>("/dashboard/scheme-guide");
}

export async function getUnmatchedQueries() {
  return jsonFetch<{ items: Array<{ normalized_query_text: string; frequency: number; languages: string[]; latest_at: string }> }>("/admin/unmatched-queries");
}

export async function getQualityFlags() {
  return jsonFetch<{ items: QualityFlag[] }>("/admin/quality-flags");
}

export async function markQualityFlagReviewed(flagId: string, reviewNotes: string) {
  return jsonFetch(`/admin/quality-flags/${flagId}/review`, { method: "POST", body: JSON.stringify({ review_notes: reviewNotes }) });
}
