import type { SearchSessionResponse, SearchSessionResult } from "@/actions/search/type";
import { PersonCard } from "@/components/search/PersonCard";
import { ProductCard } from "@/components/search/ProductCard";
import { Button } from "@/components/ui/button";
import { BackgroundImages } from "@/features/background/BackgroundImages";
import { AlertCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

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

interface PersonWithRank {
  id: number;
  rank: number;
  name: string;
  similarity: number;
  distance: number;
  image_path: string;
}

async function getSearchSessionResults(sessionId: string): Promise<SearchSessionResponse | null> {
  try {
    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const response = await fetch(`${API_BASE_URL}/api/search/session/${sessionId}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      console.error("Failed to fetch session results:", response.status);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching session results:", error);
    return null;
  }
}

export default async function ResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const sessionData = await getSearchSessionResults(id);

  if (!sessionData) {
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

  // 検索結果が空の場合
  if (!sessionData.results || sessionData.results.length === 0) {
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

  // 検索結果をランク付きのPersonWithRank形式に変換
  const formatResults = (results: SearchSessionResult[]): PersonWithRank[] => {
    return results.slice(0, 3).map((result) => ({
      id: result.person_id,
      rank: result.rank,
      name: result.name,
      // 類似度を距離から計算（距離が小さいほど類似度が高い）
      similarity: Math.max(0, Math.round((1 - result.distance) * 100)),
      distance: result.distance,
      image_path: result.image_path,
    }));
  };

  const formattedResults = formatResults(sessionData.results);

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
              {sessionData.metadata?.processing_time
                ? `処理時間: ${sessionData.metadata.processing_time.toFixed(2)}秒`
                : `セッション: ${sessionData.session_id.slice(0, 8)}...`}
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
