import { SearchResultsDisplay } from "@/features/search-results";

interface ResultPageProps {
  params: Promise<{ id: string }>;
}

export default async function ResultPage({ params }: ResultPageProps) {
  const { id } = await params;

  return <SearchResultsDisplay sessionId={id} />;
}
