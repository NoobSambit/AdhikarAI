"use client";

import { FormEvent, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { DashboardBeneficiary, listDashboardBeneficiaries } from "@/lib/api";

export default function BeneficiariesPage() {
  const [items, setItems] = useState<DashboardBeneficiary[]>([]);
  const [q, setQ] = useState("");

  async function load(nextQ = q) {
    const response = await listDashboardBeneficiaries(nextQ ? { q: nextQ } : {});
    setItems(response.items);
  }

  useEffect(() => {
    load("");
  }, []);

  function submit(event: FormEvent) {
    event.preventDefault();
    load(q);
  }

  return (
    <section className="dashboardPage">
      <header className="dashboardHeader">
        <div>
          <h1>Beneficiaries</h1>
          <p>Search by name, phone, or village.</p>
        </div>
      </header>
      <form className="dashboardToolbar" onSubmit={submit}>
        <label className="searchBox">
          <Search size={18} aria-hidden="true" />
          <span className="srOnly">Search beneficiaries</span>
          <input value={q} onChange={(event) => setQ(event.target.value)} placeholder="Name, phone, village" />
        </label>
        <button className="secondaryButton" type="submit">Search</button>
      </form>
      <table className="denseTable">
        <thead>
          <tr><th>Name</th><th>Phone</th><th>Village</th><th>State</th><th>Status</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td><a href={`/dashboard/beneficiaries/${item.id}`}>{item.name}</a></td>
              <td>{item.phone_e164 ?? "-"}</td>
              <td>{item.village ?? "-"}</td>
              <td>{item.state_code}</td>
              <td>{item.application_statuses[0]?.status ?? "not_started"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
