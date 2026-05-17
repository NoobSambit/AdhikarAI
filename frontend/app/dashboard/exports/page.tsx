export default function ExportsPage() {
  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Exports</h1><p>Download beneficiary CSV with organisation-scoped filters.</p></div></header>
      <a className="primaryButton" href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/dashboard/export/beneficiaries.csv`}>Download beneficiaries CSV</a>
    </section>
  );
}
