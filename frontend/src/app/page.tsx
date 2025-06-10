import { BackgroundImages } from "@/features/background/BackgroundImages";
import { ImageUploadZone } from "@/features/image-upload/ImageUploadZone";
import SearchRanking from "@/features/ranking/SearchRanking";
import { Suspense } from "react";
import type { Metadata } from "next";

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
    <main className="relative min-h-screen bg-[#111] text-white flex items-center justify-center p-4 overflow-hidden">
      <BackgroundImages />
      <div className="relative z-10 max-w-4xl w-full mx-auto text-center flex flex-col justify-center items-center">
        <h1 className="text-3xl font-bold mb-2">
          【開発中】
          <br />
          妄想が、確信に変わる。
        </h1>
        <p className="text-lg mb-6">画像をアップするだけで、そっくりなAV女優が見つかる。</p>

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

        <footer className="mt-12 text-sm text-gray-500 relative z-10">
          <p>18歳未満の方のご利用は固くお断りします。</p>
          <p className="mt-1">画像は著作権に配慮したものをご利用ください。</p>
        </footer>
      </div>
    </main>
  );
}
