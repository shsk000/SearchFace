"use client";

import { PersonCard } from "@/components/search/PersonCard";
import { Button } from "@/components/ui/button";
import { AlertCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { PersonWithRank, SearchSessionResponse } from "../types";

interface SearchResultsPresentationProps {
  sessionData: SearchSessionResponse | null;
  formattedResults: PersonWithRank[] | null;
  error: string | null;
}

/**
 * 検索結果のUI表示を担当するPresentationalコンポーネント
 * Client Componentとして実装
 */
export function SearchResultsPresentation({
  sessionData,
  formattedResults,
  error,
}: SearchResultsPresentationProps) {
  // エラー状態の表示
  if (error) {
    return <ErrorDisplay error={error} />;
  }

  // データが存在しない場合
  if (!sessionData || !formattedResults) {
    return <SearchResultsNotFound />;
  }

  // 検索結果が空の場合
  if (formattedResults.length === 0) {
    return <SearchResultsEmpty />;
  }

  return (
    <>
      {/* ヘッダー */}
      <SearchResultsHeader sessionData={sessionData} />

      {/* 検索結果エリア - コンパクト */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-4 text-center">類似度の高い人物</h2>

        {/* レスポンシブレイアウト - 3件データとの後方互換性を保持 */}
        <div className="max-w-6xl mx-auto">
          {/* 大画面: 1行神殿風レイアウト (800px以上) */}
          <div className="hidden min-[800px]:flex items-end justify-center gap-4">
            {/* 4位 (低) */}
            {formattedResults[3] && (
              <div className="flex flex-col items-center">
                <PersonCard person={formattedResults[3]} isWinner={false} className="w-28" />
              </div>
            )}

            {/* 2位 (中) */}
            {formattedResults[1] && (
              <div className="flex flex-col items-center mb-8">
                <PersonCard person={formattedResults[1]} isWinner={false} className="w-32" />
              </div>
            )}

            {/* 1位 (最高・ゴールド) */}
            <div className="flex flex-col items-center mb-8">
              <PersonCard person={formattedResults[0]} isWinner={true} className="w-48" />
            </div>

            {/* 3位 (中) */}
            {formattedResults[2] && (
              <div className="flex flex-col items-center mb-8">
                <PersonCard person={formattedResults[2]} isWinner={false} className="w-32" />
              </div>
            )}

            {/* 5位 (低) */}
            {formattedResults[4] && (
              <div className="flex flex-col items-center">
                <PersonCard person={formattedResults[4]} isWinner={false} className="w-28" />
              </div>
            )}
          </div>

          {/* 中画面: コンパクト神殿風レイアウト (600px-799px) */}
          <div className="hidden min-[600px]:flex min-[800px]:hidden items-end justify-center gap-2">
            {/* 4位 (低) */}
            {formattedResults[3] && (
              <div className="flex flex-col items-center">
                <PersonCard person={formattedResults[3]} isWinner={false} className="w-24" />
              </div>
            )}

            {/* 2位 (中) */}
            {formattedResults[1] && (
              <div className="flex flex-col items-center mb-6">
                <PersonCard person={formattedResults[1]} isWinner={false} className="w-28" />
              </div>
            )}

            {/* 1位 (最高・ゴールド) */}
            <div className="flex flex-col items-center mb-12">
              <PersonCard person={formattedResults[0]} isWinner={true} className="w-36" />
            </div>

            {/* 3位 (中) */}
            {formattedResults[2] && (
              <div className="flex flex-col items-center mb-6">
                <PersonCard person={formattedResults[2]} isWinner={false} className="w-28" />
              </div>
            )}

            {/* 5位 (低) */}
            {formattedResults[4] && (
              <div className="flex flex-col items-center">
                <PersonCard person={formattedResults[4]} isWinner={false} className="w-24" />
              </div>
            )}
          </div>

          {/* 小画面: 横並びレイアウト (600px未満) */}
          <div className="min-[600px]:hidden flex flex-col items-center gap-4 px-4">
            {formattedResults.slice(0, 5).map((person, index) => (
              <div key={person.id} className="w-full max-w-md">
                <PersonCard
                  person={person}
                  isWinner={index === 0}
                  isCompact={true}
                  className="w-full"
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

/**
 * エラー表示コンポーネント
 */
function ErrorDisplay({ error }: { error: string }) {
  return (
    <div className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
      <div className="relative z-10 max-w-7xl mx-auto flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-4">エラーが発生しました</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <Link href="/">
            <Button className="bg-pink-600 hover:bg-pink-700">
              <ArrowLeft className="w-4 h-4 mr-2" />
              検索画面に戻る
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

/**
 * 検索結果が見つからない場合のエラー表示
 */
function SearchResultsNotFound() {
  return (
    <div className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
      <div className="relative z-10 max-w-7xl mx-auto flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-4">検索結果が見つかりません</h2>
          <p className="text-gray-400 mb-6">セッションIDが無効か、結果が期限切れです。</p>
          <Link href="/">
            <Button className="bg-pink-600 hover:bg-pink-700">
              <ArrowLeft className="w-4 h-4 mr-2" />
              検索画面に戻る
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

/**
 * 検索結果が空の場合の表示
 */
function SearchResultsEmpty() {
  return (
    <div className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
      <div className="relative z-10 max-w-7xl mx-auto flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-bold mb-4">検索結果が見つかりませんでした</h2>
          <p className="text-gray-400 mb-6">別の画像で再度お試しください。</p>
          <Link href="/">
            <Button className="bg-pink-600 hover:bg-pink-700">
              <ArrowLeft className="w-4 h-4 mr-2" />
              検索画面に戻る
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

/**
 * 検索結果ヘッダーコンポーネント
 */
function SearchResultsHeader({ sessionData }: { sessionData: SearchSessionResponse }) {
  return (
    <div className="flex items-center justify-between mb-8">
      <Link href="/">
        <Button variant="ghost" className="text-white hover:bg-white/10">
          <ArrowLeft className="w-4 h-4 mr-2" />
          検索に戻る
        </Button>
      </Link>
      <div className="text-center">
        <h1 className="text-2xl font-bold">検索結果</h1>
        <p className="text-sm text-gray-400">
          {sessionData.metadata?.processing_time
            ? `処理時間: ${sessionData.metadata.processing_time.toFixed(2)}秒`
            : `セッション: ${sessionData.session_id.slice(0, 8)}...`}
        </p>
      </div>
      <div className="w-24" /> {/* スペーサー */}
    </div>
  );
}
