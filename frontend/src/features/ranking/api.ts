import type { RankingResponse } from "./types";

// ランキングデータを取得する関数
export async function getRankingData(): Promise<RankingResponse | null> {
  try {
    // 環境変数からAPI URLを取得（デプロイ環境とローカル環境で異なる）
    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const response = await fetch(`${API_BASE_URL}/api/ranking?limit=5`, {
      cache: "no-store", // リアルタイムなランキング情報を取得
    });

    if (!response.ok) {
      console.error("Failed to fetch ranking data:", response.status);
      return null;
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching ranking data:", error);
    return null;
  }
}
