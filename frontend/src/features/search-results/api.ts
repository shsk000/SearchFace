import type { SearchSessionResponse } from "./types";

/**
 * 検索セッション結果を取得する
 * @param sessionId 検索セッションID
 * @returns 検索セッション結果またはnull
 */
export async function getSearchSessionResults(
  sessionId: string,
): Promise<SearchSessionResponse | null> {
  try {
    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const response = await fetch(`${API_BASE_URL}/api/search/${sessionId}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      console.error("Failed to fetch session results:", response.status);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching session results:", error);
    return null;
  }
}
