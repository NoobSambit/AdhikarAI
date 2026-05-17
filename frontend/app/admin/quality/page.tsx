"use client";

import { useEffect, useState } from "react";
import { getQualityFlags, markQualityFlagReviewed, QualityFlag } from "@/lib/api";

export default function QualityPage() {
  const [items, setItems] = useState<QualityFlag[]>([]);

  async function load() {
    setItems((await getQualityFlags()).items);
  }

  useEffect(() => {
    load();
  }, []);

  async function review(id: string) {
    await markQualityFlagReviewed(id, "Reviewed from dashboard.");
    await load();
  }

  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Quality Flags</h1><p>Review sessions flagged by Phase 5 quality rules.</p></div></header>
      <table className="denseTable">
        <thead><tr><th>Type</th><th>Severity</th><th>Reviewed</th><th>Action</th></tr></thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.flag_type}</td>
              <td>{item.severity}</td>
              <td>{item.reviewed_at ? "yes" : "no"}</td>
              <td><button className="secondaryButton" onClick={() => review(item.id)} disabled={Boolean(item.reviewed_at)}>Review</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
