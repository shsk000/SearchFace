import type { PersonWithRank, SearchSessionResult } from "./types";

/**
 * 検索結果をUI表示用のPersonWithRank形式に変換する
 * @param results 検索セッション結果
 * @returns UI表示用の人物データ（最大3位まで）
 */
export function formatSearchResults(results: SearchSessionResult[]): PersonWithRank[] {
  return results.slice(0, 3).map((result) => ({
    id: result.person_id,
    rank: result.rank,
    name: result.name,
    // 類似度を距離から計算（距離が小さいほど類似度が高い）
    similarity: Math.max(0, Math.round((1 - result.distance) * 100)),
    distance: result.distance,
    image_path: result.image_path,
  }));
}
