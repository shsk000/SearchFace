import { createLogger } from "@/lib/logger";
import type { SearchSessionResponse } from "./types";

const logger = createLogger("SearchResults");

/**
 * 検索セッション結果を取得する
 * @param sessionId 検索セッションID
 * @returns 検索セッション結果またはnull
 */
export async function getSearchSessionResults(
  sessionId: string,
): Promise<SearchSessionResponse | null> {
  try {
    logger.info("検索セッション結果を取得開始", { sessionId });

    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const response = await fetch(`${API_BASE_URL}/api/search/${sessionId}`, {
      next: { revalidate: 86400 }, // 1日（24時間）キャッシュ
    });

    if (!response.ok) {
      logger.error("検索セッション結果の取得に失敗", {
        sessionId,
        status: response.status,
        statusText: response.statusText,
      });
      return null;
    }

    const data = await response.json();
    logger.info("検索セッション結果の取得に成功", {
      sessionId,
      resultCount: data.results?.length || 0,
    });

    return data;
  } catch (error) {
    logger.error("検索セッション結果の取得中にエラー", { sessionId, error });
    return null;
  }
}
