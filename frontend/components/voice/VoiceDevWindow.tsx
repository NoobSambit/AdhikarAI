"use client";

import { Keyboard, RefreshCw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { createSession, fetchSessionState, LanguageCode, sendMessage, sendVoiceTurn, VoiceTurnResponse } from "@/lib/api";
import { AudioMetadata, AudioRecorder, RecordingMode } from "@/components/voice/AudioRecorder";
import { LanguageSelector } from "@/components/voice/LanguageSelector";
import { TtsPlayer } from "@/components/voice/TtsPlayer";
import { VoiceStatus } from "@/components/voice/VoiceStatus";
import { WaveformVisualizer } from "@/components/voice/WaveformVisualizer";
import { DebugStatePanel } from "@/components/dev-chat/DebugStatePanel";
import { DevMessage, MessageList } from "@/components/dev-chat/MessageList";
import { voiceMessage } from "@/lib/i18n/messages";

const DEFAULT_ORG = "00000000-0000-0000-0000-000000000001";

export function VoiceDevWindow() {
  const [organisationId, setOrganisationId] = useState(DEFAULT_ORG);
  const [sessionId, setSessionId] = useState("");
  const [languageCode, setLanguageCode] = useState<LanguageCode>("en");
  const [mode, setMode] = useState<RecordingMode>("push_to_talk");
  const [messages, setMessages] = useState<DevMessage[]>([]);
  const [debug, setDebug] = useState<unknown>(null);
  const [status, setStatus] = useState("Ready");
  const [progress, setProgress] = useState(0);
  const [fallbackVisible, setFallbackVisible] = useState(false);
  const [amplitudes, setAmplitudes] = useState<number[]>([]);
  const [typedFallback, setTypedFallback] = useState("");
  const [lastVoice, setLastVoice] = useState<VoiceTurnResponse | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("language_code") as LanguageCode | null;
    if (stored) setLanguageCode(stored);
  }, []);

  function updateLanguage(code: LanguageCode) {
    setLanguageCode(code);
    window.localStorage.setItem("language_code", code);
  }

  async function startSession() {
    setBusy(true);
    try {
      const session = await createSession(organisationId, sessionId, languageCode);
      setSessionId(session.session_id);
      setMessages([{ role: "assistant", content: session.greeting }]);
      setDebug(session);
      setStatus("Ready");
    } finally {
      setBusy(false);
    }
  }

  async function refreshState() {
    if (!sessionId) return;
    setDebug(await fetchSessionState(organisationId, sessionId));
  }

  async function handleVoiceTurn(blob: Blob, metadata: AudioMetadata) {
    if (!sessionId) return;
    setBusy(true);
    setProgress(5);
    setFallbackVisible(false);
    try {
      const response = await sendVoiceTurn(organisationId, sessionId, languageCode, blob, metadata.durationMs, setProgress);
      setLastVoice(response);
      if (response.transcript) {
        setMessages((current) => [...current, { role: "user", content: response.transcript ?? "" }]);
      }
      setMessages((current) => [...current, { role: "assistant", content: response.content }]);
      setDebug(response);
      setStatus(response.type === "low_confidence" ? response.content : "Ready");
      setFallbackVisible(response.type === "low_confidence");
    } catch {
      setStatus(voiceMessage(languageCode, "network_failure"));
      setFallbackVisible(true);
    } finally {
      setBusy(false);
    }
  }

  async function handleBrowserFallback(text: string) {
    if (!sessionId) return;
    setTypedFallback(text);
    setStatus(voiceMessage(languageCode, "slow_internet"));
    setFallbackVisible(true);
  }

  async function submitTypedFallback(event: FormEvent) {
    event.preventDefault();
    if (!sessionId || !typedFallback.trim()) return;
    const text = typedFallback.trim();
    setTypedFallback("");
    setMessages((current) => [...current, { role: "user", content: text }]);
    setBusy(true);
    try {
      const response = await sendMessage(organisationId, sessionId, languageCode, text);
      setMessages((current) => [...current, { role: "assistant", content: response.content }]);
      setDebug(response);
      setStatus("Ready");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <div className="shell voiceShell">
        <aside className="panel">
          <div className="field">
            <label htmlFor="voice-org">Organisation ID</label>
            <input id="voice-org" value={organisationId} onChange={(event) => setOrganisationId(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="voice-session">Session ID</label>
            <input id="voice-session" value={sessionId} onChange={(event) => setSessionId(event.target.value)} />
          </div>
          <LanguageSelector value={languageCode} onChange={updateLanguage} />
          <div className="segmented" role="group" aria-label="Recording mode">
            <button className={mode === "push_to_talk" ? "active" : ""} type="button" onClick={() => setMode("push_to_talk")}>
              Hold
            </button>
            <button className={mode === "continuous" ? "active" : ""} type="button" onClick={() => setMode("continuous")}>
              Continuous
            </button>
          </div>
          <button className="button" type="button" onClick={startSession} disabled={busy}>
            Start or Resume
          </button>
          <button className="button secondary" type="button" onClick={refreshState} disabled={busy || !sessionId}>
            <RefreshCw aria-hidden="true" size={18} />
            Refresh State
          </button>
          <DebugStatePanel value={debug} />
        </aside>
        <section className="chat">
          <div className="chatHeader">AdhikarAI Phase 3 Dev Voice</div>
          <MessageList messages={messages} />
          <div className="voiceComposer">
            <WaveformVisualizer amplitudes={amplitudes} isActive={busy || progress > 0} />
            <VoiceStatus status={status} progress={progress} fallbackVisible={fallbackVisible} />
            <AudioRecorder
              mode={mode}
              languageCode={languageCode}
              onVoiceTurn={handleVoiceTurn}
              onFallbackText={handleBrowserFallback}
              onAmplitudes={setAmplitudes}
              onStatus={(nextStatus, showFallback) => {
                setStatus(nextStatus);
                setFallbackVisible(Boolean(showFallback));
              }}
            />
            <form className="composer fallbackComposer" onSubmit={submitTypedFallback}>
              <textarea
                aria-label={voiceMessage(languageCode, "type_fallback")}
                value={typedFallback}
                onChange={(event) => setTypedFallback(event.target.value)}
                rows={2}
                disabled={!sessionId || busy}
              />
              <button className="button" type="submit" disabled={!sessionId || busy || !typedFallback.trim()}>
                <Keyboard aria-hidden="true" size={18} />
              </button>
            </form>
            <TtsPlayer audioUrl={lastVoice?.audio_url} transcript={lastVoice?.content ?? ""} autoPlay />
          </div>
        </section>
      </div>
    </main>
  );
}
