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

      {/* 検索結果エリア */}
      <div className="mb-12">
        <h2 className="text-xl font-semibold mb-6 text-center">類似度の高い人物</h2>

        {/* レスポンシブレイアウト */}
        <div className="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-12">
          {/* 2位（存在する場合） */}
          {formattedResults[1] && (
            <div className="order-2 lg:order-1">
              <PersonCard person={formattedResults[1]} isWinner={false} className="w-64 lg:w-72" />
            </div>
          )}

          {/* 1位（中央・大きめ） */}
          <div className="order-1 lg:order-2">
            <PersonCard person={formattedResults[0]} isWinner={true} className="w-80 lg:w-96" />
          </div>

          {/* 3位（存在する場合） */}
          {formattedResults[2] && (
            <div className="order-3 lg:order-3">
              <PersonCard person={formattedResults[2]} isWinner={false} className="w-64 lg:w-72" />
            </div>
          )}
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
    <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
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
    </main>
  );
}

/**
 * 検索結果が見つからない場合のエラー表示
 */
function SearchResultsNotFound() {
  return (
    <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
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
    </main>
  );
}

/**
 * 検索結果が空の場合の表示
 */
function SearchResultsEmpty() {
  return (
    <main className="relative min-h-screen bg-zinc-900 text-white p-4 overflow-hidden">
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
    </main>
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
