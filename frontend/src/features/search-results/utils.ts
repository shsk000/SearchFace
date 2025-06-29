import type { PersonWithRank, SearchSessionResult } from "./types";

/**
 * 検索結果をUI表示用のPersonWithRank形式に変換する
 * @param results 検索セッション結果
 * @returns UI表示用の人物データ（最大5位まで）
 *
 * 注意: 以前の3件データとの後方互換性を保持
 * 3件のデータでも正常に動作し、4位・5位は表示されません
 */
export function formatSearchResults(results: SearchSessionResult[]): PersonWithRank[] {
  return results.slice(0, 5).map((result) => ({
    id: result.person_id,
    rank: result.rank,
    name: result.name,
    // バックエンドで計算済みのsimilarityを％表示用に変換
    similarity: Math.round(result.similarity * 100),
    distance: result.distance,
    image_path: result.image_path,
  }));
}
