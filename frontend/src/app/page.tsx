"use client";

import React, { useState } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const bgImages = [
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/sone00682/sone00682ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/nima00045/nima00045ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/sone00687/sone00687ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/dsvr00052/dsvr00052ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/nima00049/nima00049ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/royd00213/royd00213ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/ngod00253/ngod00253ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/jums00066/jums00066ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/savr00631/savr00631ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/mkmp00601/mkmp00601ps.jpg?w=147&h=200&f=webp&t=margin",

    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/xvsr00810/xvsr00810ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/lulu00328/lulu00328ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/usba00083/usba00083ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/cspl00013/cspl00013ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/savr00362/savr00362ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/pfes00058/pfes00058ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/lulu00243/lulu00243ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/bnst00078/bnst00078ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/1namh00007/1namh00007ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/gdrd00006/gdrd00006ps.jpg?w=147&h=200&f=webp&t=margin",

    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/ofje00484/ofje00484ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/hnvr00139/hnvr00139ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/mudr00282/mudr00282ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/dass00572/dass00572ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/cawd00817/cawd00817ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/h_237nacr00850/h_237nacr00850ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/mdvr00348/mdvr00348ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/mdbk00338/mdbk00338ps.jpg?w=147&h=200&f=webp&t=margin",
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/midv00946/midv00946ps.jpg?w=147&h=200&f=webp&t=margin",
  ];

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleZoneClick = () => {
    document.getElementById("fileInput")?.click();
  };

  const handleSearch = () => {
    if (selectedImage) {
      setHasSearched(true);
    }
  };

  return (
    <main className="relative min-h-screen bg-[#111] text-white flex items-center justify-center p-4 overflow-hidden">
      {/* 背景画像を複数枚並べて表示 */}
      <div className="fixed z-0 grid grid-cols-4 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 w-full h-full pointer-events-none top-0 left-0 right-0 bottom-0 mx-auto">
        {bgImages.map((url, idx) => (
          <div key={idx} className="w-full h-full aspect-[1/1.361] relative">
            <img
              src={url}
              alt="bg"
              className="object-cover w-full h-full opacity-60  select-none blur-sm"
              draggable={false}
              loading="lazy"
              fetchPriority="low"
            />
          </div>
        ))}
        {/* オーバーレイ */}
        <div className="absolute inset-0 bg-black opacity-60" />
      </div>
      <div className="relative z-10 max-w-3xl w-full mx-auto text-center flex flex-col justify-center items-center">
        <h1 className="text-3xl font-bold mb-2">
          【開発中】
          <br />
          妄想が、確信に変わる。
        </h1>
        <p className="text-lg mb-6">
          画像をアップするだけで、そっくりなAV女優が見つかる。
        </p>

        <div
          className={`bg-[#1a1a1a] border ${
            dragActive ? "border-pink-500" : "border-gray-700"
          } p-6 rounded-xl mb-4 transition-colors duration-200`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleZoneClick}
          style={{ cursor: "pointer" }}
        >
          <input
            id="fileInput"
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            style={{ display: "none" }}
          />
          <div className="flex flex-col items-center justify-center py-8">
            <div className="text-3xl mb-2">🖼️</div>
            <div className="text-base text-gray-300 mb-2">
              画像ファイルをドラッグ＆ドロップ
            </div>
            <div className="text-xs text-gray-500">またはクリックして選択</div>
          </div>
          {previewUrl && (
            <div className="mb-4">
              <Image
                src={previewUrl}
                alt="preview"
                width={200}
                height={200}
                className="rounded-lg mx-auto"
              />
            </div>
          )}
          <Button
            onClick={handleSearch}
            className="w-full bg-pink-600 hover:bg-pink-700 mt-2"
          >
            検索する
          </Button>
        </div>

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
