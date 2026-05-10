export type AgentMessageType = "question" | "result" | "clarification" | "error" | "state";

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
