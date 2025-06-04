"use client";

import type { SearchResult, SearchSuccessResponse } from "@/actions/search/type";
import { PersonCard } from "@/components/search/PersonCard";
import { ProductCard } from "@/components/search/ProductCard";
import { Button } from "@/components/ui/button";
import { BackgroundImages } from "@/features/background/BackgroundImages";
import { getAndClearSearchResults } from "@/lib/search-storage";
import { AlertCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";

// アフィリエイト商品の仮データ
const mockProducts = [
  {
    id: 1,
    title: "美少女図鑑2024",
    price: "¥3,980",
    image: "https://placehold.co/200x280/F59E0B/FFFFFF?text=商品1",
  },
  {
    id: 2,
    title: "プレミアムコレクション",
    price: "¥5,480",
    image: "https://placehold.co/200x280/EF4444/FFFFFF?text=商品2",
  },
  {
    id: 3,
    title: "限定版フォトブック",
    price: "¥7,200",
    image: "https://placehold.co/200x280/8B5CF6/FFFFFF?text=商品3",
  },
  {
    id: 4,
    title: "スペシャルエディション",
    price: "¥4,800",
    image: "https://placehold.co/200x280/06B6D4/FFFFFF?text=商品4",
  },
  {
    id: 5,
    title: "コンプリートBOX",
    price: "¥12,800",
    image: "https://placehold.co/200x280/10B981/FFFFFF?text=商品5",
  },
];

interface PersonWithRank extends SearchResult {
  id: number;
  rank: number;
}

export default function ResultsPage() {
  const [searchData, setSearchData] = useState<SearchSuccessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const _router = useRouter();
  const hasInitialized = useRef(false);

  useEffect(() => {
    // 既に初期化済みの場合は何もしない（StrictModeの2回目実行対策）
    if (hasInitialized.current) {
      return;
    }

    hasInitialized.current = true;

    try {
      const results = getAndClearSearchResults();

      if (!results) {
        setError("検索結果が見つかりません。検索を再度実行してください。");
        setLoading(false);
        return;
      }

      setSearchData(results);
      setLoading(false);
    } catch (err) {
      setError(`検索結果の読み込みに失敗しました: ${err}`);
      setLoading(false);
    }
  }, []); // 空の依存配列に変更

  // 検索結果をランク付きのPersonWithRank形式に変換
  const formatResults = (results: SearchResult[]): PersonWithRank[] => {
    return results.slice(0, 3).map((result, index) => ({
      ...result,
      id: index + 1,
      rank: index + 1,
      // 類似度を距離から計算（距離が小さいほど類似度が高い）
      similarity: Math.max(0, Math.round((1 - result.distance) * 100)),
    }));
  };

  // ローディング状態
  if (loading) {
    return (
      <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
        <BackgroundImages />
        <div className="relative z-10 max-w-7xl mx-auto flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500 mx-auto mb-4" />
            <p className="text-lg">検索結果を読み込み中...</p>
          </div>
        </div>
      </main>
    );
  }

  // エラー状態
  if (error || !searchData) {
    return (
      <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
        <BackgroundImages />
        <div className="relative z-10 max-w-7xl mx-auto flex items-center justify-center min-h-screen">
          <div className="text-center">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-4">エラーが発生しました</h2>
            <p className="text-gray-400 mb-6">{error}</p>
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

  // 検索結果が空の場合
  if (!searchData.results || searchData.results.length === 0) {
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

  const formattedResults = formatResults(searchData.results);

  return (
    <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
      <BackgroundImages />

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* ヘッダー */}
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
              処理時間: {searchData.processing_time.toFixed(2)}秒
            </p>
          </div>
          <div className="w-24" /> {/* スペーサー */}
        </div>

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
          <h3 className="text-lg font-semibold mb-4 text-center">関連商品</h3>

          <div className="overflow-x-auto">
            <div className="flex gap-4 pb-4 min-w-max">
              {mockProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        </div>

        {/* フッター */}
        <footer className="text-center text-sm text-gray-400 mt-12">
          <p>18歳未満の方のご利用は固くお断りします。</p>
          <p className="mt-1">画像は著作権に配慮したものをご利用ください。</p>
        </footer>
      </div>
    </main>
  );
}
