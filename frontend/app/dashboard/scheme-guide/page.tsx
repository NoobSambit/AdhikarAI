"use client";

import { useEffect, useState } from "react";
import { getSchemeGuide } from "@/lib/api";

export default function SchemeGuidePage() {
  const [items, setItems] = useState<Array<Record<string, string>>>([]);
  useEffect(() => {
    getSchemeGuide().then((response) => setItems(response.items)).catch(() => setItems([]));
  }, []);
  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Scheme Guide</h1><p>Active schemes with operator summaries.</p></div></header>
      <table className="denseTable"><thead><tr><th>Scheme</th><th>State</th><th>Benefit</th><th>Apply</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.name}</td><td>{item.state_code ?? "All"}</td><td>{item.benefit_amount}</td><td>{item.application_url ? <a href={item.application_url}>Open</a> : "-"}</td></tr>)}</tbody></table>
    </section>
  );
}
