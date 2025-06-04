"use client";

import { BackgroundImages } from "@/features/background/BackgroundImages";
import { ImageUploadZone } from "@/features/image-upload/ImageUploadZone";
import { useState } from "react";

export default function Home() {
  const [hasSearched, setHasSearched] = useState(false);

  return (
    <main className="relative min-h-screen bg-[#111] text-white flex items-center justify-center p-4 overflow-hidden">
      <BackgroundImages />
      <div className="relative z-10 max-w-3xl w-full mx-auto text-center flex flex-col justify-center items-center">
        <h1 className="text-3xl font-bold mb-2">
          【開発中】
          <br />
          妄想が、確信に変わる。
        </h1>
        <p className="text-lg mb-6">画像をアップするだけで、そっくりなAV女優が見つかる。</p>

        <ImageUploadZone onSearchComplete={() => setHasSearched(true)} />

        {hasSearched && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mt-8">
            <p>検索結果</p>
          </div>
        )}

        <footer className="mt-12 text-sm text-gray-500 relative z-10">
          <p>18歳未満の方のご利用は固くお断りします。</p>
          <p className="mt-1">画像は著作権に配慮したものをご利用ください。</p>
        </footer>
      </div>
    </main>
  );
}
