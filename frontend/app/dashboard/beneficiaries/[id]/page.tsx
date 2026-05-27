import { BeneficiaryDetailClient } from "./BeneficiaryDetailClient";

export default async function BeneficiaryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <BeneficiaryDetailClient beneficiaryId={id} />;
}
