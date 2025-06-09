import { createLogger } from "@/lib/logger";
import type { RankingResponse } from "./types";

const logger = createLogger("Ranking");

// ランキングデータを取得する関数
export async function getRankingData(): Promise<RankingResponse | null> {
  try {
    logger.info("ランキングデータの取得を開始");

    // 環境変数からAPI URLを取得（デプロイ環境とローカル環境で異なる）
    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const response = await fetch(`${API_BASE_URL}/api/ranking?limit=5`, {
      next: { revalidate: 3600 }, // 1時間キャッシュ
    });

    if (!response.ok) {
      logger.error("ランキングデータの取得に失敗", {
        status: response.status,
        statusText: response.statusText,
      });
      return null;
    }

    const data = await response.json();
    logger.info("ランキングデータの取得に成功", {
      rankingCount: data.ranking?.length || 0,
    });

    return data;
  } catch (error) {
    logger.error("ランキングデータ取得中にエラー", { error });
    return null;
  }
}
