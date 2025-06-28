import { Footer } from "@/components/footer/Footer";
import { ImageUploadZone } from "@/features/image-upload/ImageUploadZone";
import SearchRanking from "@/features/ranking/SearchRanking";
import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import { Users, Search } from "lucide-react";

export const metadata: Metadata = {
  title: "そっくりAV女優検索 - 妄想が、確信に変わる。",
  description:
    "画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。",
  keywords: ["AV女優", "顔検索", "そっくり", "AI検索", "画像検索", "類似検索", "アップロード"],
  openGraph: {
    title: "そっくりAV女優検索 - 妄想が、確信に変わる。",
    description:
      "画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。",
    url: "https://www.sokkuri-av.lol",
    siteName: "そっくりAV女優検索",
    images: [
      {
        url: "/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "そっくりAV女優検索 - 妄想が、確信に変わる。",
      },
    ],
    type: "website",
    locale: "ja_JP",
  },
  twitter: {
    card: "summary_large_image",
    title: "そっくりAV女優検索 - 妄想が、確信に変わる。",
    description:
      "画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。",
    images: ["/og-image.jpg"],
  },
  alternates: {
    canonical: "https://www.sokkuri-av.lol",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function Home() {
  return (
    <div className="relative z-10 max-w-4xl w-full mx-auto text-center flex flex-col justify-center items-center">
      {/* ナビゲーションメニュー */}
      <nav className="w-full mb-8">
        <div className="flex justify-center gap-4">
          <Link
            href="/actresses"
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800/50 border border-zinc-700 rounded-lg hover:border-[#ee2737] hover:text-[#ee2737] transition-all duration-300 hover:scale-105"
          >
            <Users className="w-4 h-4" />
            <span className="text-sm">女優一覧</span>
          </Link>
          <Link
            href="/"
            className="flex items-center gap-2 px-4 py-2 bg-[#ee2737]/90 border border-[#ee2737] rounded-lg text-white font-semibold shadow-md hover:bg-[#d81e2b] transition-all duration-300 hover:scale-105"
          >
            <Search className="w-4 h-4" />
            <span className="text-sm">顔検索</span>
          </Link>
        </div>
      </nav>

      <h1 className="text-4xl font-extrabold mb-4 text-white drop-shadow-lg">
        顔画像から、そっくりなAV女優をAIで一発検索！
      </h1>
      <p className="text-lg mb-8 text-gray-200 font-medium">
        画像をアップロードするだけで、AIがあなたの"そっくりAV女優"を瞬時に見つけます。
        <br className="hidden md:block" />
        プライバシーも安心・無料でご利用いただけます。
      </p>

      <ImageUploadZone />

      {/* ランキング表示 - 検索inputの下部に配置 */}
      <div className="w-full mt-8">
        <Suspense
          fallback={
            <div className="bg-zinc-900/90 border-zinc-700 backdrop-blur-sm rounded-xl p-6">
              <p className="text-gray-400 text-center">ランキングを読み込み中...</p>
            </div>
          }
        >
          <SearchRanking />
        </Suspense>
      </div>

      <Footer />
    </div>
  );
}
