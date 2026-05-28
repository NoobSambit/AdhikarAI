"use client";

import { Bookmark, CheckCircle2, ChevronDown, Clock3, Home, Keyboard, Save, Search, User, Volume2 } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { AudioMetadata, AudioRecorder } from "@/components/voice/AudioRecorder";
import { LanguageSelector } from "@/components/voice/LanguageSelector";
import { TtsPlayer } from "@/components/voice/TtsPlayer";
import { VoiceStatus } from "@/components/voice/VoiceStatus";
import { WaveformVisualizer } from "@/components/voice/WaveformVisualizer";
import { InstallPrompt } from "@/components/pwa/InstallPrompt";
import {
  AuthUser,
  createSession,
  getMe,
  LanguageCode,
  saveScheme,
  SchemeCardView,
  sendOtp,
  sendMessage,
  sendVoiceTurn,
  updateApplicationStatus,
  updateChecklist,
  updateMe,
  verifyOtp,
  VoiceTurnResponse
} from "@/lib/api";
import { districtsForState, INDIA_STATES, stateLabelFromCode, VILLAGE_SUGGESTIONS_BY_DISTRICT } from "@/lib/indiaLocations";
import {
  appendConversationTurn,
  cacheSchemes,
  enqueueSync,
  getCachedSchemes,
  getHistory,
  getOrCreateGuestProfile,
  GuestProfile,
  saveGuestProfile,
  saveLocalChecklist
} from "@/lib/offlineDb";
import { voiceMessage } from "@/lib/i18n/messages";

const DEFAULT_ORG = "00000000-0000-0000-0000-000000000001";
type Tab = "home" | "schemes" | "history" | "profile";

const SAMPLE_SCHEMES: SchemeCardView[] = [
  {
    scheme_id: "pm_kisan",
    name: "PM-KISAN",
    plain_language_benefit: "You get INR 6,000 per year directly in your bank account.",
    benefit_amount: "INR 6,000/year",
    eligibility_status: "eligible",
    documents: [
      { document_name: "Aadhaar card", is_mandatory: true, status: "not_gathered", accepted_substitutes: [] },
      { document_name: "Bank passbook", is_mandatory: true, status: "not_gathered", accepted_substitutes: [] },
      {
        document_name: "Land record",
        is_mandatory: true,
        status: "not_gathered",
        accepted_substitutes: [{ name: "Patta copy", instructions: "Ask your tehsil office for a signed copy." }]
      }
    ],
    application_steps: ["Collect documents", "Open PM-KISAN portal", "Submit details and save receipt"],
    application_url: "https://pmkisan.gov.in/",
    saved: false
  },
  {
    scheme_id: "widow_pension",
    name: "Widow Pension",
    plain_language_benefit: "Monthly pension support for eligible widowed women.",
    benefit_amount: "State amount varies",
    eligibility_status: "near_miss",
    failed_criterion: "Income certificate missing",
    how_to_qualify: "Get an income certificate or accepted substitute from the tehsil office.",
    documents: [
      {
        document_name: "Income certificate",
        is_mandatory: true,
        status: "not_gathered",
        accepted_substitutes: [{ name: "BPL card", instructions: "Use if the state accepts BPL proof." }]
      }
    ],
    application_steps: ["Gather proof", "Visit state pension portal or CSC", "Track receipt"],
    saved: false
  }
];

