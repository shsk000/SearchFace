"use client";

import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ImageUploadZone } from "@/features/image-upload/ImageUploadZone";
import { BackgroundImages } from "@/features/background/BackgroundImages";
import { searchImage } from "@/actions/search/search";
import { SearchResultError } from "@/actions/search/error";

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleImageSelect = (file: File) => {
    setSelectedImage(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleSearch = async () => {
    if (selectedImage) {
      try {
        const formData = new FormData();
        formData.append('image', selectedImage);
        await searchImage(formData);
        setHasSearched(true);
      } catch (error) {
        console.error('検索エラー:', error);
        // TODO: エラー表示のUI実装
      }
    }
  };

  return (
    <main className="relative min-h-screen bg-[#111] text-white flex items-center justify-center p-4 overflow-hidden">
      <BackgroundImages />
      <div className="relative z-10 max-w-3xl w-full mx-auto text-center flex flex-col justify-center items-center">
        <h1 className="text-3xl font-bold mb-2">
          【開発中】
          <br />
          妄想が、確信に変わる。
        </h1>
        <p className="text-lg mb-6">
          画像をアップするだけで、そっくりなAV女優が見つかる。
        </p>

        <ImageUploadZone
          onImageSelect={handleImageSelect}
          onSearch={handleSearch}
          selectedImage={selectedImage}
          previewUrl={previewUrl}
        />

        {hasSearched && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mt-8">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="bg-[#1f1f1f] border border-gray-700">
                <CardContent className="p-4">
                  <div className="bg-gray-700 w-full h-40 mb-2 rounded-lg"></div>
                  <p className="text-sm text-white">女優名 {i + 1}</p>
                  <p className="text-xs text-gray-400">類似度: {98 - i}%</p>
                </CardContent>
              </Card>
            ))}
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
