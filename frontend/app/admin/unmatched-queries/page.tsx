"use client";

import { useEffect, useState } from "react";
import { getUnmatchedQueries } from "@/lib/api";

export default function UnmatchedQueriesPage() {
  const [items, setItems] = useState<Array<{ normalized_query_text: string; frequency: number; languages: string[]; latest_at: string }>>([]);
  useEffect(() => {
    getUnmatchedQueries().then((response) => setItems(response.items)).catch(() => setItems([]));
  }, []);
  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Zero-match Review</h1><p>Grouped unmatched queries sorted by frequency.</p></div></header>
      <table className="denseTable"><thead><tr><th>Query</th><th>Frequency</th><th>Languages</th><th>Latest</th></tr></thead><tbody>{items.map((item) => <tr key={item.normalized_query_text}><td>{item.normalized_query_text}</td><td>{item.frequency}</td><td>{item.languages.join(", ")}</td><td>{item.latest_at}</td></tr>)}</tbody></table>
    </section>
  );
}
