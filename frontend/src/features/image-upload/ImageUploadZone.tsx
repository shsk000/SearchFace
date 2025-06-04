"use client";

import { getErrorMessage } from "@/actions/search/error";
import { searchImage } from "@/actions/search/search";
import { isErrorCode } from "@/actions/search/type";
import { Button } from "@/components/ui/button";
import { logger } from "@/lib/logger";
import Image from "next/image";
import type React from "react";
import { useState } from "react";
import { toast } from "sonner";

interface ImageUploadZoneProps {
  onSearchComplete?: () => void;
}

export function ImageUploadZone({ onSearchComplete }: ImageUploadZoneProps) {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedImage) return;

    try {
      setIsSearching(true);
      const formData = new FormData();
      formData.append("image", selectedImage);
      await searchImage(formData);
      onSearchComplete?.();
    } catch (error) {
      logger.error("Search Result error:", error);
      if (error instanceof Error && isErrorCode(error.message)) {
        const message = error.message;
        const displayMessage = getErrorMessage(message);
        toast.error(displayMessage, {
          closeButton: true,
        });
      }
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div
        className={`w-full bg-[#1a1a1a] border border-gray-700 p-6 rounded-xl transition-colors duration-200 ${
          isSearching
            ? "border-pink-500 cursor-not-allowed"
            : "hover:border-pink-500 cursor-pointer"
        }`}
        onClick={() => !isSearching && document.getElementById("fileInput")?.click()}
        onKeyDown={(e) =>
          e.key === "Enter" && !isSearching && document.getElementById("fileInput")?.click()
        }
      >
        <input
          id="fileInput"
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          style={{ display: "none" }}
        />
        <div className="flex flex-col items-center justify-center py-8">
          {isSearching ? (
            <>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-500 mb-4"></div>
              <div className="text-base text-pink-400 mb-2">画像を検索中...</div>
              <div className="text-xs text-gray-500">しばらくお待ちください</div>
            </>
          ) : (
            <>
              <div className="text-3xl mb-2">🖼️</div>
              <div className="text-base text-gray-300 mb-2">画像を選択</div>
              <div className="text-xs text-gray-500">クリックして選択</div>
            </>
          )}
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
      <Button
        type="submit"
        className="w-full bg-pink-600 hover:bg-pink-700"
        disabled={!selectedImage || isSearching}
      >
        {isSearching ? (
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>検索中...</span>
          </div>
        ) : (
          "検索する"
        )}
      </Button>
    </form>
  );
}
