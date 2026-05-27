"use client";

import { useEffect, useState } from "react";
import { getStatusBoard, updateDashboardApplicationStatus } from "@/lib/api";

const columns = ["not_started", "documents_gathering", "submitted", "approved"];

export default function StatusBoardPage() {
  const [board, setBoard] = useState<Record<string, Array<Record<string, string>>>>({});

  useEffect(() => {
    getStatusBoard().then(setBoard).catch(() => setBoard({}));
  }, []);

  async function move(statusId: string, status: string) {
    await updateDashboardApplicationStatus(statusId, status);
    setBoard(await getStatusBoard());
  }

  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Status Board</h1><p>Move application records across PRD columns.</p></div></header>
      <div className="kanbanGrid">
        {columns.map((column) => (
          <section className="kanbanColumn" key={column}>
            <h2>{column.replaceAll("_", " ")}</h2>
            {(board[column] ?? []).map((card) => (
              <article className="kanbanCard" key={card.status_id}>
                <strong><a href={`/dashboard/beneficiaries/${card.beneficiary_id}`}>{card.name}</a></strong>
                <span>{card.scheme_id}</span>
                <select value={card.status} onChange={(event) => move(card.status_id, event.target.value)} aria-label={`Update ${card.name} status`}>
                  <option value="not_started">not started</option>
                  <option value="documents_gathering">documents</option>
                  <option value="submitted">submitted</option>
                  <option value="approved">approved</option>
                  <option value="rejected">rejected</option>
                </select>
              </article>
            ))}
          </section>
        ))}
      </div>
    </section>
  );
}
