import ProductsContainer from "@/features/products/containers/ProductsContainer";
import { getSearchSessionResults } from "../api";
import { SearchResultsPresentation } from "../presentations/SearchResultsPresentation";
import { formatSearchResults } from "../utils";

interface SearchResultsContainerProps {
  sessionId: string;
}

/**
 * 検索結果のデータ取得・ビジネスロジックを担当するContainerコンポーネント
 * Server Componentとして実装
 */
export default async function SearchResultsContainer({ sessionId }: SearchResultsContainerProps) {
  try {
    // データ取得
    const sessionData = await getSearchSessionResults(sessionId);

    if (!sessionData) {
      return (
        <SearchResultsPresentation
          sessionData={null}
          formattedResults={null}
          error="検索結果が見つかりません"
        />
      );
    }

    // 検索結果が空の場合
    if (!sessionData.results || sessionData.results.length === 0) {
      return (
        <SearchResultsPresentation
          sessionData={sessionData}
          formattedResults={[]}
          error="検索結果が見つかりませんでした"
        />
      );
    }

    // データ変換
    const formattedResults = formatSearchResults(sessionData.results);

    // Presentationalコンポーネントに渡す
    return (
      <>
        <SearchResultsPresentation
          sessionData={sessionData}
          formattedResults={formattedResults}
          error={null}
        />
        {/* 関連商品エリア */}
        {formattedResults[0]?.id && (
          <div className="mb-8">
            <ProductsContainer personId={formattedResults[0].id} limit={20} className="" />
          </div>
        )}
      </>
    );
  } catch {
    // エラー状態を渡す
    return (
      <SearchResultsPresentation
        sessionData={null}
        formattedResults={null}
        error="データ取得に失敗しました"
      />
    );
  }
}
