import { PersonCard } from "@/components/search/PersonCard";
import { ProductCard } from "@/components/search/ProductCard";
import { Button } from "@/components/ui/button";
import { BackgroundImages } from "@/features/background/BackgroundImages";
import { AlertCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { getSearchSessionResults } from "./api";
import { mockProducts } from "./data";
import type { SearchSessionResponse } from "./types";
import { formatSearchResults } from "./utils";

interface SearchResultsDisplayProps {
  sessionId: string;
}

/**
 * 検索結果を表示するメインコンポーネント
 */
export default async function SearchResultsDisplay({ sessionId }: SearchResultsDisplayProps) {
  const sessionData = await getSearchSessionResults(sessionId);

  if (!sessionData) {
    return <SearchResultsNotFound />;
  }

  // 検索結果が空の場合
  if (!sessionData.results || sessionData.results.length === 0) {
    return <SearchResultsEmpty />;
  }

  const formattedResults = formatSearchResults(sessionData.results);

  return (
    <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
      <BackgroundImages />

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* ヘッダー */}
        <SearchResultsHeader sessionData={sessionData} />

        {/* 検索結果エリア */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold mb-6 text-center">類似度の高い人物</h2>

          {/* レスポンシブレイアウト */}
          <div className="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-12">
            {/* 2位（存在する場合） */}
            {formattedResults[1] && (
              <div className="order-2 lg:order-1">
                <PersonCard
                  person={formattedResults[1]}
                  isWinner={false}
                  className="w-64 lg:w-72"
                />
              </div>
            )}

            {/* 1位（中央・大きめ） */}
            <div className="order-1 lg:order-2">
              <PersonCard person={formattedResults[0]} isWinner={true} className="w-80 lg:w-96" />
            </div>

            {/* 3位（存在する場合） */}
            {formattedResults[2] && (
              <div className="order-3 lg:order-3">
                <PersonCard
                  person={formattedResults[2]}
                  isWinner={false}
                  className="w-64 lg:w-72"
                />
              </div>
            )}
          </div>
        </div>

        {/* アフィリエイト商品エリア */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4 text-center">最新商品</h3>

          <div className="overflow-x-auto">
            <div className="flex gap-4 pb-4 min-w-max">
              {mockProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        </div>

        {/* フッター */}
        <SearchResultsFooter />
      </div>
    </main>
  );
}

/**
 * 検索結果ヘッダーコンポーネント
 */
function SearchResultsHeader({ sessionData }: { sessionData: SearchSessionResponse }) {
  return (
    <div className="flex items-center justify-between mb-8">
      <Link href="/">
        <Button variant="ghost" className="text-white hover:bg-white/10">
          <ArrowLeft className="w-4 h-4 mr-2" />
          検索に戻る
        </Button>
      </Link>
      <div className="text-center">
        <h1 className="text-2xl font-bold">検索結果</h1>
        <p className="text-sm text-gray-400">
          {sessionData.metadata?.processing_time
            ? `処理時間: ${sessionData.metadata.processing_time.toFixed(2)}秒`
            : `セッション: ${sessionData.session_id.slice(0, 8)}...`}
        </p>
      </div>
      <div className="w-24" /> {/* スペーサー */}
    </div>
  );
}

/**
 * 検索結果が見つからない場合のエラー表示
 */
function SearchResultsNotFound() {
  return (
    <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
      <BackgroundImages />
      <div className="relative z-10 max-w-7xl mx-auto flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-4">検索結果が見つかりません</h2>
          <p className="text-gray-400 mb-6">セッションIDが無効か、結果が期限切れです。</p>
          <Link href="/">
            <Button className="bg-pink-600 hover:bg-pink-700">
              <ArrowLeft className="w-4 h-4 mr-2" />
              検索画面に戻る
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}

/**
 * 検索結果が空の場合の表示
 */
function SearchResultsEmpty() {
  return (
    <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
      <BackgroundImages />
      <div className="relative z-10 max-w-7xl mx-auto flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-bold mb-4">検索結果が見つかりませんでした</h2>
          <p className="text-gray-400 mb-6">別の画像で再度お試しください。</p>
          <Link href="/">
            <Button className="bg-pink-600 hover:bg-pink-700">
              <ArrowLeft className="w-4 h-4 mr-2" />
              検索画面に戻る
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}

/**
 * フッターコンポーネント
 */
function SearchResultsFooter() {
  return (
    <footer className="text-center text-sm text-gray-400 mt-12">
      <p>18歳未満の方のご利用は固くお断りします。</p>
      <p className="mt-1">画像は著作権に配慮したものをご利用ください。</p>
    </footer>
  );
}
