"use client";

import { getErrorMessage } from "@/actions/search/error";
import { searchImage } from "@/actions/search/search";
import { isErrorCode } from "@/actions/search/type";
import { Button } from "@/components/ui/button";
import { logger } from "@/lib/logger";
import Image from "next/image";
import { useRouter } from "next/navigation";
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
  const [isDragOver, setIsDragOver] = useState(false);
  const router = useRouter();

  const validateAndSetFile = (file: File) => {
    // ファイルサイズチェック（500KB = 500 * 1024 bytes）
    const maxSizeKB = 500;
    const maxSizeBytes = maxSizeKB * 1024;

    if (file.size > maxSizeBytes) {
      toast.error(`ファイルサイズが大きすぎます（${maxSizeKB}KB以下にしてください）`, {
        closeButton: true,
      });
      return false;
    }

    // ファイル形式チェック
    if (!file.type.startsWith("image/")) {
      toast.error("画像ファイルを選択してください", {
        closeButton: true,
      });
      return false;
    }

    setSelectedImage(file);
    setPreviewUrl(URL.createObjectURL(file));
    return true;
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!validateAndSetFile(file)) {
        // input要素をリセット
        e.target.value = "";
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (!isSearching) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLButtonElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLButtonElement>) => {
    e.preventDefault();
    setIsDragOver(false);

    if (isSearching) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedImage || isSearching) return;

    setIsSearching(true);

    try {
      const formData = new FormData();
      formData.append("image", selectedImage);

      const result = await searchImage(formData);

      logger.info("検索成功", { result });
      toast.success("検索が完了しました！");

      // 結果ページに遷移（session_idベース）
      router.push(`/result/${result.search_session_id}`);

      onSearchComplete?.();
    } catch (error) {
      logger.error("検索エラー", { error });

      let errorMessage = "検索中にエラーが発生しました";

      if (error instanceof Error && isErrorCode(error.message)) {
        const errorCode = error.message;
        errorMessage = getErrorMessage(errorCode);
      }

      toast.error(errorMessage, {
        closeButton: true,
      });
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="text-xl font-bold text-white mb-2 text-center drop-shadow-lg">
        画像をアップロードしてそっくりAV女優を検索！
      </div>
      <button
        type="button"
        className={`w-full max-w-md mx-auto bg-[#18181b]/80 border-2 p-8 rounded-2xl shadow-xl transition-all duration-300
          ${
            isSearching
              ? "border-[#ee2737] ring-2 ring-[#ee2737]/40 cursor-not-allowed"
              : isDragOver
                ? "border-[#ee2737] ring-2 ring-[#ee2737]/60 scale-105 bg-[#ee2737]/10"
                : "border-zinc-700 hover:border-[#ee2737] hover:shadow-2xl hover:scale-105 cursor-pointer"
          }
        `}
        onClick={() => !isSearching && document.getElementById("fileInput")?.click()}
        onKeyDown={(e) =>
          e.key === "Enter" && !isSearching && document.getElementById("fileInput")?.click()
        }
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        tabIndex={0}
        aria-label="画像をアップロード"
        disabled={isSearching}
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
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#ee2737] mb-4" />
              <div className="text-base text-[#ee2737] mb-2">画像を検索中...</div>
              <div className="text-xs text-gray-400">しばらくお待ちください</div>
            </>
          ) : (
            <>
              <div className="text-4xl mb-2">🖼️</div>
              <div className="text-lg text-white font-semibold mb-2">
                {isDragOver ? "ここにドロップ" : "画像を選択"}
              </div>
              <div className="text-xs text-gray-400">
                {isDragOver
                  ? "画像ファイルをここにドロップしてください"
                  : "クリックまたはドラッグ&ドロップ（500KB以下）"}
              </div>
            </>
          )}
        </div>
        {previewUrl && (
          <div className="mb-4">
            <Image
              src={previewUrl}
              alt="preview"
              width={220}
              height={220}
              className="rounded-lg mx-auto shadow-lg border-2 border-[#ee2737]/60"
            />
          </div>
        )}
      </button>
      <Button
        type="submit"
        className="w-full h-14 text-lg font-bold bg-[#ee2737] hover:bg-[#d81e2b] shadow-lg transition-all duration-200 rounded-xl"
        disabled={!selectedImage || isSearching}
      >
        {isSearching ? (
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
            <span>検索中...</span>
          </div>
        ) : (
          "検索する"
        )}
      </Button>
    </form>
  );
}
