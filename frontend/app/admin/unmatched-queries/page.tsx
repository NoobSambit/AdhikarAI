"use client";

import { useEffect, useState } from "react";
import { getUnmatchedQueries } from "@/lib/api";

export default function UnmatchedQueriesPage() {
  const [items, setItems] = useState<Array<{ normalized_query_text: string; frequency: number; languages: string[]; latest_at: string }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getUnmatchedQueries()
      .then((response) => setItems(response.items))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Zero-match Review</h1><p>Grouped unmatched queries sorted by frequency.</p></div></header>
      <div className="tableContainer">
        <table className="denseTable">
          <thead><tr><th>Query</th><th>Frequency</th><th>Languages</th><th>Latest</th></tr></thead>
          <tbody>
            {loading ? (
              [1, 2, 3].map((i) => (
                <tr key={i} className="skeleton">
                  <td><div style={{height: 20, width: 200}}></div></td>
                  <td><div style={{height: 20, width: 40}}></div></td>
                  <td><div style={{height: 20, width: 80}}></div></td>
                  <td><div style={{height: 20, width: 120}}></div></td>
                </tr>
              ))
            ) : items.map((item) => (
              <tr key={item.normalized_query_text}>
                <td>{item.normalized_query_text}</td>
                <td>{item.frequency}</td>
                <td>{item.languages.join(", ")}</td>
                <td>{item.latest_at}</td>
              </tr>
            ))}
            {!loading && !items.length ? <tr><td colSpan={4}>No unmatched queries found.</td></tr> : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
