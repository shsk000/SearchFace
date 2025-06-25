import { Content } from "@/components/content/Content";
import { Footer } from "@/components/footer/Footer";
import SearchResultsContainer from "@/features/search-results/containers/SearchResultsContainer";

interface ResultPageProps {
  params: Promise<{ id: string }>;
}

export default async function ResultPage({ params }: ResultPageProps) {
  const { id } = await params;

  return (
    <Content as="main">
      <SearchResultsContainer sessionId={id} />
      <Footer />
    </Content>
  );
}
