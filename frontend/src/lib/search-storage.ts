import type { SearchSuccessResponse } from "@/actions/search/type";
import { searchSuccessResponseSchema } from "@/actions/search/type";
import { logger } from "@/lib/logger";

const SEARCH_RESULTS_KEY = "searchResults";

/**
 * 検索結果をセッションストレージに保存する
 */
export function saveSearchResults(data: SearchSuccessResponse): void {
  try {
    const dataToStore = JSON.stringify(data);
    sessionStorage.setItem(SEARCH_RESULTS_KEY, dataToStore);
    logger.info("検索結果をセッションストレージに保存しました");
  } catch (error) {
    logger.error("検索結果の保存に失敗しました", { error });
    throw new Error("検索結果の保存に失敗しました");
  }
}

/**
 * セッションストレージから検索結果を取得する
 */
export function getSearchResults(): SearchSuccessResponse | null {
  try {
    const storedResults = sessionStorage.getItem(SEARCH_RESULTS_KEY);

    if (!storedResults) {
      logger.info("セッションストレージに検索結果が見つかりません");
      return null;
    }

    const parsedResults = JSON.parse(storedResults);

    // データ形式の検証
    const validationResult = searchSuccessResponseSchema.safeParse(parsedResults);
    if (!validationResult.success) {
      logger.error("検索結果の形式が不正です", { error: validationResult.error });
      throw new Error("検索結果の形式が不正です");
    }

    logger.info("セッションストレージから検索結果を取得しました");
    return validationResult.data;
  } catch (error) {
    logger.error("検索結果の取得に失敗しました", { error });
    throw new Error("検索結果の取得に失敗しました");
  }
}

/**
 * セッションストレージから検索結果を削除する
 */
export function clearSearchResults(): void {
  try {
    sessionStorage.removeItem(SEARCH_RESULTS_KEY);
    logger.info("セッションストレージから検索結果を削除しました");
  } catch (error) {
    logger.error("検索結果の削除に失敗しました", { error });
  }
}

/**
 * 検索結果を取得して、取得後にセッションストレージから削除する
 * （一度だけ使用する場合）
 */
export function getAndClearSearchResults(): SearchSuccessResponse | null {
  try {
    const results = getSearchResults();
    if (results) {
      clearSearchResults();
    }
    return results;
  } catch (error) {
    // エラーが発生してもクリアは実行する
    clearSearchResults();
    throw error;
  }
}
