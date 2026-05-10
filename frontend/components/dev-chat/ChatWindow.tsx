"use client";

import { Send } from "lucide-react";
import { FormEvent, useState } from "react";
import { createSession, fetchSessionState, sendMessage } from "@/lib/api";
import { DebugStatePanel } from "./DebugStatePanel";
import { DevMessage, MessageList } from "./MessageList";

const DEFAULT_ORG = "00000000-0000-0000-0000-000000000001";
const LANGUAGES = ["en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or"];

export function ChatWindow() {
  const [organisationId, setOrganisationId] = useState(DEFAULT_ORG);
  const [sessionId, setSessionId] = useState("");
  const [languageCode, setLanguageCode] = useState("en");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<DevMessage[]>([]);
  const [debug, setDebug] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function startSession() {
    setBusy(true);
    try {
      const session = await createSession(organisationId, sessionId, languageCode);
      setSessionId(session.session_id);
      setMessages([{ role: "assistant", content: session.greeting }]);
      setDebug(session);
    } finally {
      setBusy(false);
    }
  }

  async function refreshState() {
    if (!sessionId) return;
    setDebug(await fetchSessionState(organisationId, sessionId));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!sessionId || !message.trim()) return;
    const userText = message.trim();
    setMessage("");
    setMessages((current) => [...current, { role: "user", content: userText }]);
    setBusy(true);
    try {
      const response = await sendMessage(organisationId, sessionId, languageCode, userText);
      setMessages((current) => [...current, { role: "assistant", content: response.content }]);
      setDebug(response);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <div className="shell">
        <aside className="panel">
          <div className="field">
            <label htmlFor="org">Organisation ID</label>
            <input id="org" value={organisationId} onChange={(event) => setOrganisationId(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="session">Session ID</label>
            <input id="session" value={sessionId} onChange={(event) => setSessionId(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="language">Language</label>
            <select id="language" value={languageCode} onChange={(event) => setLanguageCode(event.target.value)}>
              {LANGUAGES.map((language) => (
                <option key={language} value={language}>
                  {language}
                </option>
              ))}
            </select>
          </div>
          <button className="button" type="button" onClick={startSession} disabled={busy}>
            Start or Resume
          </button>
          <button className="button secondary" type="button" onClick={refreshState} disabled={busy || !sessionId}>
            Refresh State
          </button>
          <DebugStatePanel value={debug} />
        </aside>
        <section className="chat">
          <div className="chatHeader">AdhikarAI Phase 2 Dev Chat</div>
          <MessageList messages={messages} />
          <form className="composer" onSubmit={onSubmit}>
            <textarea
              aria-label="Message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              rows={2}
              disabled={!sessionId || busy}
            />
            <button className="button" type="submit" disabled={!sessionId || busy}>
              <Send aria-hidden="true" size={18} />
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
