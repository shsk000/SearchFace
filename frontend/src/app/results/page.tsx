"use client";

import { PersonCard } from "@/components/search/PersonCard";
import { ProductCard } from "@/components/search/ProductCard";
import { Button } from "@/components/ui/button";
import { BackgroundImages } from "@/features/background/BackgroundImages";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

// 仮データ
const mockResults = [
  {
    id: 1,
    name: "山田 美咲",
    similarity: 92,
    image_path: "https://placehold.co/300x300/8B5CF6/FFFFFF?text=No.1",
    rank: 1,
  },
  {
    id: 2,
    name: "佐藤 愛子",
    similarity: 87,
    image_path: "https://placehold.co/300x300/06B6D4/FFFFFF?text=No.2",
    rank: 2,
  },
  {
    id: 3,
    name: "田中 美優",
    similarity: 84,
    image_path: "https://placehold.co/300x300/10B981/FFFFFF?text=No.3",
    rank: 3,
  },
];

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

export default function ResultsPage() {
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
          <h1 className="text-2xl font-bold">検索結果</h1>
          <div className="w-24" /> {/* スペーサー */}
        </div>

        {/* 検索結果エリア */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold mb-6 text-center">類似度の高い人物</h2>

          {/* レスポンシブレイアウト */}
          <div className="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-12">
            {/* 2位 */}
            <div className="order-2 lg:order-1">
              <PersonCard person={mockResults[1]} isWinner={false} className="w-64 lg:w-72" />
            </div>

            {/* 1位（中央・大きめ） */}
            <div className="order-1 lg:order-2">
              <PersonCard person={mockResults[0]} isWinner={true} className="w-80 lg:w-96" />
            </div>

            {/* 3位 */}
            <div className="order-3 lg:order-3">
              <PersonCard person={mockResults[2]} isWinner={false} className="w-64 lg:w-72" />
            </div>
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
