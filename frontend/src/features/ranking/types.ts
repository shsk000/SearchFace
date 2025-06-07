// ランキング項目の型定義
export interface RankingItem {
  rank: number;
  person_id: number;
  name: string;
  win_count: number;
  last_win_date: string | null;
  image_path: string | null;
}

// ランキングレスポンスの型定義
export interface RankingResponse {
  ranking: RankingItem[];
  total_count: number;
}

// RankingItemCardコンポーネントのProps型
export interface RankingItemCardProps {
  item: RankingItem;
}
