"use client";

import { FormEvent, useState } from "react";
import { createDashboardBeneficiary } from "@/lib/api";

export default function NewBeneficiaryPage() {
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const state = String(form.get("state_code") ?? "");
    if (!state) {
      setMessage("State is required to run eligibility.");
      return;
    }
    await createDashboardBeneficiary({
      name: form.get("name"),
      phone_e164: form.get("phone_e164") || undefined,
      state_code: state,
      language_code: form.get("language_code") || "hi",
      village: form.get("village") || undefined,
      district: form.get("district") || undefined,
      profile: {
        age: Number(form.get("age") || 0) || undefined,
        gender: form.get("gender") || undefined,
        annual_income: Number(form.get("annual_income") || 0) || undefined
      }
    });
    setMessage("Beneficiary saved.");
  }

  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Add Beneficiary</h1><p>Create profile facts for assisted eligibility.</p></div></header>
      <form className="denseForm" onSubmit={submit}>
        <label>Name<input name="name" required maxLength={200} /></label>
        <label>Phone<input name="phone_e164" /></label>
        <label>State<input name="state_code" required placeholder="IN-BR" /></label>
        <label>Language<input name="language_code" defaultValue="hi" /></label>
        <label>District<input name="district" /></label>
        <label>Village<input name="village" /></label>
        <label>Age<input name="age" type="number" min="0" max="120" /></label>
        <label>Gender<input name="gender" placeholder="female" /></label>
        <label>Annual income<input name="annual_income" type="number" min="0" /></label>
        <button className="primaryButton" type="submit">Save</button>
      </form>
      {message ? <p className="dashboardStatus">{message}</p> : null}
    </section>
  );
}
