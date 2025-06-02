"use client";

import { Button } from "@/components/ui/button";
import Image from "next/image";
import type React from "react";

interface ImageUploadZoneProps {
  onImageSelect: (file: File) => void;
  onSearch: () => void;
  selectedImage: File | null;
  previewUrl: string | null;
}

export function ImageUploadZone({ onImageSelect, onSearch, previewUrl }: ImageUploadZoneProps) {
  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImageSelect(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div
        className="w-full bg-[#1a1a1a] border border-gray-700 p-6 rounded-xl transition-colors duration-200 hover:border-pink-500 cursor-pointer"
        onClick={() => document.getElementById("fileInput")?.click()}
        onKeyDown={(e) => e.key === "Enter" && document.getElementById("fileInput")?.click()}
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
          <div className="text-base text-gray-300 mb-2">画像を選択</div>
          <div className="text-xs text-gray-500">クリックして選択</div>
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
      </div>
      <Button type="submit" className="w-full bg-pink-600 hover:bg-pink-700">
        検索する
      </Button>
    </form>
  );
}
