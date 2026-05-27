"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarClock, Search, UserPlus } from "lucide-react";
import { DashboardBeneficiary, DashboardMe, getDashboardMe, listDashboardBeneficiaries } from "@/lib/api";

export default function DashboardHome() {
  const [me, setMe] = useState<DashboardMe | null>(null);
  const [items, setItems] = useState<DashboardBeneficiary[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const nextMe = await getDashboardMe();
        setMe(nextMe);
        const response = await listDashboardBeneficiaries({ followup_due: "today" });
        setItems(response.items);
      } catch {
        setError("Dashboard session required.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = useMemo(() => items.filter((item) => item.name.toLowerCase().includes(query.toLowerCase())), [items, query]);
  const role = me?.role ?? "operator";

  return (
    <section className="dashboardPage">
      <header className="dashboardHeader">
        <div>
          <h1>Operator Dashboard</h1>
          <p>{role === "operator" ? "Your assigned beneficiaries only" : "Organisation-level beneficiary support"}</p>
        </div>
        <a className="primaryButton" href="/dashboard/beneficiaries/new">
          <UserPlus size={18} aria-hidden="true" />
          Add beneficiary
        </a>
      </header>

      {error ? <p className="dashboardError">{error}</p> : null}

      <div className="dashboardToolbar">
        <label className="searchBox">
          <Search size={18} aria-hidden="true" />
          <span className="srOnly">Search follow-ups</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search name" />
        </label>
      </div>

      <section className="dashboardPanel" aria-labelledby="followups-heading">
        <div className="panelTitle">
          <CalendarClock size={18} aria-hidden="true" />
          <h2 id="followups-heading">Follow-ups due</h2>
        </div>
        <div className="tableContainer">
          <table className="denseTable">
            <thead>
              <tr>
                <th>Name</th>
                <th>Village</th>
                <th>State</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [1, 2, 3].map((i) => (
                  <tr key={i} className="skeleton">
                    <td><div style={{height: 20, width: 120}}></div></td>
                    <td><div style={{height: 20, width: 80}}></div></td>
                    <td><div style={{height: 20, width: 40}}></div></td>
                    <td><div style={{height: 20, width: 150}}></div></td>
                    <td><div style={{height: 20, width: 90}}></div></td>
                  </tr>
                ))
              ) : filtered.map((item) => (
                <tr key={item.id}>
                  <td><a href={`/dashboard/beneficiaries/${item.id}`}>{item.name}</a></td>
                  <td>{item.village ?? "-"}</td>
                  <td>{item.state_code}</td>
                  <td>{item.follow_up?.reason ?? "-"}</td>
                  <td>{item.application_statuses[0]?.status ?? "not_started"}</td>
                </tr>
              ))}
              {!loading && !filtered.length ? (
                <tr><td colSpan={5}>No follow-ups due today.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}
