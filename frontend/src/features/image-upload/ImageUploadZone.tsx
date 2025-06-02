'use client';

import React, { useState } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";

interface ImageUploadZoneProps {
  onImageSelect: (file: File) => void;
  onSearch: () => void;
  selectedImage: File | null;
  previewUrl: string | null;
}

export function ImageUploadZone({
  onImageSelect,
  onSearch,
  selectedImage,
  previewUrl,
}: ImageUploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImageSelect(file);
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
      onImageSelect(file);
    }
  };

  const handleZoneClick = () => {
    document.getElementById("fileInput")?.click();
  };

  return (
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
        onClick={onSearch}
        className="w-full bg-pink-600 hover:bg-pink-700 mt-2"
      >
        検索する
      </Button>
    </div>
  );
} 