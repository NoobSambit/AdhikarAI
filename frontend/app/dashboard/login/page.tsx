"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { dashboardLogin } from "@/lib/api";

function errorMessage(error: unknown): string {
  const text = error instanceof Error ? error.message : String(error);
  if (text.includes("DASHBOARD_AUTH_NOT_CONFIGURED")) {
    return "Dashboard login is not configured for this environment.";
  }
  if (text.includes("DASHBOARD_DEV_LOGIN_DISABLED")) {
    return "Dev login is disabled here.";
  }
  if (text.includes("DASHBOARD_INVALID_CREDENTIALS")) {
    return "Email or code is not correct.";
  }
  return "Sign in failed. Try again.";
}

function safeNext(value: string | null): string {
  if (value?.startsWith("/dashboard") || value?.startsWith("/admin")) {
    return value;
  }
  return "/dashboard";
}

export default function DashboardLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [loginCode, setLoginCode] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setStatus("");
    setSubmitting(true);
    try {
      await dashboardLogin(email, loginCode);
      setStatus("Signed in.");
      const params = new URLSearchParams(window.location.search);
      router.replace(safeNext(params.get("next")));
      router.refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="dashboardLoginPage">
      <section className="dashboardLoginPanel" aria-labelledby="dashboard-login-heading">
        <h1 id="dashboard-login-heading">Dashboard sign in</h1>
        {error ? <p className="dashboardError" role="alert">{error}</p> : null}
        {status ? <p className="dashboardStatus" role="status">{status}</p> : null}
        <form className="denseForm" onSubmit={submit}>
          <label>
            Email
            <input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Access code
            <input type="password" autoComplete="current-password" value={loginCode} onChange={(event) => setLoginCode(event.target.value)} required />
          </label>
          <button className="primaryButton" type="submit" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
