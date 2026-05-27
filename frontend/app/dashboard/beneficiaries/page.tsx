"use client";

import { FormEvent, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { DashboardBeneficiary, listDashboardBeneficiaries } from "@/lib/api";

export default function BeneficiariesPage() {
  const [items, setItems] = useState<DashboardBeneficiary[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);

  async function load(nextQ = q) {
    setLoading(true);
    try {
      const response = await listDashboardBeneficiaries(nextQ ? { q: nextQ } : {});
      setItems(response.items);
    } finally {
      setLoading(false);
    }
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
          <input value={q} onChange={(event) => setQ(event.target.value)} placeholder="Name, phone, village" disabled={loading} />
        </label>
        <button className="secondaryButton" type="submit" disabled={loading}>
          {loading ? <span className="spinner" /> : "Search"}
        </button>
      </form>
        <div className="tableContainer">
          <table className="denseTable">
            <thead>
              <tr><th>Name</th><th>Phone</th><th>Village</th><th>State</th><th>Status</th></tr>
            </thead>
            <tbody>
              {loading ? (
                [1, 2, 3, 4, 5].map((i) => (
                  <tr key={i} className="skeleton">
                    <td><div style={{height: 20, width: 120}}></div></td>
                    <td><div style={{height: 20, width: 100}}></div></td>
                    <td><div style={{height: 20, width: 80}}></div></td>
                    <td><div style={{height: 20, width: 40}}></div></td>
                    <td><div style={{height: 20, width: 90}}></div></td>
                  </tr>
                ))
              ) : items.map((item) => (
                <tr key={item.id}>
                  <td><a href={`/dashboard/beneficiaries/${item.id}`}>{item.name}</a></td>
                  <td>{item.phone_e164 ?? "-"}</td>
                  <td>{item.village ?? "-"}</td>
                  <td>{item.state_code}</td>
                  <td>{item.application_statuses[0]?.status ?? "not_started"}</td>
                </tr>
              ))}
              {!loading && !items.length ? <tr><td colSpan={5}>No beneficiaries found.</td></tr> : null}
            </tbody>
          </table>
        </div>
      </section>
    );
  }
