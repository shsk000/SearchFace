import { createLogger } from "@/lib/logger";
import { getActressList } from "../api";
import { ActressListPresentation } from "../presentations/ActressListPresentation";
import type { ActressListParams } from "../types";

const logger = createLogger("ActressListContainer");

interface ActressListContainerProps {
  searchParams?: {
    page?: string;
    search?: string;
    sort_by?: string;
  };
}

/**
 * 女優一覧コンテナコンポーネント（Server Component）
 * データ取得とビジネスロジックを担当
 */
export default async function ActressListContainer({
  searchParams = {},
}: ActressListContainerProps) {
  // パラメータを解析
  const currentPage = Number.parseInt(searchParams.page || "1", 10);
  const searchQuery = searchParams.search || "";
  const sortBy = (searchParams.sort_by as "name" | "person_id" | "created_at") || "name";
  const itemsPerPage = 20;
  const offset = (currentPage - 1) * itemsPerPage;

  // API呼び出しパラメータを構築
  const apiParams: ActressListParams = {
    limit: itemsPerPage,
    offset,
    sort_by: sortBy,
  };

  if (searchQuery) {
    apiParams.search = searchQuery;
  }

  logger.info("女優一覧データを取得開始", {
    currentPage,
    searchQuery,
    sortBy,
    apiParams,
  });

  // データを取得
  const response = await getActressList(apiParams);

  if (!response) {
    logger.error("女優一覧データの取得に失敗");
    return (
      <ActressListPresentation
        actresses={[]}
        totalCount={0}
        currentPage={currentPage}
        itemsPerPage={itemsPerPage}
        searchQuery={searchQuery}
        sortBy={sortBy}
        isLoading={false}
        error="データの取得に失敗しました。しばらく時間をおいて再度お試しください。"
      />
    );
  }

  logger.info("女優一覧データ取得成功", {
    count: response.persons.length,
    totalCount: response.total_count,
    hasMore: response.has_more,
  });

  return (
    <ActressListPresentation
      actresses={response.persons}
      totalCount={response.total_count}
      currentPage={currentPage}
      itemsPerPage={itemsPerPage}
      searchQuery={searchQuery}
      sortBy={sortBy}
      isLoading={false}
      error={null}
    />
  );
}
