"use client";

import { useEffect, useState } from "react";
import { getQualityFlags, markQualityFlagReviewed, QualityFlag } from "@/lib/api";

export default function QualityPage() {
  const [items, setItems] = useState<QualityFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState("");

  async function load() {
    setLoading(true);
    try {
      setItems((await getQualityFlags()).items);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function review(id: string) {
    setReviewing(id);
    try {
      await markQualityFlagReviewed(id, "Reviewed from dashboard.");
      await load();
    } finally {
      setReviewing("");
    }
  }

  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Quality Flags</h1><p>Review sessions flagged by Phase 5 quality rules.</p></div></header>
      <div className="tableContainer">
        <table className="denseTable">
          <thead><tr><th>Type</th><th>Severity</th><th>Reviewed</th><th>Action</th></tr></thead>
          <tbody>
            {loading ? (
              [1, 2, 3].map((i) => (
                <tr key={i} className="skeleton">
                  <td><div style={{height: 20, width: 120}}></div></td>
                  <td><div style={{height: 20, width: 80}}></div></td>
                  <td><div style={{height: 20, width: 40}}></div></td>
                  <td><div style={{height: 32, width: 80}}></div></td>
                </tr>
              ))
            ) : items.map((item) => (
              <tr key={item.id}>
                <td>{item.flag_type}</td>
                <td>{item.severity}</td>
                <td>{item.reviewed_at ? "yes" : "no"}</td>
                <td>
                  <button className="secondaryButton" onClick={() => review(item.id)} disabled={Boolean(item.reviewed_at) || reviewing === item.id}>
                    {reviewing === item.id ? <><span className="spinner" />...</> : "Review"}
                  </button>
                </td>
              </tr>
            ))}
            {!loading && !items.length ? <tr><td colSpan={4}>No quality flags to review.</td></tr> : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
