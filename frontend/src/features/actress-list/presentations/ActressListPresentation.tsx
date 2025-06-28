"use client";

// Input コンポーネントが存在しないため、HTML input タグを使用
import { Button } from "@/components/ui/button";
import { Search, SortAsc } from "lucide-react";
import { useState } from "react";
import type { ActressListPresentationProps } from "../types";
// Select コンポーネントが存在しないため、HTML select タグを使用
import { ActressCard } from "./ActressCard";

/**
 * 女優一覧表示コンポーネント（Presentational Component）
 * UI表示とユーザーインタラクションを担当
 */
export function ActressListPresentation({
  actresses,
  totalCount,
  currentPage,
  itemsPerPage,
  searchQuery,
  sortBy,
  isLoading,
  error,
}: ActressListPresentationProps) {
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);

  // 検索とソートのハンドラ（親コンポーネントから props で受け取る想定）
  const handleSearch = () => {
    // 実際の検索処理は Container コンポーネントで実装
    window.location.href = `/actresses?search=${encodeURIComponent(localSearchQuery)}&sort_by=${sortBy}`;
  };

  const handleSortChange = (newSortBy: string) => {
    // 実際のソート処理は Container コンポーネントで実装
    const params = new URLSearchParams();
    if (localSearchQuery) params.append("search", localSearchQuery);
    params.append("sort_by", newSortBy);
    window.location.href = `/actresses?${params.toString()}`;
  };

  const handlePageChange = (page: number) => {
    const params = new URLSearchParams();
    if (localSearchQuery) params.append("search", localSearchQuery);
    params.append("sort_by", sortBy);
    params.append("page", page.toString());
    window.location.href = `/actresses?${params.toString()}`;
  };

  const totalPages = Math.ceil(totalCount / itemsPerPage);
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalCount);

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-400 mb-4">エラーが発生しました</div>
        <div className="text-gray-400 text-sm">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-2">女優一覧</h1>
        <p className="text-gray-400">
          {totalCount > 0
            ? `${totalCount}名の女優が登録されています`
            : "女優が見つかりませんでした"}
        </p>
      </div>

      {/* 検索・ソートエリア */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        {/* 検索ボックス */}
        <div className="flex gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="女優名で検索..."
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 text-white rounded-md focus:outline-none focus:border-zinc-600"
            />
          </div>
          <Button onClick={handleSearch} disabled={isLoading} variant="secondary">
            検索
          </Button>
        </div>

        {/* ソート選択 */}
        <div className="flex items-center gap-2">
          <SortAsc className="w-4 h-4 text-gray-400" />
          <select
            value={sortBy}
            onChange={(e) => handleSortChange(e.target.value)}
            className="px-3 py-2 bg-zinc-800 border border-zinc-700 text-white rounded-md focus:outline-none focus:border-zinc-600"
          >
            <option value="name">名前順</option>
            <option value="person_id">ID順</option>
            <option value="created_at">登録順</option>
          </select>
        </div>
      </div>

      {/* ローディング状態 */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="text-gray-400">読み込み中...</div>
        </div>
      )}

      {/* 女優グリッド */}
      {!isLoading && actresses.length > 0 && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {actresses.map((actress) => (
              <ActressCard key={actress.person_id} actress={actress} />
            ))}
          </div>

          {/* ページネーション情報 */}
          <div className="text-center text-gray-400 text-sm">
            {startItem}-{endItem}件 / 全{totalCount}件
          </div>

          {/* ページネーション */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <Button
                variant="outline"
                disabled={currentPage <= 1}
                onClick={() => handlePageChange(currentPage - 1)}
                className="bg-zinc-800 border-zinc-700 text-white hover:bg-zinc-700"
              >
                前へ
              </Button>

              {/* ページ番号表示（簡易版） */}
              <div className="flex items-center gap-2">
                {currentPage > 2 && (
                  <>
                    <Button
                      variant="ghost"
                      onClick={() => handlePageChange(1)}
                      className="text-white hover:bg-zinc-700"
                    >
                      1
                    </Button>
                    {currentPage > 3 && <span className="text-gray-400">...</span>}
                  </>
                )}

                {currentPage > 1 && (
                  <Button
                    variant="ghost"
                    onClick={() => handlePageChange(currentPage - 1)}
                    className="text-white hover:bg-zinc-700"
                  >
                    {currentPage - 1}
                  </Button>
                )}

                <Button variant="default" className="bg-blue-600 text-white">
                  {currentPage}
                </Button>

                {currentPage < totalPages && (
                  <Button
                    variant="ghost"
                    onClick={() => handlePageChange(currentPage + 1)}
                    className="text-white hover:bg-zinc-700"
                  >
                    {currentPage + 1}
                  </Button>
                )}

                {currentPage < totalPages - 1 && (
                  <>
                    {currentPage < totalPages - 2 && <span className="text-gray-400">...</span>}
                    <Button
                      variant="ghost"
                      onClick={() => handlePageChange(totalPages)}
                      className="text-white hover:bg-zinc-700"
                    >
                      {totalPages}
                    </Button>
                  </>
                )}
              </div>

              <Button
                variant="outline"
                disabled={currentPage >= totalPages}
                onClick={() => handlePageChange(currentPage + 1)}
                className="bg-zinc-800 border-zinc-700 text-white hover:bg-zinc-700"
              >
                次へ
              </Button>
            </div>
          )}
        </>
      )}

      {/* 結果なし */}
      {!isLoading && actresses.length === 0 && !error && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            {searchQuery
              ? "検索条件に一致する女優が見つかりませんでした"
              : "女優が登録されていません"}
          </div>
          {searchQuery && (
            <Button
              variant="secondary"
              onClick={() => {
                setLocalSearchQuery("");
                window.location.href = "/actresses";
              }}
            >
              検索をクリア
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
