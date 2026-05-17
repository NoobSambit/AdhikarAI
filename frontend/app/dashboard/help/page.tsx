const steps = ["create beneficiary", "run eligibility", "explain documents", "update application status", "set follow-up"];

export default function HelpPage() {
  return (
    <section className="dashboardPage">
      <header className="dashboardHeader"><div><h1>Operator Training</h1><p>Five-step assisted workflow.</p></div></header>
      <ol className="trainingList">{steps.map((step) => <li key={step}>{step}</li>)}</ol>
    </section>
  );
}
