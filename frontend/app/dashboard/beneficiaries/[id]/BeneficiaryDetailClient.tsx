"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { CalendarPlus, FileCheck2, ListChecks, NotebookPen, PlayCircle } from "lucide-react";
import {
  addBeneficiaryFollowup,
  addBeneficiaryNote,
  DashboardBeneficiaryDetail,
  DashboardMe,
  getDashboardBeneficiary,
  getDashboardMe,
  runBeneficiaryEligibility,
  updateDashboardApplicationStatus
} from "@/lib/api";

const statusOptions = ["not_started", "documents_gathering", "submitted", "pending", "approved", "rejected"];

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function errorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  try {
    const parsed = JSON.parse(message) as { code?: string; message?: string; error?: { code?: string; message?: string } };
    const code = parsed.code ?? parsed.error?.code;
    if (code === "BENEFICIARY_NOT_ASSIGNED" || code === "ORG_SCOPE_DENIED" || code === "PERMISSION_DENIED") {
      return "You do not have access to this beneficiary.";
    }
    if (code === "BENEFICIARY_NOT_FOUND") return "Beneficiary was not found.";
    return parsed.message ?? parsed.error?.message ?? message;
  } catch {
    return message;
  }
}

export function BeneficiaryDetailClient({ beneficiaryId }: { beneficiaryId: string }) {
  const [me, setMe] = useState<DashboardMe | null>(null);
  const [beneficiary, setBeneficiary] = useState<DashboardBeneficiaryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [note, setNote] = useState("");
  const [assignMatchedSchemes, setAssignMatchedSchemes] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [nextMe, nextBeneficiary] = await Promise.all([getDashboardMe(), getDashboardBeneficiary(beneficiaryId)]);
      setMe(nextMe);
      setBeneficiary(nextBeneficiary);
    } catch (nextError) {
      setError(errorMessage(nextError));
      setBeneficiary(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [beneficiaryId]);

  const canWrite = useMemo(() => {
    if (!me || !beneficiary) return false;
    const hasPermission = me.permissions.includes("*") || me.permissions.includes("beneficiary:write");
    if (!hasPermission) return false;
    return me.role !== "operator" || beneficiary.assigned_operator_id === me.member_id;
  }, [me, beneficiary]);

  async function submitNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!beneficiary || !note.trim()) return;
    setSaving("note");
    setError("");
    setMessage("");
    try {
      await addBeneficiaryNote(beneficiary.id, note.trim());
      setNote("");
      setMessage("Note added.");
      await load();
    } catch (nextError) {
      setError(errorMessage(nextError));
    } finally {
      setSaving("");
    }
  }

  async function submitFollowup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!beneficiary) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const dueDate = String(form.get("due_date") ?? "");
    const reason = String(form.get("reason") ?? "").trim();
    setSaving("followup");
    setError("");
    setMessage("");
    try {
      await addBeneficiaryFollowup(beneficiary.id, { due_date: dueDate, reason: reason || undefined });
      formElement.reset();
      setMessage("Follow-up added.");
      await load();
    } catch (nextError) {
      setError(errorMessage(nextError));
    } finally {
      setSaving("");
    }
  }

  async function submitEligibility(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!beneficiary) return;
    setSaving("eligibility");
    setError("");
    setMessage("");
    try {
      const result = await runBeneficiaryEligibility(beneficiary.id, assignMatchedSchemes);
      setMessage(`Eligibility run complete. Assigned ${result.assigned_count} scheme(s).`);
      await load();
    } catch (nextError) {
      setError(errorMessage(nextError));
    } finally {
      setSaving("");
    }
  }

  async function changeStatus(statusId: string, status: string) {
    setSaving(statusId);
    setError("");
    setMessage("");
    try {
      await updateDashboardApplicationStatus(statusId, status, "Updated from beneficiary detail.");
      setMessage("Application status updated.");
      await load();
    } catch (nextError) {
      setError(errorMessage(nextError));
    } finally {
      setSaving("");
    }
  }

  if (loading) {
    return <section className="dashboardPage"><p className="dashboardStatus">Loading beneficiary detail...</p></section>;
  }

  if (error && !beneficiary) {
    return (
      <section className="dashboardPage">
        <header className="dashboardHeader"><div><h1>Beneficiary Detail</h1><p>Access is checked by the backend.</p></div></header>
        <p className="dashboardError" role="alert">{error}</p>
      </section>
    );
  }

  if (!beneficiary) return null;

  return (
    <section className="dashboardPage">
      <header className="dashboardHeader">
        <div>
          <h1>{beneficiary.name}</h1>
          <p>{beneficiary.village ?? "Village not set"} · {beneficiary.district ?? "District not set"} · {beneficiary.state_code}</p>
        </div>
        <a className="secondaryButton" href="/dashboard/beneficiaries">Back to list</a>
      </header>

      {error ? <p className="dashboardError" role="alert">{error}</p> : null}
      {message ? <p className="dashboardStatus" role="status">{message}</p> : null}

      <section className="detailGrid" aria-label="Beneficiary summary">
        <div className="dashboardPanel">
          <h2>Identity</h2>
          <dl className="keyValueGrid">
            <div><dt>Phone</dt><dd>{beneficiary.phone_e164 ?? "-"}</dd></div>
            <div><dt>Language</dt><dd>{beneficiary.language_code}</dd></div>
            <div><dt>Assigned operator</dt><dd>{beneficiary.assigned_operator_id ?? "-"}</dd></div>
            <div><dt>Profile id</dt><dd>{beneficiary.profile_id}</dd></div>
          </dl>
        </div>

        <div className="dashboardPanel">
          <h2>Profile</h2>
          <dl className="keyValueGrid">
            {Object.entries(beneficiary.profile).map(([key, value]) => (
              <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{formatValue(value)}</dd></div>
            ))}
            {!Object.keys(beneficiary.profile).length ? <div><dt>Profile fields</dt><dd>-</dd></div> : null}
          </dl>
        </div>
      </section>

      <section className="dashboardPanel" aria-labelledby="statuses-heading">
        <div className="panelTitle">
          <ListChecks size={18} aria-hidden="true" />
          <h2 id="statuses-heading">Application statuses</h2>
        </div>
        <div className="tableContainer">
          <table className="denseTable">
            <thead><tr><th>Scheme</th><th>Status</th><th>Update</th></tr></thead>
            <tbody>
              {beneficiary.application_statuses.map((status) => (
                <tr key={status.id ?? status.scheme_id}>
                  <td>{status.scheme_id}</td>
                  <td>{status.status}</td>
                  <td>
                    {canWrite && status.id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <select
                          className="denseSelect"
                          value={status.status}
                          disabled={saving === status.id}
                          onChange={(event) => changeStatus(status.id as string, event.target.value)}
                          aria-label={`Update ${status.scheme_id} application status`}
                        >
                          {statusOptions.map((option) => <option key={option} value={option}>{option.replaceAll("_", " ")}</option>)}
                        </select>
                        {saving === status.id && <span className="spinner" />}
                      </div>
                    ) : "-"}
                  </td>
                </tr>
              ))}
              {!beneficiary.application_statuses.length ? <tr><td colSpan={3}>No application status records.</td></tr> : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="detailGrid">
        <div className="dashboardPanel">
          <div className="panelTitle"><NotebookPen size={18} aria-hidden="true" /><h2>Notes</h2></div>
          {canWrite ? (
            <form className="stackedForm" onSubmit={submitNote}>
              <label htmlFor="beneficiary-note">Add note</label>
              <textarea id="beneficiary-note" value={note} onChange={(event) => setNote(event.target.value)} maxLength={5000} required />
              <button className="primaryButton" type="submit" disabled={saving === "note"}>
                {saving === "note" ? <><span className="spinner" /> Saving...</> : "Add note"}
              </button>
            </form>
          ) : null}
          <div className="activityList">
            {beneficiary.notes.map((item) => <article key={item.id}><strong>{item.created_at?.slice(0, 10) ?? "Note"}</strong><p>{item.note}</p></article>)}
            {!beneficiary.notes.length ? <p>No notes yet.</p> : null}
          </div>
        </div>

        <div className="dashboardPanel">
          <div className="panelTitle"><CalendarPlus size={18} aria-hidden="true" /><h2>Follow-ups</h2></div>
          {canWrite ? (
            <form className="stackedForm" onSubmit={submitFollowup}>
              <label htmlFor="followup-due-date">Due date</label>
              <input id="followup-due-date" name="due_date" type="date" required />
              <label htmlFor="followup-reason">Reason</label>
              <input id="followup-reason" name="reason" maxLength={500} />
              <button className="primaryButton" type="submit" disabled={saving === "followup"}>
                {saving === "followup" ? <><span className="spinner" /> Saving...</> : "Add follow-up"}
              </button>
            </form>
          ) : null}
          <div className="activityList">
            {beneficiary.followups.map((item) => <article key={item.id}><strong>{item.due_date} · {item.status}</strong><p>{item.reason ?? "-"}</p></article>)}
            {!beneficiary.followups.length ? <p>No follow-ups.</p> : null}
          </div>
        </div>
      </section>

      <section className="detailGrid">
        <div className="dashboardPanel">
          <div className="panelTitle"><PlayCircle size={18} aria-hidden="true" /><h2>Eligibility</h2></div>
          {canWrite ? (
            <form className="stackedForm" onSubmit={submitEligibility}>
              <label className="inlineCheck">
                <input type="checkbox" checked={assignMatchedSchemes} onChange={(event) => setAssignMatchedSchemes(event.target.checked)} />
                <span>Assign matched schemes</span>
              </label>
              <button className="primaryButton" type="submit" disabled={saving === "eligibility"}>
                {saving === "eligibility" ? <><span className="spinner" /> Running...</> : "Run eligibility"}
              </button>
            </form>
          ) : <p>View-only access.</p>}
          <h3>Assigned schemes</h3>
          <div className="tableContainer">
            <table className="denseTable">
              <thead><tr><th>Scheme</th><th>Source</th></tr></thead>
              <tbody>
                {beneficiary.assigned_schemes.map((item) => <tr key={item.id}><td>{item.scheme_id}</td><td>{item.assignment_source}</td></tr>)}
                {!beneficiary.assigned_schemes.length ? <tr><td colSpan={2}>No assigned schemes.</td></tr> : null}
              </tbody>
            </table>
          </div>
        </div>

        <div className="dashboardPanel">
          <div className="panelTitle"><FileCheck2 size={18} aria-hidden="true" /><h2>Document checklist</h2></div>
          <div className="tableContainer">
            <table className="denseTable">
              <thead><tr><th>Document</th><th>Status</th><th>Metadata</th></tr></thead>
              <tbody>
                {beneficiary.document_checklist.map((item) => (
                  <tr key={item.id}>
                    <td>{item.document_name}</td>
                    <td>{item.status}</td>
                    <td>{item.metadata ? formatValue(item.metadata) : "-"}</td>
                  </tr>
                ))}
                {!beneficiary.document_checklist.length ? <tr><td colSpan={3}>No document review metadata.</td></tr> : null}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </section>
  );
}
