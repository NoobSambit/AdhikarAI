export default function BulkEligibilityPage() {
  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Bulk Eligibility</h1><p>CSV uploads accept up to 500 rows and 2 MB.</p></div></header>
      <form className="denseForm" action={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/dashboard/bulk-eligibility`} method="post" encType="multipart/form-data">
        <label>CSV file<input name="file" type="file" accept=".csv,text/csv" /></label>
        <button className="primaryButton" type="submit">Upload</button>
      </form>
    </section>
  );
}