export default function HomePage() {
  const [tab, setTab] = useState<Tab>("home");
  const [languageCode, setLanguageCode] = useState<LanguageCode>("hi");
  const [sessionId, setSessionId] = useState("");
  const [profileId, setProfileId] = useState("");
  const [guestProfile, setGuestProfile] = useState<GuestProfile | null>(null);
  const [status, setStatus] = useState("Tap mic and speak your situation.");
  const [fallbackVisible, setFallbackVisible] = useState(false);
  const [typed, setTyped] = useState("");
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([]);
  const [amplitudes, setAmplitudes] = useState<number[]>([]);
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [schemes, setSchemes] = useState<SchemeCardView[]>(SAMPLE_SCHEMES);
  const [lastVoice, setLastVoice] = useState<VoiceTurnResponse | null>(null);
  const [loginPrompt, setLoginPrompt] = useState("");
  const [profileNotice, setProfileNotice] = useState("");
  const [profileSavedAt, setProfileSavedAt] = useState("");
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [phoneE164, setPhoneE164] = useState("+91");
  const [otp, setOtp] = useState("");
  const [otpChallengeId, setOtpChallengeId] = useState("");
  const [accountNotice, setAccountNotice] = useState("");
  const [history, setHistory] = useState<Array<{ id: string; updated_at: string; language_code: string; matched_scheme_count: number }>>([]);

  useEffect(() => {
    async function boot() {
      const storedLanguage = (window.localStorage.getItem("language_code") as LanguageCode | null) ?? "hi";
      setLanguageCode(storedLanguage);
      const guest = await getOrCreateGuestProfile(storedLanguage);
      setGuestProfile(guest);
      setProfileId(guest.id);
      setSessionId(`guest_${guest.id.slice(0, 8)}`);
      const cached = await getCachedSchemes();
      if (cached.length) setSchemes(cached);
      setHistory(await getHistory());
      applyAccessibility(guest);
      try {
        const me = await getMe();
        setAuthUser(me.user);
        setProfileId(me.user.primary_profile_id ?? guest.id);
      } catch {
        setAuthUser(null);
      }
    }
    boot();
  }, []);

  const matched = useMemo(() => schemes.filter((scheme) => scheme.eligibility_status === "eligible"), [schemes]);
  const nearMiss = useMemo(() => schemes.filter((scheme) => scheme.eligibility_status === "near_miss"), [schemes]);
  const profileCompleteness = useMemo(() => computeLocalProfileCompleteness(guestProfile), [guestProfile]);
  const selectedStateLabel = stateLabelFromCode(guestProfile?.state_code) || guestProfile?.state_code || "";
  const districtOptions = useMemo(() => districtsForState(guestProfile?.state_code), [guestProfile?.state_code]);
  const villageOptions = useMemo(() => VILLAGE_SUGGESTIONS_BY_DISTRICT[guestProfile?.district ?? ""] ?? [], [guestProfile?.district]);
  const stateSelectOptions = useMemo(() => INDIA_STATES.map((state) => ({ value: state.code, label: state.name, meta: state.code })), []);
  const districtSelectOptions = useMemo(() => districtOptions.map((district) => ({ value: district, label: district })), [districtOptions]);
  const villageSelectOptions = useMemo(() => villageOptions.map((village) => ({ value: village, label: village })), [villageOptions]);

  async function updateLanguage(code: LanguageCode) {
    setLanguageCode(code);
    window.localStorage.setItem("language_code", code);
    if (guestProfile) {
      const next = { ...guestProfile, language_code: code };
      setGuestProfile(next);
      await saveGuestProfile(next);
    }
  }

  async function ensureSession() {
    if (sessionId && !sessionId.startsWith("guest_")) return sessionId;
    const session = await createSession(DEFAULT_ORG, "", languageCode);
    setSessionId(session.session_id);
    setProfileId(session.profile_id);
    setMessages([{ role: "assistant", content: session.greeting }]);
    return session.session_id;
  }

  async function handleVoiceTurn(blob: Blob, metadata: AudioMetadata) {
    setBusy(true);
    setProgress(10);
    setFallbackVisible(false);
    try {
      const activeSession = await ensureSession();
      const response = await sendVoiceTurn(DEFAULT_ORG, activeSession, languageCode, blob, metadata.durationMs, setProgress);
      setLastVoice(response);
      await applyAgentResponse(activeSession, response.transcript, response.content, response.payload);
      setStatus(response.type === "low_confidence" ? response.content : "Ready. You can speak again.");
      setFallbackVisible(response.type === "low_confidence");
    } catch {
      setStatus(voiceMessage(languageCode, "network_failure"));
      setFallbackVisible(true);
    } finally {
      setBusy(false);
    }
  }

  async function submitTyped(event: FormEvent) {
    event.preventDefault();
    if (!typed.trim()) return;
    const text = typed.trim();
    setTyped("");
    setBusy(true);
    try {
      const activeSession = await ensureSession();
      const response = await sendMessage(DEFAULT_ORG, activeSession, languageCode, text);
      await applyAgentResponse(activeSession, text, response.content, response.payload);
      setStatus("Ready. Tap mic or type again.");
    } catch {
      setStatus("Internet is slow. Your message is saved here. Tap mic or type again.");
      setFallbackVisible(true);
      await enqueueSync("conversation.message", { session_id: sessionId, message: text, language_code: languageCode });
    } finally {
      setBusy(false);
    }
  }

  async function applyAgentResponse(activeSession: string, userText?: string | null, assistantText?: string, payload?: unknown) {
    if (userText) {
      setMessages((current) => [...current, { role: "user", content: userText }]);
      await appendConversationTurn(activeSession, languageCode, "user", userText);
    }
    if (assistantText) {
      setMessages((current) => [...current, { role: "assistant", content: assistantText }]);
      await appendConversationTurn(activeSession, languageCode, "assistant", assistantText, matched.length);
    }
    const nextCards = schemeCardsFromPayload(payload);
    if (nextCards.length) {
      setSchemes(nextCards);
      await cacheSchemes(nextCards);
      setTab("schemes");
    }
    setHistory(await getHistory());
  }

  async function toggleChecklist(scheme: SchemeCardView, documentName: string) {
    const nextStatus: "not_gathered" | "gathered" = scheme.documents.find((doc) => doc.document_name === documentName)?.status === "gathered" ? "not_gathered" : "gathered";
    const local = { id: `${scheme.scheme_id}:${documentName}`, scheme_id: scheme.scheme_id, document_name: documentName, status: nextStatus, updated_at: new Date().toISOString() };
    await saveLocalChecklist(local);
    setSchemes((current) =>
      current.map((item) =>
        item.scheme_id === scheme.scheme_id
          ? { ...item, documents: item.documents.map((doc) => (doc.document_name === documentName ? { ...doc, status: nextStatus } : doc)) }
          : item
      )
    );
    try {
      await updateChecklist({
        profile_id: profileId,
        scheme_id: scheme.scheme_id,
        document_name: documentName,
        status: nextStatus,
        idempotency_key: crypto.randomUUID(),
        is_mandatory: true
      });
    } catch {
      await enqueueSync("checklist.update", local);
      setStatus("Saved offline. It will sync when internet returns. You can tap mic or type.");
    }
  }

  async function handleBookmark(scheme: SchemeCardView) {
    if (sessionId.startsWith("guest_")) {
      setLoginPrompt("Login with phone to save this scheme.");
      setTab("profile");
      return;
    }
    await saveScheme(profileId, scheme.scheme_id);
    setSchemes((current) => current.map((item) => (item.scheme_id === scheme.scheme_id ? { ...item, saved: true } : item)));
  }

  async function updateAccessibility(next: Partial<GuestProfile>) {
    if (!guestProfile) return;
    const profile = { ...guestProfile, ...next };
    setGuestProfile(profile);
    await saveGuestProfile(profile);
    applyAccessibility(profile);
    try {
      await updateMe({
        language_code: profile.language_code,
        high_contrast_enabled: profile.high_contrast_enabled,
        font_size: profile.font_size,
        guest_profile_id: profile.id
      });
    } catch {
      await enqueueSync("profile.settings", profile);
    }
  }

  function updateProfileDraft(next: Partial<GuestProfile>) {
    setProfileNotice("");
    setProfileSavedAt("");
    setGuestProfile((current) => (current ? { ...current, ...next } : current));
  }

  async function saveProfileDetails() {
    if (!guestProfile) return null;
    await saveGuestProfile(guestProfile);
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    console.info("Guest profile saved locally", { guest_profile_id: guestProfile.id, saved_at: time });
    setProfileSavedAt(time);
    setProfileNotice(`Saved on this phone at ${time}.`);
    return guestProfile;
  }

  async function requestOtp() {
    setAccountNotice("");
    setBusy(true);
    try {
      const response = await sendOtp(DEFAULT_ORG, phoneE164.trim());
      setOtpChallengeId(response.challenge_id);
      setAccountNotice(`OTP sent to ${response.masked_phone}.`);
    } catch {
      setAccountNotice("Could not send OTP. Check phone number and internet.");
    } finally {
      setBusy(false);
    }
  }

  async function completeOtpLogin() {
    if (!guestProfile || !otpChallengeId) return;
    setAccountNotice("");
    setBusy(true);
    try {
      const response = await verifyOtp(DEFAULT_ORG, otpChallengeId, otp.trim(), guestProfile.id, languageCode);
      setAuthUser(response.user);
      setProfileId(response.user.primary_profile_id ?? profileId);
      setAccountNotice(response.migrated_guest_profile ? "Account ready. Your guest profile is linked." : "Signed in.");
      setOtp("");
      setOtpChallengeId("");
    } catch {
      setAccountNotice("OTP did not work. Try again or request a new OTP.");
    } finally {
      setBusy(false);
    }
  }

  async function findSchemesWithProfile() {
    if (!guestProfile) return;
    const stateCode = guestProfile.state_code?.trim().toUpperCase();
    if (!stateCode) {
      setProfileNotice("Add state before finding schemes.");
      return;
    }
    const profile = { ...guestProfile, state_code: stateCode };
    setGuestProfile(profile);
    setBusy(true);
    try {
      await saveGuestProfile(profile);
      const activeSession = await ensureSession();
      const message = buildProfileFactsMessage(profile);
      const response = await sendMessage(DEFAULT_ORG, activeSession, languageCode, message);
      await applyAgentResponse(activeSession, "My saved details", response.content, response.payload);
      if (!schemeCardsFromPayload(response.payload).length) {
        setTab("home");
      }
      setProfileNotice("Saved on this phone.");
      setStatus("Ready. Your details were used to check schemes.");
    } catch {
      setProfileNotice("Saved on this phone. Connect internet and tap Find schemes again.");
      setStatus("Saved on this phone. Connect internet and tap Find schemes again.");
      await enqueueSync("profile.find_schemes", { session_id: sessionId, profile });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="pwaShell">
      <header className="topBar">
        <div className="languagePill">
          <LanguageSelector value={languageCode} onChange={updateLanguage} />
        </div>
        <InstallPrompt />
      </header>

      {tab === "home" ? (
        <section className="homePane" aria-label="Voice home">
          <div className="voiceHero">
            <WaveformVisualizer amplitudes={amplitudes} isActive={busy || progress > 0} />
            <AudioRecorder
              mode="continuous"
              languageCode={languageCode}
              onVoiceTurn={handleVoiceTurn}
              onFallbackText={async (text) => setTyped(text)}
              onAmplitudes={setAmplitudes}
              onStatus={(nextStatus, showFallback) => {
                setStatus(nextStatus);
                setFallbackVisible(Boolean(showFallback));
              }}
            />
            <VoiceStatus status={status} progress={progress} fallbackVisible={fallbackVisible} />
          </div>
          <form className="typeFallback" onSubmit={submitTyped}>
            <textarea aria-label="Type your problem" value={typed} onChange={(event) => setTyped(event.target.value)} placeholder="Type here if speaking does not work" rows={2} disabled={busy} />
            <button type="submit" aria-label="Send typed message" disabled={busy || !typed.trim()}>
              {busy ? <span className="spinner" aria-hidden="true" /> : <Keyboard aria-hidden="true" size={20} />}
            </button>
          </form>
          <div className="turnList" aria-live="polite">
            {messages.slice(-4).map((message, index) => (
              <p className={`turn ${message.role}`} key={`${message.role}-${index}`}>
                {message.content}
              </p>
            ))}
          </div>
          <TtsPlayer audioUrl={lastVoice?.audio_url} transcript={lastVoice?.content ?? ""} autoPlay />
        </section>
      ) : null}

      {tab === "schemes" ? (
        <section className="schemePane">
          <SchemeSection title="Matched schemes" schemes={matched} onBookmark={handleBookmark} onChecklist={toggleChecklist} />
          <SchemeSection title="Near miss" schemes={nearMiss} onBookmark={handleBookmark} onChecklist={toggleChecklist} />
        </section>
      ) : null}

      {tab === "history" ? (
        <section className="historyPane">
          {history.map((item) => (
            <button className="historyItem" key={item.id} type="button" onClick={() => setSessionId(item.id)}>
              <Clock3 aria-hidden="true" size={20} />
              <span>{new Date(item.updated_at).toLocaleDateString()}</span>
              <strong>{item.matched_scheme_count} schemes</strong>
            </button>
          ))}
        </section>
      ) : null}

      {tab === "profile" ? (
        <section className="profilePane">
          {loginPrompt ? <p className="loginPrompt">{loginPrompt}</p> : null}
          <section className="accountPanel" aria-labelledby="account-heading">
            <div>
              <h2 id="account-heading">Account</h2>
              <p>{authUser ? `Signed in as ${maskPhone(authUser.phone_e164)}` : "Guest mode. No account has been created yet."}</p>
            </div>
            {!authUser ? (
              <div className="otpGrid">
                <label className="profileField">
                  <span>Phone number</span>
                  <input type="tel" value={phoneE164} onChange={(event) => setPhoneE164(event.target.value)} placeholder="+91XXXXXXXXXX" autoComplete="tel" />
                </label>
                <button type="button" disabled={busy || phoneE164.trim().length < 10} onClick={requestOtp}>Send OTP</button>
                {otpChallengeId ? (
                  <>
                    <label className="profileField">
                      <span>OTP</span>
                      <input value={otp} onChange={(event) => setOtp(event.target.value)} inputMode="numeric" autoComplete="one-time-code" />
                    </label>
                    <button type="button" disabled={busy || otp.trim().length < 4} onClick={completeOtpLogin}>Verify OTP</button>
                  </>
                ) : null}
              </div>
            ) : null}
            {accountNotice ? <p className="profileNotice" aria-live="polite">{accountNotice}</p> : null}
          </section>
          <header className="profileHeader">
            <h1>My details</h1>
            <p>Save basic facts here. They stay on this phone and help find schemes faster.</p>
          </header>
          <div className="profileCompleteness" aria-label="Profile completeness">
            <div>
              <span>Profile completeness</span>
              <strong>{profileCompleteness}%</strong>
            </div>
            <progress value={profileCompleteness} max={100}>{profileCompleteness}%</progress>
          </div>
          {profileNotice ? <p className="profileNotice" aria-live="polite">{profileNotice}</p> : null}
          <form className="profileForm" onSubmit={async (event) => {
            event.preventDefault();
            await saveProfileDetails();
          }}>
            <label className="profileField">
              <span>Display name</span>
              <input name="display_name" value={guestProfile?.display_name ?? ""} onChange={(event) => updateProfileDraft({ display_name: event.target.value })} autoComplete="name" />
            </label>
            <SearchableSelect
              label="State"
              name="state_code"
              value={selectedStateLabel}
              placeholder="Select state"
              options={stateSelectOptions}
              onSelect={(option) => updateProfileDraft({ state_code: option.value, district: "", village: "" })}
            />
            <SearchableSelect
              label="District"
              name="district"
              value={guestProfile?.district ?? ""}
              placeholder={guestProfile?.state_code ? "Select district" : "Select state first"}
              options={districtSelectOptions}
              disabled={!guestProfile?.state_code}
              onSelect={(option) => updateProfileDraft({ district: option.value, village: "" })}
            />
            <SearchableSelect
              label="Village or place"
              name="village"
              value={guestProfile?.village ?? ""}
              placeholder="Select or type village"
              options={villageSelectOptions}
              allowCustom
              onSelect={(option) => updateProfileDraft({ village: option.value })}
            />
            <label className="profileField">
              <span>Age</span>
              <input name="age" type="number" min={0} max={120} inputMode="numeric" value={guestProfile?.age ?? ""} onChange={(event) => updateProfileDraft({ age: numberOrUndefined(event.target.value) })} />
            </label>
            <label className="profileField">
              <span>Gender</span>
              <select name="gender" value={guestProfile?.gender ?? ""} onChange={(event) => updateProfileDraft({ gender: event.target.value as GuestProfile["gender"] })}>
                <option value="">Select</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="profileField">
              <span>Occupation</span>
              <input name="occupation_type" value={guestProfile?.occupation_type ?? ""} onChange={(event) => updateProfileDraft({ occupation_type: event.target.value })} placeholder="farmer" />
            </label>
            <label className="profileField">
              <span>Annual income</span>
              <input name="annual_income" type="number" min={0} inputMode="numeric" value={guestProfile?.annual_income ?? ""} onChange={(event) => updateProfileDraft({ annual_income: numberOrUndefined(event.target.value) })} />
            </label>
            <label className="profileField">
              <span>Ration card type</span>
              <select name="ration_card_type" value={guestProfile?.ration_card_type ?? ""} onChange={(event) => updateProfileDraft({ ration_card_type: event.target.value })}>
                <option value="">Select</option>
                <option value="bpl">BPL</option>
                <option value="aay">Antyodaya</option>
                <option value="apl">APL</option>
                <option value="none">No ration card</option>
              </select>
            </label>
            <label className="profileField">
              <span>Land acres</span>
              <input name="land_holding_acres" type="number" min={0} step="0.01" inputMode="decimal" value={guestProfile?.land_holding_acres ?? ""} onChange={(event) => updateProfileDraft({ land_holding_acres: numberOrUndefined(event.target.value) })} />
            </label>
            <label className="toggleRow">
              <input name="has_land_record" type="checkbox" checked={Boolean(guestProfile?.has_land_record)} onChange={(event) => updateProfileDraft({ has_land_record: event.target.checked })} />
              Has land record
            </label>
            <label className="toggleRow">
              <input name="has_bank_account" type="checkbox" checked={Boolean(guestProfile?.has_bank_account)} onChange={(event) => updateProfileDraft({ has_bank_account: event.target.checked })} />
              Has bank account
            </label>
            <div className="profileActions">
              <button className={profileSavedAt ? "saved" : ""} type="submit" disabled={busy}>
                <Save aria-hidden="true" size={18} />
                {profileSavedAt ? "Saved" : "Save details"}
              </button>
              <button className="primary" type="button" disabled={busy} onClick={findSchemesWithProfile}>
                <Search aria-hidden="true" size={18} />
                Find schemes
              </button>
            </div>
            <div className={`saveInlineStatus ${profileSavedAt ? "visible" : ""}`} role="status" aria-live="polite">
              {profileSavedAt ? `Saved on this phone at ${profileSavedAt}.` : "Changes are not saved yet."}
            </div>
          </form>
          <section className="settingsSection" aria-labelledby="settings-heading">
            <h2 id="settings-heading">Settings</h2>
            <label className="toggleRow">
              <input type="checkbox" checked={Boolean(guestProfile?.high_contrast_enabled)} onChange={(event) => updateAccessibility({ high_contrast_enabled: event.target.checked })} />
              High contrast
            </label>
            <label className="profileField">
              <span>Text size</span>
              <select value={guestProfile?.font_size ?? "default"} onChange={(event) => updateAccessibility({ font_size: event.target.value as GuestProfile["font_size"] })}>
                <option value="default">Default</option>
                <option value="large">Large</option>
                <option value="extra_large">Extra large</option>
              </select>
            </label>
          </section>
        </section>
      ) : null}

      <nav className="bottomNav" aria-label="Main">
        {[
          ["home", Home, "Home"],
          ["schemes", CheckCircle2, "My Schemes"],
          ["history", Clock3, "History"],
          ["profile", User, "Profile"]
        ].map(([key, Icon, label]) => (
          <button className={tab === key ? "active" : ""} key={String(key)} type="button" onClick={() => setTab(key as Tab)}>
            <Icon aria-hidden="true" size={20} />
            <span>{String(label)}</span>
          </button>
        ))}
      </nav>
    </main>
  );
}

function SchemeSection(props: {
  title: string;
  schemes: SchemeCardView[];
  onBookmark: (scheme: SchemeCardView) => Promise<void>;
  onChecklist: (scheme: SchemeCardView, documentName: string) => Promise<void>;
}) {
  const [savingBookmark, setSavingBookmark] = useState<string>("");
  const [savingChecklist, setSavingChecklist] = useState<string>("");

  if (!props.schemes.length) return null;
  return (
    <section>
      <h2>{props.title}</h2>
      {props.schemes.map((scheme) => {
        const ready = scheme.documents.every((doc) => !doc.is_mandatory || doc.status === "gathered" || doc.status === "verified");
        return (
          <article className={`schemeCard ${scheme.eligibility_status}`} key={scheme.scheme_id}>
            <div className="schemeTitleRow">
              <h3>{scheme.name}</h3>
              <button className="iconButton" type="button" disabled={savingBookmark === scheme.scheme_id} onClick={async () => {
                setSavingBookmark(scheme.scheme_id);
                await props.onBookmark(scheme);
                setSavingBookmark("");
              }} aria-label={`Save ${scheme.name}`}>
                {savingBookmark === scheme.scheme_id ? <span className="spinner" /> : <Bookmark aria-hidden="true" size={19} fill={scheme.saved ? "currentColor" : "none"} />}
              </button>
            </div>
            <p>{scheme.plain_language_benefit}</p>
            <span className="amountBadge">{scheme.benefit_amount}</span>
            <span className="statusBadge">{scheme.eligibility_status.replace("_", " ")}</span>
            {scheme.failed_criterion ? <p className="nearMissText">{scheme.failed_criterion}. {scheme.how_to_qualify}</p> : null}
            <div className="checklist">
              {scheme.documents.map((doc) => {
                const isToggling = savingChecklist === `${scheme.scheme_id}:${doc.document_name}`;
                return (
                  <label key={doc.document_name} className={`checkItem ${isToggling ? "is-loading" : ""}`}>
                    <input type="checkbox" disabled={isToggling} checked={doc.status === "gathered" || doc.status === "verified"} onChange={async () => {
                      setSavingChecklist(`${scheme.scheme_id}:${doc.document_name}`);
                      await props.onChecklist(scheme, doc.document_name);
                      setSavingChecklist("");
                    }} />
                    <span>{doc.document_name} {isToggling && <span className="spinner" style={{marginLeft: 4, width: '0.8em', height: '0.8em'}} />}</span>
                    {doc.accepted_substitutes.length ? <small>Substitute available</small> : null}
                  </label>
                );
              })}
            </div>
            <details>
              <summary>Application steps</summary>
              <ol>
                {scheme.application_steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            </details>
            <div className="cardActions">
              <button type="button" onClick={() => updateApplicationStatus("00000000-0000-0000-0000-000000000000", scheme.scheme_id, "documents_gathering")}>
                {ready ? "Ready to apply" : "Keep gathering"}
              </button>
              {scheme.application_url ? <a href={scheme.application_url}>Apply</a> : null}
              <button type="button" aria-label={`Hear ${scheme.name}`}>
                <Volume2 aria-hidden="true" size={18} />
              </button>
            </div>
          </article>
        );
      })}
    </section>
  );
}

type SelectOption = { value: string; label: string; meta?: string };

function SearchableSelect(props: {
  label: string;
  name: string;
  value: string;
  placeholder: string;
  options: SelectOption[];
  onSelect: (option: SelectOption) => void;
  disabled?: boolean;
  allowCustom?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(props.value);
  const listId = `${props.name}-dropdown`;

  useEffect(() => {
    setQuery(props.value);
  }, [props.value]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return props.options;
    return props.options.filter((option) => `${option.label} ${option.meta ?? ""}`.toLowerCase().includes(normalized));
  }, [props.options, query]);

  function choose(option: SelectOption) {
    props.onSelect(option);
    setQuery(option.label);
    setOpen(false);
  }

  function updateQuery(value: string) {
    setQuery(value);
    setOpen(true);
    const exact = props.options.find((option) => option.label.toLowerCase() === value.trim().toLowerCase() || option.value.toLowerCase() === value.trim().toLowerCase());
    if (exact) {
      props.onSelect(exact);
    } else if (props.allowCustom) {
      props.onSelect({ value, label: value });
    }
  }

  return (
    <label className="profileField searchableSelect">
      <span>{props.label}</span>
      <div className="selectShell">
        <input
          aria-controls={listId}
          aria-expanded={open}
          aria-haspopup="listbox"
          autoComplete="off"
          disabled={props.disabled}
          name={props.name}
          onBlur={() => window.setTimeout(() => setOpen(false), 120)}
          onChange={(event) => updateQuery(event.target.value)}
          onFocus={() => setOpen(true)}
          placeholder={props.placeholder}
          role="combobox"
          value={query}
        />
        <button type="button" disabled={props.disabled} aria-label={`Open ${props.label} list`} onClick={() => setOpen((current) => !current)}>
          <ChevronDown aria-hidden="true" size={18} />
        </button>
        {open && !props.disabled ? (
          <div className="selectMenu" id={listId} role="listbox">
            {filtered.map((option) => (
              <button key={`${option.value}-${option.label}`} type="button" role="option" aria-selected={props.value === option.label || props.value === option.value} onMouseDown={(event) => {
                event.preventDefault();
                choose(option);
              }}>
                <span>{option.label}</span>
                {option.meta ? <small>{option.meta}</small> : null}
              </button>
            ))}
            {props.allowCustom && query.trim() ? (
              <button type="button" role="option" onMouseDown={(event) => {
                event.preventDefault();
                choose({ value: query.trim(), label: query.trim() });
              }}>
                <span>Use "{query.trim()}"</span>
              </button>
            ) : null}
            {!filtered.length && !props.allowCustom ? <p>No matches</p> : null}
          </div>
        ) : null}
      </div>
    </label>
  );
}

function schemeCardsFromPayload(payload: unknown): SchemeCardView[] {
  const data = payload as { matched_schemes?: Array<Record<string, unknown>>; near_miss_schemes?: Array<Record<string, unknown>> } | null;
  const convert = (item: Record<string, unknown>, status: SchemeCardView["eligibility_status"]) => {
    const scheme = (item.scheme ?? {}) as Record<string, unknown>;
    const required = (scheme.required_documents ?? []) as Array<{ name: string; is_mandatory: boolean; accepted_substitutes?: Array<Record<string, unknown>> }>;
    return {
      scheme_id: String(scheme.id ?? ""),
      name: String(scheme.name ?? "Scheme"),
      plain_language_benefit: String(scheme.description ?? "You may get support from this scheme."),
      benefit_amount: String(scheme.benefit_amount ?? "Benefit varies"),
      eligibility_status: status,
      failed_criterion: item.failed_criterion ? String(item.failed_criterion) : undefined,
      how_to_qualify: item.how_to_qualify ? String(item.how_to_qualify) : undefined,
      documents: required.map((doc) => ({
        document_name: doc.name,
        is_mandatory: doc.is_mandatory,
        status: "not_gathered" as const,
        accepted_substitutes: doc.accepted_substitutes ?? []
      })),
      application_steps: ["Gather documents", "Submit form online or at CSC", "Save receipt"],
      application_url: typeof scheme.application_url === "string" ? scheme.application_url : undefined,
      saved: false
    };
  };
  return [...(data?.matched_schemes ?? []).map((item) => convert(item, "eligible")), ...(data?.near_miss_schemes ?? []).map((item) => convert(item, "near_miss"))].filter((item) => item.scheme_id);
}

function applyAccessibility(profile: GuestProfile) {
  document.documentElement.dataset.contrast = profile.high_contrast_enabled ? "high" : "normal";
  document.documentElement.dataset.fontSize = profile.font_size;
}

function numberOrUndefined(value: string) {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function computeLocalProfileCompleteness(profile: GuestProfile | null) {
  if (!profile) return 0;
  const fields: Array<keyof GuestProfile> = [
    "display_name",
    "state_code",
    "district",
    "village",
    "age",
    "gender",
    "occupation_type",
    "annual_income",
    "ration_card_type",
    "land_holding_acres",
    "has_land_record",
    "has_bank_account"
  ];
  const filled = fields.filter((field) => {
    const value = profile[field];
    return value !== undefined && value !== null && value !== "";
  }).length;
  return Math.round((filled / fields.length) * 100);
}

function buildProfileFactsMessage(profile: GuestProfile) {
  const facts: string[] = [];
  const add = (key: string, value: string | number | boolean | undefined) => {
    if (value === undefined || value === "") return;
    facts.push(`${key}=${String(value).trim()}`);
  };
  add("display_name", profile.display_name);
  add("state_code", profile.state_code?.trim().toUpperCase());
  add("district", profile.district);
  add("age", profile.age);
  add("gender", profile.gender);
  add("occupation_type", profile.occupation_type);
  add("annual_income", profile.annual_income);
  add("ration_card_type", profile.ration_card_type);
  add("land_holding_acres", profile.land_holding_acres);
  add("has_land_record", profile.has_land_record);
  add("has_bank_account", profile.has_bank_account);
  return `profile_facts: ${facts.join("; ")}`;
}

function maskPhone(phone: string) {
  return phone.replace(/(\+\d{2})\d+(\d{4})$/, "$1******$2");
}
